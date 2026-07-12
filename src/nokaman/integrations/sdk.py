from __future__ import annotations

from nokaman.eval.pipeline import evaluate_demo, evaluate_text


def assess_for_app(
    language: str,
    text: str,
    *,
    skill: str = "writing",
    multi_skill: bool = False,
) -> dict:
    """
    Stable JSON contract for language-learning apps.

    Returns keys: language, overall/skill scores, cefr, model, integration_version.
    """
    if multi_skill:
        from nokaman.models.toy import ToyAbilityModel

        payload = ToyAbilityModel(language=language).score_multi_skill(text)
    else:
        payload = evaluate_text(language, text, skill=skill)
    payload["integration_version"] = "nokaman.sdk.v1"
    payload["ready_for_ui"] = True
    return payload


def demo_payload(language: str = "en") -> dict:
    payload = evaluate_demo(language)
    payload["integration_version"] = "nokaman.sdk.v1"
    return payload
