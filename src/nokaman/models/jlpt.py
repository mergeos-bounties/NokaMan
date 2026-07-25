from __future__ import annotations

#: JLPT N-levels from easiest (N5) to hardest (N1).
JLPT_BANDS = ("N5", "N4", "N3", "N2", "N1")


#: Mapping from a NokaMan ability score in [0, 100] to a JLPT N-level.
#: Thresholds align with CEFR→N5..N1 ladders widely used in Japanese
#: assessment tooling: N5≈A1, N4≈A2, N3≈B1, N2≈B2, N1≈C1/C2.
JLPT_THRESHOLDS = [
    (80, "N1"),
    (60, "N2"),
    (45, "N3"),
    (30, "N4"),
    (0, "N5"),
]


def score_to_jlpt(score_0_100: float) -> str:
    """Map a NokaMan ability score [0, 100] to a JLPT N-level band.

    This is the canonical adapter for JLPT-style scoring.  It is intended
    to sit alongside :func:`nokaman.models.cefr.score_to_cefr` so that
    Japanese assessments expose both CEFR and JLPT views from the same
    underlying ability score.

    Args:
        score_0_100: Overall ability score in the [0, 100] range.

    Returns:
        A JLPT N-level string (``N5``..``N1``).  The level ``N1`` is the
        highest band; ``N5`` is the baseline for any score above 0.
    """
    s = max(0.0, min(100.0, float(score_0_100)))
    for min_score, band in JLPT_THRESHOLDS:
        if s >= min_score:
            return band
    return "N5"


def jlpt_rank(band: str) -> int:
    """Return the ordinal rank of a JLPT N-level (higher is more advanced).

    ``N5`` → 0, ``N1`` → 4.  Unknown bands fall back to 0 (``N5``).
    """
    try:
        return JLPT_BANDS.index(band.upper())
    except ValueError:
        return 0


def jlpt_descriptions() -> dict[str, str]:
    """Short human-readable descriptions of each JLPT band."""
    return {
        "N5": "Basic Japanese — familiar phrases and short sentences.",
        "N4": "Elementary — everyday expressions and simple written text.",
        "N3": "Intermediate — main points of clear standard language.",
        "N2": "Upper intermediate — detailed Japanese on a wide range of topics.",
        "N1": "Advanced — fluent Japanese with complex reading and reasoning.",
    }
