from __future__ import annotations

import json
from pathlib import Path

import pytest

from nokaman.rubrics.writing_cohesion import (
    score_writing_cohesion,
    score_writing_sample,
)


def test_writing_cohesion_reports_offline_dimensions() -> None:
    result = score_writing_cohesion(
        "First I outlined the topic. Then I added examples. However, one claim was weak, "
        "so I revised it. Therefore the paragraph is clearer.",
        paragraph_count=1,
        connector_count=4,
    )

    assert 0 <= result["score"] <= 100
    assert set(result["dimensions"]) == {"cohesion", "coherence"}
    assert result["observations"]["connector_count"] == 4
    assert result["observations"]["paragraph_count"] == 1
    assert result["observations"]["sentence_count"] >= 3
    assert any("not a certified CEFR" in item for item in result["limitations"])


def test_writing_sample_fixture_is_supported() -> None:
    path = Path("data/samples/en_writing_b1_cohesion.json")
    sample = json.loads(path.read_text(encoding="utf-8"))

    result = score_writing_sample(sample)

    assert result["observations"]["paragraph_count"] == 1
    assert result["observations"]["connector_count"] == 5
    assert result["dimensions"]["cohesion"] > 0
    assert result["dimensions"]["coherence"] > 0


def test_writing_cohesion_marks_estimated_observations() -> None:
    result = score_writing_cohesion(
        "I like parks.\n\nParks help me relax after work because they are quiet."
    )

    assert any("Connector count was estimated" in item for item in result["limitations"])
    assert any("Paragraph count was estimated" in item for item in result["limitations"])
    assert result["observations"]["paragraph_count"] == 2


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"paragraph_count": 0}, "paragraph_count"),
        ({"connector_count": -1}, "connector_count"),
    ],
)
def test_writing_cohesion_rejects_invalid_observations(kwargs: dict, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        score_writing_cohesion("A valid writing sample.", **kwargs)


def test_writing_sample_requires_writing_skill() -> None:
    with pytest.raises(ValueError, match="writing"):
        score_writing_sample({"skill": "speaking", "text": "Hello there."})
