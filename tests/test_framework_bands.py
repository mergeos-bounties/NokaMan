from nokaman.models.toy import ToyAbilityModel
from nokaman.eval.pipeline import evaluate_demo


def test_en_framework_bands() -> None:
    r = ToyAbilityModel("en").score_text(
        "Although remote work is common, hybrid schedules help collaboration.",
        skill="writing",
    )
    assert "framework_bands" in r
    assert "ielts_approx" in r["framework_bands"]


def test_demo_includes_frameworks() -> None:
    d = evaluate_demo("ja")
    assert "framework_bands" in d
    assert d["framework_bands"].get("jlpt")


def test_ko_framework_bands_include_topik_track() -> None:
    r = ToyAbilityModel("ko").score_text(
        "I study Korean every morning and write short practice notes.",
        skill="writing",
    )
    bands = r["framework_bands"]
    assert bands["topik"] in {"1", "2", "3", "4", "5", "6"}
    assert bands["topik_track"] in {"TOPIK I", "TOPIK II"}
    assert bands["topik_label"] == f"{bands['topik_track']} Level {bands['topik']}"


def test_ko_demo_includes_topik_field() -> None:
    d = evaluate_demo("ko")
    bands = d["framework_bands"]
    assert bands.get("topik")
    assert bands.get("topik_track")
    assert bands.get("topik_label")
