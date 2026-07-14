from __future__ import annotations

from collections.abc import Iterable

from nokaman.models.cefr import score_to_cefr
from nokaman.models.toy import ToyAbilityModel
from nokaman.rubrics.registry import get_language_meta

CEFR_TARGETS = {
    "A1": 22.0,
    "A2": 42.0,
    "B1": 57.0,
    "B2": 72.0,
    "C1": 84.0,
    "C2": 94.0,
}


def adaptive_session(
    language: str,
    answers: list[str] | None = None,
    administered_ids: list[str] | None = None,
) -> dict:
    code = language.strip().lower()
    meta = get_language_meta(code)
    answer_list = [answer for answer in (answers or []) if answer.strip()]
    answer_estimates = estimate_answer_scores(code, answer_list)
    ability_score = _running_ability(answer_estimates)
    administered = set(administered_ids or [])
    next_prompt = select_next_prompt(
        ability_score=ability_score,
        prompt_bank=build_prompt_bank(code),
        administered_ids=administered,
    )
    return {
        "language": code,
        "language_name": meta["name"],
        "n_answers": len(answer_list),
        "ability_score": round(ability_score, 2),
        "cefr": score_to_cefr(ability_score),
        "answer_estimates": answer_estimates,
        "next_prompt": next_prompt,
        "complete": next_prompt is None,
        "model": "AdaptiveHeuristicSession",
    }


def estimate_answer_scores(language: str, answers: list[str]) -> list[dict]:
    model = ToyAbilityModel(language=language)
    estimates = []
    for index, answer in enumerate(answers, start=1):
        scored = model.score_text(answer, skill="writing")
        estimates.append(
            {
                "answer_index": index,
                "score": scored["score"],
                "cefr": scored["cefr"],
                "tokens": scored["features"]["tokens"],
            }
        )
    return estimates


def select_next_prompt(
    ability_score: float,
    prompt_bank: Iterable[dict],
    administered_ids: set[str] | list[str] | None = None,
) -> dict | None:
    administered = set(administered_ids or [])
    candidates = [prompt for prompt in prompt_bank if str(prompt["id"]) not in administered]
    if not candidates:
        return None
    target = max(0.0, min(100.0, float(ability_score)))
    return min(
        candidates,
        key=lambda prompt: (
            abs(float(prompt["target_score"]) - target),
            float(prompt["target_score"]),
            str(prompt["id"]),
        ),
    )


def build_prompt_bank(language: str) -> list[dict]:
    code = language.strip().lower()
    meta = get_language_meta(code)
    language_name = meta["name"]
    templates = {
        "A1": f"Introduce yourself in simple {language_name} sentences.",
        "A2": f"Describe your daily routine in {language_name} with times and places.",
        "B1": f"Explain a recent problem you solved while learning {language_name}.",
        "B2": f"Compare two study strategies and defend your preference in {language_name}.",
        "C1": f"Analyze how culture affects communication style in {language_name}.",
        "C2": f"Write a nuanced argument about language policy and education in {language_name}.",
    }
    return [
        {
            "id": f"{code}_{band.lower()}_adaptive",
            "language": code,
            "difficulty_cefr": band,
            "target_score": target,
            "prompt": templates[band],
        }
        for band, target in CEFR_TARGETS.items()
    ]


def _running_ability(answer_estimates: list[dict]) -> float:
    if not answer_estimates:
        return CEFR_TARGETS["A2"]
    return sum(float(item["score"]) for item in answer_estimates) / len(answer_estimates)
