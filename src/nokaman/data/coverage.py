from __future__ import annotations

from pathlib import Path

from nokaman.config import RUBRICS_DIR
from nokaman.data.loader import list_sample_files, load_sample
from nokaman.rubrics.registry import SKILLS, SUPPORTED_LANGUAGES


def language_skill_coverage(sample_dir: Path | None = None) -> dict:
    counts: dict[str, dict[str, int]] = {
        code: {skill: 0 for skill in SKILLS} for code in sorted(SUPPORTED_LANGUAGES)
    }
    for path in list_sample_files(sample_dir):
        sample = load_sample(path)
        language = str(sample.get("language") or "").strip().lower()
        skill = str(sample.get("skill") or "").strip().lower()
        if language not in counts:
            counts[language] = {item: 0 for item in SKILLS}
        if skill not in counts[language]:
            counts[language][skill] = 0
        counts[language][skill] += 1

    rows = []
    for code in sorted(counts):
        meta = SUPPORTED_LANGUAGES.get(code, {"name": code, "frameworks": []})
        skill_counts = {skill: counts[code].get(skill, 0) for skill in SKILLS}
        total = sum(skill_counts.values())
        rows.append(
            {
                "code": code,
                "name": meta.get("name", code),
                "frameworks": list(meta.get("frameworks") or []),
                "has_rubric": (RUBRICS_DIR / f"{code}.json").exists(),
                "total": total,
                "skills": skill_counts,
            }
        )
    return {"skills": list(SKILLS), "languages": rows}
