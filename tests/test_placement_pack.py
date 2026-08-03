from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from nokaman.cli import app
from nokaman.eval.metrics import list_placement_packs, run_placement_pack


def test_placement_packs_cover_en_ko_ja() -> None:
    packs = list_placement_packs()
    assert set(packs) >= {"en", "ko", "ja"}


def test_sample_reports_for_three_languages(tmp_path: Path) -> None:
    for lang in ("en", "ko", "ja"):
        report = run_placement_pack(lang, use_demo_answers=True)
        assert report["language"] == lang
        assert report["n_items"] >= 3
        assert report["ready_for_ui"] is True
        assert report["sample_report"] is True
        assert report["cefr"]
        out = tmp_path / f"placement_pack_{lang}.json"
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        assert out.exists()


def test_cli_placement_pack_demo() -> None:
    result = CliRunner().invoke(app, ["eval", "placement-pack", "--lang", "en", "--demo"])
    assert result.exit_code == 0, result.output
    assert "placement_en_v1" in result.output
    assert "ready_for_ui" in result.output
