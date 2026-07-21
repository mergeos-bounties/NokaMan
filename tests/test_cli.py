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


def test_eval_score_sample_prints_table(tmp_path) -> None:
    """Test: nokaman eval score <sample> prints dimension table."""
    from nokaman.data.loader import SAMPLES_DIR
    samples = list(SAMPLES_DIR.glob("en_writing_*.json"))
    assert samples, "Need at least one en_writing sample"
    sample_path = samples[0]

    result = CliRunner().invoke(app, ["eval", "score", str(sample_path)])
    assert result.exit_code == 0, result.output
    assert "Score breakdown" in result.output or "Language" in result.output


def test_eval_score_sample_json_only(tmp_path) -> None:
    """Test: nokaman eval score <sample> --json-only returns JSON."""
    from nokaman.data.loader import SAMPLES_DIR
    samples = list(SAMPLES_DIR.glob("en_writing_*.json"))
    sample_path = samples[0]

    result = CliRunner().invoke(app, ["eval", "score", str(sample_path), "--json-only"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert "score" in data
    assert "cefr" in data
