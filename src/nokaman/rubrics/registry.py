from __future__ import annotations

from pathlib import Path

from nokaman.config import RUBRICS_DIR
from nokaman.data.loader import list_rubric_files, load_rubric

# Built-in language metadata (ISO-ish codes used by CLI)
SUPPORTED_LANGUAGES: dict[str, dict] = {
    "en": {"name": "English", "frameworks": ["CEFR", "TOEIC", "IELTS"]},
    "ko": {"name": "Korean", "frameworks": ["CEFR", "TOPIK"]},
    "ja": {"name": "Japanese", "frameworks": ["CEFR", "JLPT"]},
    "vi": {"name": "Vietnamese", "frameworks": ["CEFR"]},
    "zh": {"name": "Chinese (Mandarin)", "frameworks": ["CEFR", "HSK"]},
    "es": {"name": "Spanish", "frameworks": ["CEFR", "DELE"]},
    "fr": {"name": "French", "frameworks": ["CEFR", "DELF"]},
    "de": {"name": "German", "frameworks": ["CEFR", "Goethe"]},
}

SKILLS = ("vocabulary", "grammar", "reading", "writing", "listening", "speaking")

CEFR_BANDS = ("A1", "A2", "B1", "B2", "C1", "C2")


def get_language_meta(code: str) -> dict:
    key = code.strip().lower()
    if key not in SUPPORTED_LANGUAGES:
        raise KeyError(f"unsupported language {code!r}; known={sorted(SUPPORTED_LANGUAGES)}")
    return {"code": key, **SUPPORTED_LANGUAGES[key]}


def load_language_rubric(code: str) -> dict:
    key = code.strip().lower()
    path = RUBRICS_DIR / f"{key}.json"
    if path.exists():
        return load_rubric(path)
    # Fallback minimal rubric
    return {
        "language": key,
        "skills": {skill: {"weight": 1.0, "notes": f"Default {skill} rubric"} for skill in SKILLS},
        "bands": list(CEFR_BANDS),
    }


def list_available_rubrics() -> list[dict]:
    items = []
    for path in list_rubric_files():
        items.append(load_rubric(path))
    return items
