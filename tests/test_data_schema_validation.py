from __future__ import annotations

import json

import pytest

from nokaman.data.loader import list_rubric_files, list_sample_files, load_rubric, load_sample
from nokaman.data.schemas import validate_rubric_payload, validate_sample_payload


def test_existing_sample_fixtures_validate() -> None:
    files = list_sample_files()

    assert files
    for path in files:
        sample = load_sample(path)
        assert sample["id"]
        assert sample["language"]
        assert sample["skill"]
        assert isinstance(sample["text"], str)


def test_existing_rubric_fixtures_validate() -> None:
    files = list_rubric_files()

    assert files
    for path in files:
        rubric = load_rubric(path)
        assert rubric["language"]
        assert isinstance(rubric["skills"], dict)


def test_invalid_sample_payload_has_helpful_error() -> None:
    with pytest.raises(ValueError) as excinfo:
        validate_sample_payload(
            {"id": "bad-sample", "language": "en", "skill": "writing", "text": ["not", "text"]},
            "bad_sample.json",
        )

    message = str(excinfo.value)
    assert "bad_sample.json" in message
    assert "text" in message


def test_invalid_rubric_payload_has_helpful_error() -> None:
    with pytest.raises(ValueError) as excinfo:
        validate_rubric_payload(
            {"language": "en", "skills": {"writing": {"weight": "heavy"}}},
            "bad_rubric.json",
        )

    message = str(excinfo.value)
    assert "bad_rubric.json" in message
    assert "skills.writing.weight" in message


def test_loader_reports_source_path_for_invalid_json(tmp_path) -> None:
    path = tmp_path / "invalid_sample.json"
    path.write_text(
        json.dumps({"id": "invalid", "language": "en", "skill": "writing", "text": ["bad"]}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError) as excinfo:
        load_sample(path)

    assert str(path) in str(excinfo.value)
