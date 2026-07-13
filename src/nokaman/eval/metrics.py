from __future__ import annotations

from pathlib import Path

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
        bucket = by_language.setdefault(
            lang, {"n": 0, "labeled": 0, "exact": 0, "adjacent": 0}
        )
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
        bucket["exact_cefr_hit_rate"] = (
            round(bucket["exact"] / lab, 4) if lab else None
        )
        bucket["adjacent_cefr_hit_rate"] = (
            round(bucket["adjacent"] / lab, 4) if lab else None
        )
    return {
        "n_samples": len(files),
        "n_labeled": labeled,
        "exact_cefr_hit_rate": round(exact / labeled, 4) if labeled else None,
        "adjacent_cefr_hit_rate": round(adjacent / labeled, 4) if labeled else None,
        "by_language": by_language,
        "rows": rows,
    }


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
