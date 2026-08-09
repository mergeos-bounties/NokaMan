
"""Speaking fluency rubric: offline heuristic scorer.

Scores a speaking sample on four dimensions that can be measured
without a live ASR service:

- pace            (words per minute vs. target range)
- continuity      (ratio of speech to total time)
- filler_control  (filler-word rate)
- phrase_length   (mean words between pauses)

All scores are 0-100.  The composite ``score`` is the unweighted mean.

Limitations are always reported so callers can surface them to users.
"""
from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------------------
# Filler words (English-centric; extend as needed)
# ---------------------------------------------------------------------------
_FILLERS = re.compile(
    r"\b(um|uh|er|ah|like|you\s+know|i\s+mean|basically|literally|right)\b",
    re.IGNORECASE,
)

# Target speaking pace for conversational English (words per minute)
_TARGET_WPM_LOW = 100
_TARGET_WPM_HIGH = 160

_NEUTRAL_PACE = 50.0  # score assigned when duration is unknown


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def score_speaking_fluency(
    transcript: str,
    *,
    duration_seconds: float | None = None,
    pause_count: int | None = None,
    filler_count: int | None = None,
) -> dict[str, Any]:
    """Score a speaking transcript on fluency dimensions.

    Parameters
    ----------
    transcript:
        Plain-text transcript of the learner's speech.
    duration_seconds:
        Total recording length in seconds.  Must be > 0 if supplied.
    pause_count:
        Number of pauses detected by an ASR system.  Must be >= 0.
    filler_count:
        Override for filler-word count (e.g. from ASR confidence tags).
        If omitted the function counts fillers in the transcript text.

    Returns
    -------
    dict with keys ``score``, ``dimensions``, ``observations``, ``limitations``.
    """
    # --- validate inputs ---------------------------------------------------
    if duration_seconds is not None and duration_seconds <= 0:
        raise ValueError("duration_seconds must be > 0")
    if pause_count is not None and pause_count < 0:
        raise ValueError("pause_count must be >= 0")
    if filler_count is not None and filler_count < 0:
        raise ValueError("filler_count must be >= 0")

    # --- basic text stats -------------------------------------------------
    words = transcript.split()
    word_count = len(words)

    auto_filler_count = len(_FILLERS.findall(transcript))
    effective_filler = filler_count if filler_count is not None else auto_filler_count

    # --- derived observations ---------------------------------------------
    limitations: list[str] = [
        "This scorer is not a certified CEFR instrument; treat scores as indicative only."
    ]
    estimated = False

    if duration_seconds is not None:
        wpm = round((word_count / duration_seconds) * 60, 1)
    else:
        wpm = None
        estimated = True
        limitations.append(
            "duration_seconds not provided; pace given a neutral score of 50 (estimated)."
        )

    effective_pause_count = pause_count if pause_count is not None else 0

    # --- dimension scores -------------------------------------------------
    # 1. pace
    if wpm is not None:
        if _TARGET_WPM_LOW <= wpm <= _TARGET_WPM_HIGH:
            pace_score = 100.0
        elif wpm < _TARGET_WPM_LOW:
            pace_score = max(0.0, (wpm / _TARGET_WPM_LOW) * 100)
        else:
            pace_score = max(0.0, 100.0 - ((wpm - _TARGET_WPM_HIGH) / _TARGET_WPM_HIGH) * 100)
    else:
        pace_score = _NEUTRAL_PACE

    # 2. continuity  (fewer pauses relative to word count → higher score)
    if word_count > 0:
        pause_rate = effective_pause_count / word_count
        continuity_score = max(0.0, min(100.0, 100.0 - pause_rate * 200))
    else:
        continuity_score = 0.0

    # 3. filler control
    if word_count > 0:
        filler_rate = effective_filler / word_count
        filler_score = max(0.0, min(100.0, 100.0 - filler_rate * 300))
    else:
        filler_score = 0.0

    # 4. phrase length  (mean words between pauses; target ≥ 7)
    segments = effective_pause_count + 1
    mean_phrase = word_count / segments if word_count > 0 else 0
    phrase_score = min(100.0, (mean_phrase / 7) * 100)

    composite = round((pace_score + continuity_score + filler_score + phrase_score) / 4, 1)

    observations: dict[str, Any] = {
        "word_count": word_count,
        "filler_count": effective_filler,
    }
    if wpm is not None:
        observations["words_per_minute"] = wpm
    if duration_seconds is not None:
        observations["duration_seconds"] = duration_seconds
    if pause_count is not None:
        observations["pause_count"] = pause_count

    if estimated:
        limitations.append(
            "One or more observations were estimated rather than measured."
        )

    return {
        "score": composite,
        "dimensions": {
            "pace": round(pace_score, 1),
            "continuity": round(continuity_score, 1),
            "filler_control": round(filler_score, 1),
            "phrase_length": round(phrase_score, 1),
        },
        "observations": observations,
        "limitations": limitations,
    }


def score_speaking_sample(sample: dict[str, Any]) -> dict[str, Any]:
    """Score a speaking sample loaded from an ASR transcript JSON fixture.

    The fixture schema mirrors ``data/samples/en_speaking_b1_fluency.json``::

        {
          "language": "en",
          "skill": "speaking",
          "transcript": "...",
          "duration_seconds": 22.0,
          "pause_count": 2,
          "filler_count": 0   // optional
        }

    Parameters
    ----------
    sample:
        Parsed JSON object from a speaking sample fixture.

    Returns
    -------
    dict – same shape as :func:`score_speaking_fluency`.
    """
    transcript: str = sample.get("transcript", "")
    duration_seconds: float | None = sample.get("duration_seconds")
    pause_count: int | None = sample.get("pause_count")
    filler_count: int | None = sample.get("filler_count")

    return score_speaking_fluency(
        transcript,
        duration_seconds=duration_seconds,
        pause_count=pause_count,
        filler_count=filler_count,
    )
