from __future__ import annotations

import re
from collections.abc import Mapping

FILLER_WORDS = frozenset({"ah", "erm", "hmm", "uh", "um"})
DIMENSION_WEIGHTS = {
    "pace": 0.30,
    "continuity": 0.30,
    "filler_control": 0.20,
    "phrase_length": 0.20,
}
BASE_LIMITATIONS = (
    "Transcript heuristics do not measure pronunciation, intonation, or audio quality.",
    "Token and filler detection is language-dependent and is least reliable for text without spaces.",
    "The result is an offline product signal, not a certified CEFR speaking assessment.",
)


def _words(text: str) -> list[str]:
    return re.findall(r"[^\W\d_]+(?:['-][^\W\d_]+)*", text.lower(), flags=re.UNICODE)


def _clamp(value: float) -> float:
    return round(max(0.0, min(100.0, value)), 2)


def _pace_score(words_per_minute: float | None) -> float:
    if words_per_minute is None:
        return 50.0
    if words_per_minute < 90:
        return _clamp(100 - (90 - words_per_minute) * 1.25)
    if words_per_minute <= 170:
        return 100.0
    return _clamp(100 - (words_per_minute - 170) * 0.8)


def score_speaking_fluency(
    transcript: str,
    *,
    duration_seconds: float | None = None,
    pause_count: int | None = None,
    filler_count: int | None = None,
) -> dict:
    """Score transcript-level fluency signals with deterministic offline heuristics."""
    text = transcript.strip()
    if not text:
        raise ValueError("transcript must not be empty")
    if duration_seconds is not None and duration_seconds <= 0:
        raise ValueError("duration_seconds must be greater than zero")
    if pause_count is not None and pause_count < 0:
        raise ValueError("pause_count must not be negative")
    if filler_count is not None and filler_count < 0:
        raise ValueError("filler_count must not be negative")

    words = _words(text)
    if not words:
        raise ValueError("transcript must contain words")

    observed_pauses = (
        pause_count if pause_count is not None else len(re.findall(r"[,;:.!?]+", text))
    )
    observed_fillers = (
        filler_count if filler_count is not None else sum(word in FILLER_WORDS for word in words)
    )
    words_per_minute = (
        len(words) / (duration_seconds / 60) if duration_seconds is not None else None
    )

    clauses = [part for part in re.split(r"[,;:.!?]+", text) if _words(part)]
    average_phrase_words = len(words) / max(1, len(clauses))
    pause_rate = observed_pauses / len(words) * 100
    filler_rate = observed_fillers / len(words) * 100

    dimensions = {
        "pace": _pace_score(words_per_minute),
        "continuity": _clamp(100 - pause_rate * 5),
        "filler_control": _clamp(100 - filler_rate * 4),
        "phrase_length": _clamp(average_phrase_words / 12 * 100),
    }
    overall = _clamp(sum(dimensions[name] * weight for name, weight in DIMENSION_WEIGHTS.items()))

    limitations = list(BASE_LIMITATIONS)
    if duration_seconds is None:
        limitations.append("Pace uses a neutral score because duration_seconds was not provided.")
    if pause_count is None:
        limitations.append("Pause count was estimated from transcript punctuation.")

    return {
        "score": overall,
        "dimensions": dimensions,
        "observations": {
            "word_count": len(words),
            "duration_seconds": duration_seconds,
            "words_per_minute": round(words_per_minute, 2)
            if words_per_minute is not None
            else None,
            "pause_count": observed_pauses,
            "filler_count": observed_fillers,
            "average_phrase_words": round(average_phrase_words, 2),
        },
        "limitations": limitations,
    }


def score_speaking_sample(sample: Mapping[str, object]) -> dict:
    """Score a speaking sample containing optional fluency observations."""
    if str(sample.get("skill") or "").strip().lower() != "speaking":
        raise ValueError("sample skill must be speaking")
    observations = sample.get("fluency_observations") or {}
    if not isinstance(observations, Mapping):
        raise ValueError("fluency_observations must be an object")
    return score_speaking_fluency(
        str(sample.get("text") or ""),
        duration_seconds=_optional_float(observations.get("duration_seconds")),
        pause_count=_optional_int(observations.get("pause_count")),
        filler_count=_optional_int(observations.get("filler_count")),
    )


def _optional_float(value: object) -> float | None:
    return None if value is None else float(value)


def _optional_int(value: object) -> int | None:
    return None if value is None else int(value)
