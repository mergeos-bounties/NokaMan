"""Tests for the JLPT band adapter.

Exercises :mod:`nokaman.models.jlpt` and verifies that Japanese
assessments surface a JLPT ``N5``–``N1`` view alongside the CEFR band.

Acceptance for bounty #7 (NokaMan):
- Adapter + tests
- Demo output includes jlpt field for ``ja``
"""

from __future__ import annotations

from nokaman.eval.pipeline import evaluate_demo
from nokaman.models.jlpt import JLPT_BANDS, jlpt_descriptions, jlpt_rank, score_to_jlpt
from nokaman.models.toy import ToyAbilityModel

# ---- canonical threshold checks -----------------------------------------


def test_score_to_jlpt_returns_a_known_band() -> None:
    for score in [0, 29, 44, 59, 79, 100]:
        assert score_to_jlpt(score) in JLPT_BANDS


def test_score_to_jlpt_thresholds() -> None:
    # Bands step up monotonically as the score rises.
    assert score_to_jlpt(0) == "N5"
    assert score_to_jlpt(10) == "N5"
    assert score_to_jlpt(30) == "N4"
    assert score_to_jlpt(45) == "N3"
    assert score_to_jlpt(60) == "N2"
    assert score_to_jlpt(80) == "N1"
    assert score_to_jlpt(100) == "N1"


def test_score_to_jlpt_clamps_out_of_range() -> None:
    assert score_to_jlpt(-10) == "N5"
    assert score_to_jlpt(150) == "N1"


# ---- rank helpers -------------------------------------------------------


def test_jlpt_rank_ordering() -> None:
    ranks = [jlpt_rank(b) for b in JLPT_BANDS]
    assert ranks == [0, 1, 2, 3, 4]


def test_jlpt_rank_unknown_falls_back_to_zero() -> None:
    assert jlpt_rank("X9") == 0
    assert jlpt_rank("") == 0


def test_jlpt_rank_is_case_insensitive() -> None:
    assert jlpt_rank("n3") == jlpt_rank("N3")


# ---- descriptions -------------------------------------------------------


def test_jlpt_descriptions_covers_all_bands() -> None:
    descs = jlpt_descriptions()
    assert set(descs) == set(JLPT_BANDS)
    for desc in descs.values():
        assert isinstance(desc, str) and len(desc) > 20


# ---- wiring into ToyAbilityModel / demo --------------------------------


def test_ja_score_text_exposes_jlpt_in_framework_bands() -> None:
    result = ToyAbilityModel("ja").score_text(
        "今日は日本語の文法を学びました。難しいですが、楽しかったです。",
        skill="writing",
    )
    bands = result["framework_bands"]
    assert "cefr" in bands
    assert "jlpt" in bands
    assert bands["jlpt"] in JLPT_BANDS


def test_ja_multi_skill_demo_exposes_jlpt() -> None:
    demo = evaluate_demo("ja")
    bands = demo["framework_bands"]
    assert "jlpt" in bands
    assert bands["jlpt"] in JLPT_BANDS


def test_jlpt_band_moves_with_score() -> None:
    """Higher ability scores map to harder JLPT bands."""
    low = ToyAbilityModel("ja").score_text("あ。", skill="writing")
    high = ToyAbilityModel("ja").score_text(
        "私は毎日朝早起きして、新しいプロジェクトの進捗を確認します。"
        "チームメンバーと連携し、課題を整理して改善策を提案します。"
        "来月からはクライアントとの面談も増えて、"
        "資料整理や報告書の作成にも時間がかかります。"
        "でも、責任を持って仕事を進めているので、成長を実感しています。",
        skill="writing",
    )
    assert jlpt_rank(low["framework_bands"]["jlpt"]) <= jlpt_rank(high["framework_bands"]["jlpt"])


def test_non_ja_languages_omit_jlpt() -> None:
    en = ToyAbilityModel("en").score_text("Hello world.", skill="writing")
    ko = ToyAbilityModel("ko").score_text("안녕하세요.", skill="writing")
    assert "jlpt" not in en["framework_bands"]
    assert "jlpt" not in ko["framework_bands"]
