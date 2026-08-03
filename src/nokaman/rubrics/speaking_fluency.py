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


def _normalize_confidence(value: object) -> float | None:
    """Accept ASR confidence as 0–1 or 0–100; return 0–1."""
    if value is None:
        return None
    conf = float(value)
    if conf < 0:
        raise ValueError("confidence must not be negative")
    if conf > 1.0:
        if conf > 100:
            raise ValueError("confidence must be <= 100")
        conf = conf / 100.0
    return round(conf, 4)


def _feedback_bullets(dimensions: Mapping[str, float], confidence: float | None) -> list[str]:
    bullets: list[str] = []
    pace = float(dimensions.get("pace", 50))
    continuity = float(dimensions.get("continuity", 50))
    fillers = float(dimensions.get("filler_control", 50))
    phrases = float(dimensions.get("phrase_length", 50))

    if pace < 55:
        bullets.append("Pace looks slow or rushed for a clear spoken delivery — aim for a steady mid-tempo.")
    elif pace >= 85:
        bullets.append("Pace is in a comfortable speaking range.")
    else:
        bullets.append("Pace is usable; add duration_seconds from ASR for a sharper reading.")

    if continuity < 60:
        bullets.append("Continuity is choppy — reduce pauses or regroup ideas into fewer clauses.")
    else:
        bullets.append("Continuity looks stable across the transcript.")

    if fillers < 70:
        bullets.append("Filler words are elevated — practice replacing uh/um with short silent pauses.")
    else:
        bullets.append("Filler control looks good on this transcript.")

    if phrases < 50:
        bullets.append("Phrases are short — expand answers with one supporting detail per idea.")
    else:
        bullets.append("Phrase length supports connected speech.")

    if confidence is not None and confidence < 0.7:
        bullets.append(
            f"ASR confidence is low ({confidence:.0%}); treat the score as approximate until a cleaner transcript is available."
        )
    elif confidence is not None:
        bullets.append(f"ASR confidence is {confidence:.0%} — transcript quality looks acceptable for offline scoring.")

    return bullets


def score_speaking_fluency(
    transcript: str,
    *,
    duration_seconds: float | None = None,
    pause_count: int | None = None,
    filler_count: int | None = None,
    confidence: float | None = None,
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
    conf = _normalize_confidence(confidence)

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
    if conf is not None:
        # Softly down-weight overall when ASR confidence is weak.
        overall = _clamp(overall * (0.85 + 0.15 * conf))

    limitations = list(BASE_LIMITATIONS)
    if duration_seconds is None:
        limitations.append("Pace uses a neutral score because duration_seconds was not provided.")
    if pause_count is None:
        limitations.append("Pause count was estimated from transcript punctuation.")
    if conf is not None and conf < 0.7:
        limitations.append("ASR confidence is below 0.7; fluency signals may be unreliable.")

    feedback = _feedback_bullets(dimensions, conf)

    return {
        "skill": "speaking",
        "score": overall,
        "dimensions": dimensions,
        "feedback": feedback,
        "observations": {
            "word_count": len(words),
            "duration_seconds": duration_seconds,
            "words_per_minute": round(words_per_minute, 2)
            if words_per_minute is not None
            else None,
            "pause_count": observed_pauses,
            "filler_count": observed_fillers,
            "average_phrase_words": round(average_phrase_words, 2),
            "confidence": conf,
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
    transcript = str(sample.get("text") or sample.get("transcript") or "")
    confidence = sample.get("confidence")
    if confidence is None:
        confidence = observations.get("confidence")
    return score_speaking_fluency(
        transcript,
        duration_seconds=_optional_float(observations.get("duration_seconds")),
        pause_count=_optional_int(observations.get("pause_count")),
        filler_count=_optional_int(observations.get("filler_count")),
        confidence=_optional_float(confidence) if confidence is not None else None,
    )


def score_asr_transcript(payload: Mapping[str, object]) -> dict:
    """
    Score an ASR-style JSON payload for app integration.

    Accepted shapes (skill must be speaking when present):
    - transcript / text
    - optional confidence (0–1 or 0–100)
    - optional fluency_observations or top-level duration_seconds / pause_count / filler_count
    """
    skill = str(payload.get("skill") or "speaking").strip().lower()
    if skill != "speaking":
        raise ValueError("ASR speaking path requires skill=speaking")
    observations = payload.get("fluency_observations") or {}
    if observations and not isinstance(observations, Mapping):
        raise ValueError("fluency_observations must be an object")
    obs = observations if isinstance(observations, Mapping) else {}
    transcript = str(payload.get("transcript") or payload.get("text") or "")
    confidence = payload.get("confidence")
    if confidence is None:
        confidence = obs.get("confidence")
    duration = payload.get("duration_seconds")
    if duration is None:
        duration = obs.get("duration_seconds")
    pause_count = payload.get("pause_count")
    if pause_count is None:
        pause_count = obs.get("pause_count")
    filler_count = payload.get("filler_count")
    if filler_count is None:
        filler_count = obs.get("filler_count")
    result = score_speaking_fluency(
        transcript,
        duration_seconds=_optional_float(duration),
        pause_count=_optional_int(pause_count),
        filler_count=_optional_int(filler_count),
        confidence=_optional_float(confidence) if confidence is not None else None,
    )
    result["language"] = str(payload.get("language") or "en").strip().lower()
    result["input"] = {
        "transcript": transcript,
        "confidence": result["observations"].get("confidence"),
    }
    return result


def _optional_float(value: object) -> float | None:
    return None if value is None else float(value)


def _optional_int(value: object) -> int | None:
    return None if value is None else int(value)
