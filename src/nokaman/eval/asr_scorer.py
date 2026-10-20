from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from nokaman.models.toy import ToyAbilityModel
from nokaman.models.cefr import score_to_cefr
from nokaman.rubrics.registry import get_language_meta


def score_asr_transcript(
    transcript_path: Path,
    language: str = "en",
    skill: str = "speaking",
) -> dict:
    """
    Score speaking proficiency from ASR transcript JSON.
    
    Expected JSON format:
    {{
        "text": "recognized speech text",
        "duration_seconds": 45.2,
        "confidence": 0.92,
        "words": [
            {{"word": "hello", "start": 0.1, "end": 0.5, "confidence": 0.95}},
            ...
        ]
    }}
    """
    if not transcript_path.exists():
        raise FileNotFoundError(f"Transcript not found: {transcript_path}")

    with open(transcript_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    text = str(data.get("text") or "").strip()
    duration = float(data.get("duration_seconds") or 0.0)
    confidence = float(data.get("confidence") or 1.0)
    words = data.get("words") or []

    if not text:
        return {
            "language": language,
            "skill": skill,
            "score": 0.0,
            "cefr": "A1",
            "error": "Empty transcript",
            "model": "ASRTranscriptScorer",
        }

    # Base text scoring
    model = ToyAbilityModel(language=language)
    result = model.score_text(text, skill=skill)

    # Speaking-specific adjustments
    wpm = (len(text.split()) / (duration / 60.0)) if duration > 0 else 0.0
    # Fluency: words per minute (A1: ~50, A2: ~70, B1: ~90, B2: ~110, C1: ~130, C2: ~150)
    fluency_score = min(100.0, (wpm / 150.0) * 100.0)

    # Pausing: long pauses indicate lower fluency
    pause_penalty = 0.0
    if words and len(words) > 1:
        pauses = []
        for i in range(1, len(words)):
            gap = words[i].get("start", 0) - words[i-1].get("end", 0)
            if gap > 0.5:  # pause > 500ms
                pauses.append(gap)
        if pauses:
            avg_pause = sum(pauses) / len(pauses)
            pause_penalty = min(15.0, (avg_pause / 2.0) * 10.0)

    # ASR confidence weighting
    confidence_weight = confidence  # 0.0-1.0

    # Combine: base score + fluency boost - pause penalty, weighted by ASR confidence
    base_score = result["score"]
    speaking_score = (base_score * 0.6 + fluency_score * 0.4) * confidence_weight - pause_penalty
    speaking_score = max(0.0, min(100.0, speaking_score))

    cefr = score_to_cefr(speaking_score)
    meta = get_language_meta(language)

    return {
        "language": language,
        "language_name": meta["name"],
        "skill": skill,
        "score": round(speaking_score, 2),
        "cefr": cefr,
        "frameworks": meta["frameworks"],
        "features": {
            "words": len(text.split()),
            "duration_seconds": duration,
            "wpm": round(wpm, 1),
            "asr_confidence": confidence,
            "pause_count": len(pauses) if words else 0,
            "avg_pause_seconds": round(sum(pauses) / len(pauses), 2) if pauses else 0.0,
            "pause_penalty": round(pause_penalty, 2),
            "base_score": round(base_score, 2),
            "fluency_score": round(fluency_score, 2),
        },
        "model": "ASRTranscriptScorer",
    }


def score_asr_transcript_text(
    text: str,
    language: str = "en",
    duration_seconds: float = 0.0,
    confidence: float = 1.0,
) -> dict:
    """Score speaking from raw transcript text (without JSON file)."""
    if not text.strip():
        return {
            "language": language,
            "skill": "speaking",
            "score": 0.0,
            "cefr": "A1",
            "error": "Empty transcript",
            "model": "ASRTranscriptScorer",
        }

    model = ToyAbilityModel(language=language)
    result = model.score_text(text, skill="speaking")

    wpm = (len(text.split()) / (duration_seconds / 60.0)) if duration_seconds > 0 else 0.0
    fluency_score = min(100.0, (wpm / 150.0) * 100.0)

    speaking_score = (result["score"] * 0.6 + fluency_score * 0.4) * confidence
    speaking_score = max(0.0, min(100.0, speaking_score))

    cefr = score_to_cefr(speaking_score)
    meta = get_language_meta(language)

    return {
        "language": language,
        "language_name": meta["name"],
        "skill": "speaking",
        "score": round(speaking_score, 2),
        "cefr": cefr,
        "frameworks": meta["frameworks"],
        "features": {
            "words": len(text.split()),
            "duration_seconds": duration_seconds,
            "wpm": round(wpm, 1),
            "asr_confidence": confidence,
            "base_score": round(result["score"], 2),
            "fluency_score": round(fluency_score, 2),
        },
        "model": "ASRTranscriptScorer",
    }