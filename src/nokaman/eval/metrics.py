from __future__ import annotations

import json
from pathlib import Path

from nokaman.config import PLACEMENT_DIR
from nokaman.data.loader import list_sample_files, load_sample
from nokaman.eval.pipeline import evaluate_sample_file
from nokaman.models.cefr import cefr_rank


def batch_evaluate(sample_dir: Path | None = None) -> dict:
    files = list_sample_files(sample_dir) if sample_dir else list_sample_files()
    rows = []
    exact = 0
    adjacent = 0
    labeled = 0
    for path in files:
        sample = load_sample(path)
        result = evaluate_sample_file(path)
        row = {
            "file": path.name,
            "language": result.get("language"),
            "skill": result.get("skill"),
            "score": result.get("score"),
            "cefr": result.get("cefr"),
            "expected_cefr": sample.get("expected_cefr"),
        }
        if sample.get("expected_cefr"):
            labeled += 1
            pred = str(result.get("cefr") or "").upper()
            exp = str(sample["expected_cefr"]).upper()
            dist = abs(cefr_rank(pred) - cefr_rank(exp))
            row["distance"] = dist
            if dist == 0:
                exact += 1
                adjacent += 1
            elif dist == 1:
                adjacent += 1
        rows.append(row)
    by_language: dict[str, dict] = {}
    for row in rows:
        lang = str(row.get("language") or "?")
        bucket = by_language.setdefault(lang, {"n": 0, "labeled": 0, "exact": 0, "adjacent": 0})
        bucket["n"] += 1
        if row.get("expected_cefr"):
            bucket["labeled"] += 1
            dist = row.get("distance")
            if dist == 0:
                bucket["exact"] += 1
                bucket["adjacent"] += 1
            elif dist == 1:
                bucket["adjacent"] += 1
    for lang, bucket in by_language.items():
        lab = bucket["labeled"] or 0
        bucket["exact_cefr_hit_rate"] = round(bucket["exact"] / lab, 4) if lab else None
        bucket["adjacent_cefr_hit_rate"] = round(bucket["adjacent"] / lab, 4) if lab else None
    return {
        "n_samples": len(files),
        "n_labeled": labeled,
        "exact_cefr_hit_rate": round(exact / labeled, 4) if labeled else None,
        "adjacent_cefr_hit_rate": round(adjacent / labeled, 4) if labeled else None,
        "by_language": by_language,
        "rows": rows,
    }


def load_placement_pack(language: str, directory: Path | None = None) -> dict:
    """Load a license-safe placement pack JSON for a language (en/ko/ja minimum)."""
    code = language.strip().lower()
    root = directory or PLACEMENT_DIR
    path = root / f"{code}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"No placement pack for language '{code}'. Expected file: {path}"
        )
    pack = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(pack, dict):
        raise ValueError(f"Placement pack must be a JSON object: {path}")
    prompts = pack.get("prompts") or []
    if not isinstance(prompts, list) or len(prompts) < 3:
        raise ValueError(f"Placement pack needs at least 3 prompts: {path}")
    pack["language"] = str(pack.get("language") or code).strip().lower()
    pack["source"] = str(path)
    return pack


def list_placement_packs(directory: Path | None = None) -> list[str]:
    root = directory or PLACEMENT_DIR
    if not root.exists():
        return []
    return sorted(p.stem for p in root.glob("*.json"))


def placement_test(language: str, answers: list[str]) -> dict:
    """
    Simple placement: score each short answer text, average overall CEFR.
    answers: list of learner free-text responses.
    """
    from nokaman.models.toy import ToyAbilityModel

    model = ToyAbilityModel(language=language)
    skill_scores = []
    details = []
    for i, text in enumerate(answers):
        multi = model.score_multi_skill(text)
        skill_scores.append(multi["overall"])
        details.append({"item": i + 1, "text": text[:120], **multi})
    overall = sum(skill_scores) / len(skill_scores) if skill_scores else 0.0
    from nokaman.models.cefr import score_to_cefr

    return {
        "language": language,
        "n_items": len(answers),
        "overall": round(overall, 2),
        "cefr": score_to_cefr(overall),
        "items": details,
        "ready_for_ui": True,
    }


def run_placement_pack(
    language: str,
    answers: list[str] | None = None,
    *,
    use_demo_answers: bool = False,
    directory: Path | None = None,
) -> dict:
    """
    Single product path: load prompts for a language, score answers, return app-ready report.

    If answers is None and use_demo_answers is True, score bundled demo answers
    (sample evidence reports for EN/KO/JA).
    """
    pack = load_placement_pack(language, directory=directory)
    prompts = pack["prompts"]
    if answers is None:
        if not use_demo_answers:
            raise ValueError("Provide answers or set use_demo_answers=True for sample reports")
        answers = [str(p.get("demo_answer") or "") for p in prompts]
    if len(answers) != len(prompts):
        raise ValueError(
            f"Expected {len(prompts)} answers for pack {pack.get('id')}, got {len(answers)}"
        )
    if any(not str(a).strip() for a in answers):
        raise ValueError("All placement answers must be non-empty")

    scored = placement_test(pack["language"], answers)
    items = []
    for prompt, detail, answer in zip(prompts, scored["items"], answers, strict=True):
        items.append(
            {
                "prompt_id": prompt.get("id"),
                "skill": prompt.get("skill"),
                "prompt": prompt.get("prompt"),
                "answer": answer,
                "score": detail.get("overall"),
                "cefr": detail.get("cefr"),
                "skills": detail.get("skills"),
            }
        )
    return {
        "pack_id": pack.get("id"),
        "title": pack.get("title"),
        "license": pack.get("license"),
        "language": pack["language"],
        "n_items": len(items),
        "overall": scored["overall"],
        "cefr": scored["cefr"],
        "items": items,
        "ready_for_ui": True,
        "sample_report": bool(use_demo_answers),
        "source": pack.get("source"),
    }
