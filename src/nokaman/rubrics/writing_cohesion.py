from __future__ import annotations

import re
from collections.abc import Mapping

CONNECTORS = frozenset({
    "however", "therefore", "thus", "moreover", "furthermore", "although",
    "because", "since", "while", "whereas", "nevertheless", "nonetheless",
    "meanwhile", "instead", "otherwise", "consequently", "but", "and", "or", "so"
})
DIMENSION_WEIGHTS = {
    "cohesion": 0.50,
    "coherence": 0.50,
}
BASE_LIMITATIONS = (
    "Offline cohesion relies on simple connector matching, which cannot evaluate logical flow.",
    "Coherence heuristics are estimated using paragraph and sentence structure proxies.",
    "The result is an offline product signal, not a certified CEFR writing assessment.",
)


def _words(text: str) -> list[str]:
    return re.findall(r"[^\W\d_]+(?:['-][^\W\d_]+)*", text.lower(), flags=re.UNICODE)


def _clamp(value: float) -> float:
    return round(max(0.0, min(100.0, value)), 2)


def score_writing_cohesion(text: str) -> dict:
    """Score writing cohesion/coherence with deterministic offline heuristics."""
    text = text.strip()
    if not text:
        raise ValueError("text must not be empty")

    words = _words(text)
    if not words:
        raise ValueError("text must contain words")

    paragraphs = [p for p in text.split("\n\n") if p.strip()]
    sentences = [part for part in re.split(r"[.!?]+", text) if _words(part)]
    
    observed_connectors = sum(word in CONNECTORS for word in words)
    connector_rate = observed_connectors / max(1, len(sentences)) * 100

    cohesion_score = _clamp(connector_rate * 5)
    
    coherence_score = 100.0
    if len(paragraphs) == 1 and len(sentences) > 5:
        coherence_score = 50.0
    elif len(sentences) <= 1:
        coherence_score = 30.0

    dimensions = {
        "cohesion": cohesion_score,
        "coherence": _clamp(coherence_score),
    }
    overall = _clamp(sum(dimensions[name] * weight for name, weight in DIMENSION_WEIGHTS.items()))

    return {
        "score": overall,
        "dimensions": dimensions,
        "observations": {
            "word_count": len(words),
            "sentence_count": len(sentences),
            "paragraph_count": len(paragraphs),
            "connector_count": observed_connectors,
        },
        "limitations": list(BASE_LIMITATIONS),
    }


def score_writing_sample(sample: Mapping[str, object]) -> dict:
    """Score a writing sample for cohesion/coherence."""
    if str(sample.get("skill") or "").strip().lower() != "writing":
        raise ValueError("sample skill must be writing")
    return score_writing_cohesion(str(sample.get("text") or ""))
