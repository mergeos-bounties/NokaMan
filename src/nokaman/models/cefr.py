from __future__ import annotations

from nokaman.rubrics.registry import CEFR_BANDS


def score_to_cefr(score_0_100: float) -> str:
    """Map overall ability score [0, 100] to a CEFR-style band."""
    s = max(0.0, min(100.0, float(score_0_100)))
    thresholds = [
        (90, "C2"),
        (80, "C1"),
        (65, "B2"),
        (50, "B1"),
        (35, "A2"),
        (0, "A1"),
    ]
    for min_score, band in thresholds:
        if s >= min_score:
            return band
    return "A1"


def cefr_rank(band: str) -> int:
    try:
        return CEFR_BANDS.index(band.upper())
    except ValueError:
        return 0


def compare_bands(predicted: str, expected: str) -> dict:
    p, e = predicted.upper(), expected.upper()
    return {
        "predicted": p,
        "expected": e,
        "exact_match": p == e,
        "distance": abs(cefr_rank(p) - cefr_rank(e)),
    }
