from __future__ import annotations

from nokaman.eval.adaptive import adaptive_session, build_prompt_bank, select_next_prompt


def test_select_next_prompt_uses_nearest_unadministered_prompt() -> None:
    prompt_bank = [
        {"id": "a2", "target_score": 42.0},
        {"id": "b1", "target_score": 57.0},
        {"id": "b2", "target_score": 72.0},
    ]
    selected = select_next_prompt(ability_score=60.0, prompt_bank=prompt_bank, administered_ids={"b1"})
    assert selected is not None
    assert selected["id"] == "b2"


def test_adaptive_session_starts_at_a2_prompt() -> None:
    result = adaptive_session("en", answers=[])
    assert result["ability_score"] == 42.0
    assert result["cefr"] == "A2"
    assert result["next_prompt"]["difficulty_cefr"] == "A2"
    assert not result["complete"]


def test_adaptive_session_tracks_answer_estimates_and_skips_ids() -> None:
    first_prompt = build_prompt_bank("en")[1]
    result = adaptive_session(
        "en",
        answers=["I study English every day because it helps me talk with more people."],
        administered_ids=[first_prompt["id"]],
    )
    assert result["n_answers"] == 1
    assert result["answer_estimates"][0]["tokens"] > 0
    assert result["next_prompt"]["id"] != first_prompt["id"]
