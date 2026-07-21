from __future__ import annotations

import json

from typer.testing import CliRunner

from nokaman.cli import app


def test_eval_batch_writes_nested_output_path(tmp_path) -> None:
    out_path = tmp_path / "data" / "out" / "batch.json"
    result = CliRunner().invoke(
        app,
        ["eval", "batch", "--out", str(out_path), "--json-only"],
    )

    assert result.exit_code == 0, result.output
    assert out_path.exists()
    report = json.loads(out_path.read_text(encoding="utf-8"))
    assert report["n_samples"] >= 1
    assert "by_language" in report
    assert "rows" in report


def test_eval_score_outputs_table() -> None:
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["eval", "score", "--sample", "data/samples/en_writing_a1.json"],
    )
    assert result.exit_code == 0
    assert "Score: en_writing_a1.json" in result.output
    assert "Language" in result.output
    assert "en" in result.output
    assert "Score" in result.output
    assert "48.27" in result.output


def test_eval_samples_list_filters() -> None:
    runner = CliRunner()
    # Test language filter
    result = runner.invoke(
        app,
        ["eval", "samples-list", "--language", "en", "--skill", "writing"],
    )
    assert result.exit_code == 0
    assert "Samples (19 filtered)" in result.output
    assert "en_writing_a1.json" in result.output
    assert "fr_writing_a1.json" not in result.output  # French should be filtered out
    
    # Test no filters
    result = runner.invoke(app, ["eval", "samples-list"])
    assert result.exit_code == 0
    assert "Samples (63 filtered)" in result.output  # All samples
