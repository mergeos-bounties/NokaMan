"""Tests for rubric and sample validation."""

import json
from pathlib import Path

import pytest

from nokaman.validation import (
    validate_rubric,
    validate_sample,
    validate_rubric_file,
    validate_sample_file,
)


class TestValidateRubric:
    def test_valid_rubric(self):
        data = {
            "language": "en",
            "name": "English",
            "skills": {
                "writing": {
                    "description": "Writing skill",
                    "dimensions": [
                        {"name": "grammar", "weight": 0.5, "description": "Grammar accuracy"},
                        {"name": "vocabulary", "weight": 0.5, "description": "Vocabulary range"},
                    ],
                }
            },
        }
        errors = validate_rubric(data)
        assert errors == []

    def test_missing_language(self):
        data = {"name": "Test", "skills": {}}
        errors = validate_rubric(data)
        assert any("language" in e for e in errors)

    def test_invalid_weight(self):
        data = {
            "language": "en",
            "name": "English",
            "skills": {
                "writing": {
                    "dimensions": [{"name": "grammar", "weight": 1.5}],
                }
            },
        }
        errors = validate_rubric(data)
        assert any("weight" in e for e in errors)


class TestValidateSample:
    def test_valid_sample(self):
        errors = validate_sample({"text": "Hello", "skill": "writing", "language": "en"})
        assert errors == []

    def test_missing_text(self):
        errors = validate_sample({"skill": "writing", "language": "en"})
        assert any("text" in e for e in errors)

    def test_empty_text(self):
        errors = validate_sample({"text": "", "skill": "writing", "language": "en"})
        assert any("text" in e for e in errors)

    def test_missing_skill(self):
        errors = validate_sample({"text": "Hello", "language": "en"})
        assert any("skill" in e for e in errors)


class TestValidateFiles:
    def test_rubric_file_not_found(self, tmp_path):
        errors = validate_rubric_file(tmp_path / "nonexistent.json")
        assert len(errors) > 0

    def test_sample_file_invalid_json(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("not json", encoding="utf-8")
        errors = validate_sample_file(p)
        assert len(errors) > 0

    def test_existing_fixtures_valid(self):
        from nokaman.config import RUBRICS_DIR, SAMPLES_DIR
        rubric_files = list(RUBRICS_DIR.glob("*.json"))
        for f in rubric_files:
            errors = validate_rubric_file(f)
            assert errors == [], f"{f.name}: {errors}"
