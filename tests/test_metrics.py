from __future__ import annotations

import pytest

from nokaman.eval.metrics import _compute_band_accuracy_metrics, batch_evaluate, placement_test


def test_batch_evaluate() -> None:
    report = batch_evaluate()
    assert report["n_samples"] >= 1
    assert "rows" in report


def test_compute_band_accuracy_all_exact() -> None:
    rows = [
        {"expected_cefr": "B2", "distance": 0},
        {"expected_cefr": "B1", "distance": 0},
        {"expected_cefr": "A2", "distance": 0},
    ]
    m = _compute_band_accuracy_metrics(rows)
    assert m["n_labeled"] == 3
    assert m["exact_cefr_hit_rate"] == 1.0
    assert m["adjacent_cefr_hit_rate"] == 1.0
    assert m["mae_on_score"] == 0.0


def test_compute_band_accuracy_all_adjacent() -> None:
    rows = [
        {"expected_cefr": "B2", "distance": 1},
        {"expected_cefr": "B1", "distance": 1},
    ]
    m = _compute_band_accuracy_metrics(rows)
    assert m["n_labeled"] == 2
    assert m["exact_cefr_hit_rate"] == 0.0
    assert m["adjacent_cefr_hit_rate"] == 1.0
    assert m["mae_on_score"] == 1.0


def test_compute_band_accuracy_mixed() -> None:
    rows = [
        {"expected_cefr": "B2", "distance": 0},
        {"expected_cefr": "B1", "distance": 1},
        {"expected_cefr": "A2", "distance": 2},
    ]
    m = _compute_band_accuracy_metrics(rows)
    assert m["n_labeled"] == 3
    assert m["exact_cefr_hit_rate"] == pytest.approx(1 / 3, abs=1e-3)
    assert m["adjacent_cefr_hit_rate"] == pytest.approx(2 / 3, abs=1e-3)
    assert m["mae_on_score"] == pytest.approx(1.0)


def test_compute_band_accuracy_no_labeled() -> None:
    rows = [{"expected_cefr": None}, {"expected_cefr": ""}]
    m = _compute_band_accuracy_metrics(rows)
    assert m["n_labeled"] == 0
    assert m["exact_cefr_hit_rate"] is None
    assert m["adjacent_cefr_hit_rate"] is None
    assert m["mae_on_score"] is None


def test_compute_band_accuracy_mae() -> None:
    rows = [
        {"expected_cefr": "B2", "distance": 0},
        {"expected_cefr": "B1", "distance": 2},
        {"expected_cefr": "A2", "distance": 0},
        {"expected_cefr": "C1", "distance": 1},
    ]
    m = _compute_band_accuracy_metrics(rows)
    # (0+2+0+1)/4 = 0.75
    assert m["mae_on_score"] == pytest.approx(0.75)


def test_placement_test() -> None:
    result = placement_test(
        "en",
        [
            "I study English every day and write short notes.",
            "Hello my name is Sam.",
        ],
    )
    assert result["cefr"]
    assert result["n_items"] == 2
