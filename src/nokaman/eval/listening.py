from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from nokaman.data.loader import load_listening_pack
from nokaman.models.cefr import compare_bands, score_to_cefr
from nokaman.rubrics.registry import get_language_meta

_DIFFICULTY_BASE = {
    "A1": 22.0,
    "A2": 42.0,
    "B1": 57.0,
    "B2": 72.0,
    "C1": 84.0,
    "C2": 94.0,
}


def evaluate_listening_pack_file(path: Path) -> dict:
    pack = load_listening_pack(path)
    result = score_listening_pack(pack)
    expected = pack.get("expected_cefr")
    if expected:
        result["band_check"] = compare_bands(result["cefr"], str(expected))
    result["source"] = str(path)
    return result


def score_listening_pack(pack: dict[str, Any]) -> dict:
    language = str(pack.get("language") or "en").strip().lower()
    meta = get_language_meta(language)
    items = list(pack.get("items") or pack.get("questions") or [])
    learner_answers = pack.get("answers") if isinstance(pack.get("answers"), dict) else {}

    scored_items = []
    earned = 0.0
    possible = 0.0
    for index, item in enumerate(items, start=1):
        item_id = str(item.get("id") or f"q{index}")
        response = item.get("response")
        if response is None:
            response = learner_answers.get(item_id)
        weight = _positive_weight(item.get("weight", 1.0))
        credit = _score_item(item, response)
        earned += credit * weight
        possible += weight
        scored_items.append(
            {
                "id": item_id,
                "type": str(item.get("type") or "mcq"),
                "weight": weight,
                "response": response,
                "credit": round(credit, 4),
                "correct": credit >= 1.0,
            }
        )

    accuracy = (earned / possible * 100.0) if possible else 0.0
    difficulty = str(pack.get("difficulty_cefr") or pack.get("expected_cefr") or "").upper()
    score = _ability_score(accuracy, difficulty)
    cefr = score_to_cefr(score)
    return {
        "id": pack.get("id"),
        "language": language,
        "language_name": meta["name"],
        "skill": "listening",
        "score": round(score, 2),
        "accuracy": round(accuracy, 2),
        "cefr": cefr,
        "difficulty_cefr": difficulty or None,
        "n_items": len(items),
        "earned_weight": round(earned, 4),
        "possible_weight": round(possible, 4),
        "items": scored_items,
        "model": "ListeningProxyScorer",
    }


def _score_item(item: dict[str, Any], response: object) -> float:
    kind = str(item.get("type") or "mcq").strip().lower()
    normalized_response = _normalize(response)
    if not normalized_response:
        return 0.0

    accepted = [_normalize(value) for value in _accepted_answers(item)]
    accepted = [value for value in accepted if value]
    if normalized_response in accepted:
        return 1.0

    if kind in {"short_answer", "short", "free_text"}:
        keywords = [_normalize(value) for value in item.get("keywords", [])]
        keywords = [value for value in keywords if value]
        if keywords:
            hits = sum(1 for keyword in keywords if keyword in normalized_response)
            return hits / len(keywords)

    return 0.0


def _accepted_answers(item: dict[str, Any]) -> list[object]:
    raw = item.get("accepted_answers")
    if raw is None:
        raw = item.get("answer", item.get("correct"))
    if isinstance(raw, list):
        return raw
    return [raw]


def _ability_score(accuracy: float, difficulty: str) -> float:
    if difficulty in _DIFFICULTY_BASE:
        score = _DIFFICULTY_BASE[difficulty] + (accuracy - 70.0) * 0.5
    else:
        score = accuracy
    return max(0.0, min(100.0, score))


def _positive_weight(value: object) -> float:
    try:
        weight = float(value)
    except (TypeError, ValueError):
        return 1.0
    return weight if weight > 0 else 1.0


def _normalize(value: object) -> str:
    text = "" if value is None else str(value)
    text = text.strip().lower()
    text = re.sub(r"[^\w\s:.-]", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()
