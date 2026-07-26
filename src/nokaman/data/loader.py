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
    """Return a list of sample records parsed from every JSON file in the samples dir."""
    records: list[dict] = []
    for path in list_sample_files(directory):
        payload = load_sample(path)
        records.append(
            {
                "id": payload.get("id"),
                "language": payload.get("language"),
                "skill": payload.get("skill"),
                "expected_cefr": payload.get("expected_cefr"),
                "file": path.name,
            }
        )
    return records


def filter_catalog(
    records: list[dict] | None = None,
    *,
    language: str | None = None,
    skill: str | None = None,
) -> list[dict]:
    """Return samples narrowed by optional language / skill filters."""
    if records is None:
        records = catalog_samples()
    if language:
        lang = language.strip().lower()
        records = [r for r in records if str(r.get("language") or "").strip().lower() == lang]
    if skill:
        sk = skill.strip().lower()
        records = [r for r in records if str(r.get("skill") or "").strip().lower() == sk]
    return records
