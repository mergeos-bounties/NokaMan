from __future__ import annotations

import re
from collections.abc import Mapping
from itertools import pairwise

CONNECTORS = frozenset(
    {
        "also",
        "although",
        "because",
        "besides",
        "but",
        "finally",
        "first",
        "furthermore",
        "however",
        "meanwhile",
        "moreover",
        "next",
        "so",
        "then",
        "therefore",
        "though",
        "thus",
        "while",
        "yet",
    }
)
STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "in",
        "is",
        "it",
        "of",
        "on",
        "or",
        "that",
        "the",
        "to",
        "was",
        "were",
        "with",
    }
)
DIMENSION_WEIGHTS = {
    "cohesion": 0.50,
    "coherence": 0.50,
}
BASE_LIMITATIONS = (
    "Cohesion/coherence stubs use surface heuristics and do not parse discourse structure.",
    "Connector detection is English-oriented and least reliable for other languages.",
    "Lexical overlap is only a weak proxy for topic continuity and reference chains.",
    "The result is an offline product signal, not a certified CEFR writing assessment.",
)


def _words(text: str) -> list[str]:
    return re.findall(r"[^\W\d_]+(?:['-][^\W\d_]+)*", text.lower(), flags=re.UNICODE)


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [part.strip() for part in parts if _words(part)]


def _paragraphs(text: str) -> list[str]:
    parts = re.split(r"\n\s*\n", text.strip())
    return [part.strip() for part in parts if _words(part)]


def _content_words(text: str) -> set[str]:
    return {word for word in _words(text) if word not in STOPWORDS and word not in CONNECTORS}


def _clamp(value: float) -> float:
    return round(max(0.0, min(100.0, value)), 2)


def _cohesion_score(text: str, connector_count: int | None) -> tuple[float, int, float]:
    sentences = _sentences(text)
    words = _words(text)
    observed_connectors = (
        connector_count
        if connector_count is not None
        else sum(word in CONNECTORS for word in words)
    )
    if len(sentences) < 2:
        overlap = 0.0
    else:
        ratios: list[float] = []
        for left, right in pairwise(sentences):
            left_words = _content_words(left)
            right_words = _content_words(right)
            if not left_words or not right_words:
                ratios.append(0.0)
                continue
            ratios.append(len(left_words & right_words) / len(left_words | right_words))
        overlap = sum(ratios) / len(ratios)

    connector_density = observed_connectors / max(1, len(sentences))
    connector_component = _clamp(connector_density / 0.75 * 100)
    overlap_component = _clamp(overlap / 0.35 * 100)
    score = _clamp(connector_component * 0.55 + overlap_component * 0.45)
    return score, observed_connectors, round(overlap, 4)


def _coherence_score(
    text: str,
    paragraph_count: int | None,
) -> tuple[float, int, float]:
    paragraphs = _paragraphs(text)
    sentences = _sentences(text)
    observed_paragraphs = paragraph_count if paragraph_count is not None else len(paragraphs)
    if len(paragraphs) < 2:
        topic_continuity = 1.0 if sentences else 0.0
    else:
        ratios: list[float] = []
        for left, right in pairwise(paragraphs):
            left_words = _content_words(left)
            right_words = _content_words(right)
            if not left_words or not right_words:
                ratios.append(0.0)
                continue
            ratios.append(len(left_words & right_words) / len(left_words | right_words))
        topic_continuity = sum(ratios) / len(ratios)

    # Prefer a small number of paragraphs relative to sentence count.
    if not sentences:
        structure = 0.0
    else:
        ratio = observed_paragraphs / len(sentences)
        if 0.15 <= ratio <= 0.5:
            structure = 100.0
        elif ratio < 0.15:
            structure = _clamp(ratio / 0.15 * 100)
        else:
            structure = _clamp(max(0.0, 1.2 - ratio) / 0.7 * 100)

    score = _clamp(structure * 0.55 + _clamp(topic_continuity / 0.4 * 100) * 0.45)
    return score, observed_paragraphs, round(topic_continuity, 4)


def score_writing_cohesion(
    text: str,
    *,
    paragraph_count: int | None = None,
    connector_count: int | None = None,
) -> dict:
    """Score writing cohesion/coherence stubs with deterministic offline heuristics."""
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("text must not be empty")
    words = _words(cleaned)
    if not words:
        raise ValueError("text must contain words")
    if paragraph_count is not None and paragraph_count < 1:
        raise ValueError("paragraph_count must be at least 1")
    if connector_count is not None and connector_count < 0:
        raise ValueError("connector_count must not be negative")

    cohesion, observed_connectors, adjacent_overlap = _cohesion_score(cleaned, connector_count)
    coherence, observed_paragraphs, topic_continuity = _coherence_score(cleaned, paragraph_count)
    dimensions = {"cohesion": cohesion, "coherence": coherence}
    overall = _clamp(sum(dimensions[name] * weight for name, weight in DIMENSION_WEIGHTS.items()))

    limitations = list(BASE_LIMITATIONS)
    if connector_count is None:
        limitations.append("Connector count was estimated from a small English connector list.")
    if paragraph_count is None:
        limitations.append("Paragraph count was estimated from blank-line separation.")

    return {
        "score": overall,
        "dimensions": dimensions,
        "observations": {
            "word_count": len(words),
            "sentence_count": len(_sentences(cleaned)),
            "paragraph_count": observed_paragraphs,
            "connector_count": observed_connectors,
            "adjacent_sentence_overlap": adjacent_overlap,
            "topic_continuity": topic_continuity,
        },
        "limitations": limitations,
    }


def score_writing_sample(sample: Mapping[str, object]) -> dict:
    """Score a writing sample containing optional cohesion observations."""
    if str(sample.get("skill") or "").strip().lower() != "writing":
        raise ValueError("sample skill must be writing")
    observations = sample.get("cohesion_observations") or {}
    if not isinstance(observations, Mapping):
        raise TypeError("cohesion_observations must be an object")
    return score_writing_cohesion(
        str(sample.get("text") or ""),
        paragraph_count=_optional_int(observations.get("paragraph_count")),
        connector_count=_optional_int(observations.get("connector_count")),
    )


def _optional_int(value: object) -> int | None:
    return None if value is None else int(value)
