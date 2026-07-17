from __future__ import annotations

import json
from pathlib import Path

import pytest

from nokaman.rubrics.speaking_fluency import (
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


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"duration_seconds": 0}, "duration_seconds"),
        ({"pause_count": -1}, "pause_count"),
        ({"filler_count": -1}, "filler_count"),
    ],
)
def test_speaking_fluency_rejects_invalid_observations(kwargs: dict, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        score_speaking_fluency("A valid transcript.", **kwargs)
