from __future__ import annotations

from pathlib import Path

from nokaman.data.loader import load_sample
from nokaman.models.cefr import compare_bands
from nokaman.models.toy import ToyAbilityModel
from nokaman.rubrics.registry import get_language_meta


def evaluate_text(language: str, text: str, skill: str = "writing") -> dict:
    meta = get_language_meta(language)
    model = ToyAbilityModel(language=meta["code"])
    result = model.score_text(text, skill=skill)
    result["language_name"] = meta["name"]
    result["frameworks"] = meta["frameworks"]
    return result


def evaluate_sample_file(path: Path) -> dict:
    sample = load_sample(path)
    result = evaluate_text(
        language=str(sample.get("language") or "en"),
        text=str(sample.get("text") or ""),
        skill=str(sample.get("skill") or "writing"),
    )
    expected = sample.get("expected_cefr")
    if expected:
        result["band_check"] = compare_bands(result["cefr"], str(expected))
    result["sample_id"] = sample.get("id")
    result["source"] = str(path)
    return result


def evaluate_demo(language: str) -> dict:
    demos = {
        "en": "I enjoy learning languages because it helps me meet people and travel with confidence.",
        "ko": "저는 한국어를 공부하고 있습니다. 매일 단어를 외우고 짧은 일기를 씁니다.",
        "ja": "毎日日本語を勉強しています。会話の練習もしたいです。",
        "vi": "Tôi đang học tiếng Việt và thích đọc truyện ngắn mỗi ngày.",
        "zh": "我每天学习中文，喜欢和朋友练习口语。",
        "es": "Estoy aprendiendo español y practico con canciones todos los días.",
        "fr": "J'apprends le français et j'aime lire de petits articles.",
        "de": "Ich lerne Deutsch und übe jeden Tag neue Wörter.",
    }
    code = language.strip().lower()
    text = demos.get(code, demos["en"])
    model = ToyAbilityModel(language=code)
    multi = model.score_multi_skill(text)
    multi["demo_text"] = text
    multi["language_name"] = get_language_meta(code)["name"]
    return multi
