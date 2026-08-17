from __future__ import annotations

import json
from pathlib import Path

import pytest

from nokaman.rubrics.writing_cohesion import (
    score_writing_cohesion,
    score_writing_sample,
)


def test_writing_cohesion_reports_offline_dimensions() -> None:
    text = "The weather was beautiful today. Therefore, we decided to go to the park. We walked around the lake for a while. However, it started raining unexpectedly. Because of the rain, we had to run back home. Nonetheless, we had a good time."
    result = score_writing_cohesion(text)

    assert 0 <= result["score"] <= 100
    assert set(result["dimensions"]) == {
        "cohesion",
        "coherence",
    }
    assert result["observations"]["word_count"] > 10
    assert result["observations"]["sentence_count"] == 6
    assert result["observations"]["connector_count"] >= 3
    assert any("not a certified CEFR" in item for item in result["limitations"])


def test_writing_sample_fixture_is_supported() -> None:
    path = Path("data/samples/en_writing_b1_cohesion.json")
    sample = json.loads(path.read_text(encoding="utf-8"))

    result = score_writing_sample(sample)

    assert result["observations"]["sentence_count"] == 6
    assert result["observations"]["paragraph_count"] == 1
    assert result["observations"]["connector_count"] > 0


def test_writing_cohesion_marks_estimated_observations() -> None:
    result = score_writing_cohesion("This is a single sentence without connectors.")

    assert result["dimensions"]["cohesion"] == 0.0
    assert result["dimensions"]["coherence"] == 30.0


@pytest.mark.parametrize(
    "text",
    [
        (""),
        ("   "),
    ],
)
def test_writing_cohesion_rejects_empty(text: str) -> None:
    with pytest.raises(ValueError, match="empty|words"):
        score_writing_cohesion(text)
