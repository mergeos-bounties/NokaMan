from __future__ import annotations

import json
from pathlib import Path

from nokaman.eval.fairness import build_fairness_report, write_fairness_report


def test_build_fairness_report_covers_en_ko_ja() -> None:
    report = build_fairness_report()
    assert report["suite"] == "length_matched_en_ko_ja"
    assert set(report["languages"]) == {"en", "ko", "ja"}
    assert len(report["rows"]) == 6
    assert report["metrics"]["score_spread"] >= 0
    assert report["bias_notes"]


def test_write_fairness_report(tmp_path) -> None:
    out = write_fairness_report(tmp_path / "fairness_report.json")
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["model"] == "ToyAbilityModel"
    assert "by_language" in payload
    assert payload["mitigations"]


def test_committed_fairness_fixture_matches_schema() -> None:
    fixture = Path("data/fixtures/fairness_report.json")
    payload = json.loads(fixture.read_text(encoding="utf-8"))
    assert payload["suite"] == "length_matched_en_ko_ja"
    assert set(payload["by_language"]) == {"en", "ko", "ja"}
