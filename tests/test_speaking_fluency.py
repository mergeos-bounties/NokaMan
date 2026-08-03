from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from nokaman.cli import app
from nokaman.rubrics.speaking_fluency import (
    score_asr_transcript,
    score_speaking_fluency,
    score_speaking_sample,
)


def test_speaking_fluency_reports_offline_dimensions() -> None:
    result = score_speaking_fluency(
        "I planned the project, um, explained the risks, and answered the questions.",
        duration_seconds=9,
        pause_count=2,
    )

    assert 0 <= result["score"] <= 100
    assert set(result["dimensions"]) == {
        "pace",
        "continuity",
        "filler_control",
        "phrase_length",
    }
    assert result["observations"]["word_count"] == 12
    assert result["observations"]["filler_count"] == 1
    assert result["observations"]["words_per_minute"] == 80.0
    assert isinstance(result["feedback"], list) and len(result["feedback"]) >= 3
    assert any("not a certified CEFR" in item for item in result["limitations"])


def test_speaking_sample_fixture_is_supported() -> None:
    path = Path("data/samples/en_speaking_b1_fluency.json")
    sample = json.loads(path.read_text(encoding="utf-8"))

    result = score_speaking_sample(sample)

    assert result["observations"]["duration_seconds"] == 22.0
    assert result["observations"]["pause_count"] == 2
    assert result["observations"]["filler_count"] == 0


def test_speaking_fluency_marks_estimated_observations() -> None:
    result = score_speaking_fluency("First I prepared. Then I presented the result.")

    assert result["dimensions"]["pace"] == 50.0
    assert any("neutral score" in item for item in result["limitations"])
    assert any("estimated" in item for item in result["limitations"])


def test_asr_transcript_accepts_confidence_and_feedback() -> None:
    path = Path("data/fixtures/asr_transcript_en_b1.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    result = score_asr_transcript(payload)

    assert result["skill"] == "speaking"
    assert result["observations"]["confidence"] == 0.91
    assert any("confidence" in bullet.lower() for bullet in result["feedback"])


def test_asr_confidence_percent_scale() -> None:
    result = score_asr_transcript(
        {
            "skill": "speaking",
            "transcript": "I practiced speaking for five minutes today.",
            "confidence": 88,
        }
    )
    assert result["observations"]["confidence"] == 0.88


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"duration_seconds": 0}, "duration_seconds"),
        ({"pause_count": -1}, "pause_count"),
        ({"filler_count": -1}, "filler_count"),
        ({"confidence": -0.1}, "confidence"),
    ],
)
def test_speaking_fluency_rejects_invalid_observations(kwargs: dict, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        score_speaking_fluency("A valid transcript.", **kwargs)


def test_cli_eval_speaking_fixture() -> None:
    result = CliRunner().invoke(
        app,
        ["eval", "speaking", "--file", "data/fixtures/asr_transcript_en_b1.json"],
    )
    assert result.exit_code == 0, result.output
    assert "feedback" in result.output
    assert "speaking" in result.output
