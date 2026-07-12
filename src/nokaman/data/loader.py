from __future__ import annotations

import json
from pathlib import Path

from nokaman.config import RUBRICS_DIR, SAMPLES_DIR


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


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_sample(path: Path) -> dict:
    payload = load_json(path)
    payload.setdefault("id", path.stem)
    payload.setdefault("language", "en")
    payload.setdefault("skill", "writing")
    payload.setdefault("text", "")
    return payload


def load_rubric(path: Path) -> dict:
    payload = load_json(path)
    payload.setdefault("language", path.stem)
    payload.setdefault("skills", {})
    return payload
