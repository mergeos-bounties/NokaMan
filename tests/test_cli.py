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


def test_score_command(tmp_path) -> None:
    sample_path = tmp_path / "sample.json"
    sample_path.write_text(json.dumps({
        "id": "test_en_1",
        "language": "en",
        "skill": "writing",
        "text": "Hello world"
    }))
    result = CliRunner().invoke(app, ["score", "--sample", str(sample_path)])
    assert result.exit_code == 0, result.output
    assert "Overview" in result.output
    assert "Score" in result.output
    assert "tokens" in result.output
