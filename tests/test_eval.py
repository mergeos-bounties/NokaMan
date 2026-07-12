from __future__ import annotations

from nokaman.data.loader import list_sample_files
from nokaman.eval.pipeline import evaluate_demo, evaluate_sample_file, evaluate_text
from nokaman.models.cefr import score_to_cefr
from nokaman.rubrics.registry import SUPPORTED_LANGUAGES


def test_score_to_cefr_bands() -> None:
    assert score_to_cefr(10) == "A1"
    assert score_to_cefr(55) == "B1"
    assert score_to_cefr(95) == "C2"


def test_evaluate_text_en() -> None:
    result = evaluate_text(
        "en",
        "I practice English every morning by reading news and writing short notes.",
        skill="writing",
    )
    assert result["language"] == "en"
    assert 0 <= result["score"] <= 100
    assert result["cefr"] in {"A1", "A2", "B1", "B2", "C1", "C2"}


def test_evaluate_samples() -> None:
    files = list_sample_files()
    assert len(files) >= 6
    for path in files:
        result = evaluate_sample_file(path)
        assert "score" in result
        assert result["language"] in SUPPORTED_LANGUAGES


def test_demo_multi_skill() -> None:
    result = evaluate_demo("ko")
    assert result["language"] == "ko"
    assert "skills" in result
    assert "overall" in result
