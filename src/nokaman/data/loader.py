from __future__ import annotations

import json
from pathlib import Path

from nokaman.config import LISTENING_DIR, RUBRICS_DIR, SAMPLES_DIR


def list_sample_files(directory: Path | None = None) -> list[Path]:
    root = directory or SAMPLES_DIR
    if not root.exists():
        return []
    return sorted(root.glob("*.json"))


def list_rubric_files(directory: Path | None = None) -> list[Path]:
    root = directory or RUBRICS_DIR
    if not root.exists():
        return []
    return sorted(root.glob("*.json"))


def list_listening_pack_files(directory: Path | None = None) -> list[Path]:
    root = directory or LISTENING_DIR
    if not root.exists():
        return []
    return sorted(root.glob("*.json"))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_sample(path: Path) -> dict:
    payload = load_json(path)
    payload.setdefault("id", path.stem)
    payload.setdefault("language", "en")
    payload.setdefault("skill", "writing")
    payload.setdefault("text", "")
    return payload


def load_listening_pack(path: Path) -> dict:
    payload = load_json(path)
    payload.setdefault("id", path.stem)
    payload.setdefault("language", "en")
    payload.setdefault("skill", "listening")
    payload.setdefault("questions", payload.get("items") or [])
    payload["items"] = list(payload.get("items") or payload.get("questions") or [])
    return payload


def load_rubric(path: Path) -> dict:
    payload = load_json(path)
    payload.setdefault("language", path.stem)
    payload.setdefault("skills", {})
    return payload


def catalog_samples(directory: Path | None = None) -> list[dict]:
    """Return catalogued sample metadata for CLI listing and filters."""
    records: list[dict] = []
    for path in list_sample_files(directory):
        payload = load_sample(path)
        text = str(payload.get("text") or "")
        records.append(
            {
                "id": str(payload.get("id") or path.stem),
                "file": path.name,
                "language": str(payload.get("language") or "en").strip().lower(),
                "skill": str(payload.get("skill") or "writing").strip().lower(),
                "expected_cefr": str(payload.get("expected_cefr") or "").strip().upper(),
                "text_length": len(text),
            }
        )
    return records


def filter_sample_catalog(
    records: list[dict] | None = None,
    *,
    language: str | None = None,
    skill: str | None = None,
    directory: Path | None = None,
) -> list[dict]:
    """Filter catalogued samples by language and/or skill (case-insensitive)."""
    items = catalog_samples(directory) if records is None else list(records)
    lang = language.strip().lower() if language else ""
    skill_key = skill.strip().lower() if skill else ""
    if lang:
        items = [row for row in items if row.get("language") == lang]
    if skill_key:
        items = [row for row in items if row.get("skill") == skill_key]
    return items
