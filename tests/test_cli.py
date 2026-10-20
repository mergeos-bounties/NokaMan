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


def test_score_sample_returns_table(tmp_path) -> None:
    """nokaman score --sample <path> exits 0 with rich table output."""
    data_dir = tmp_path / "data" / "samples"
    data_dir.mkdir(parents=True)
    sample_path = data_dir / "test_sample.json"
    sample_path.write_text(json.dumps({
        "id": "test_sample",
        "language": "en",
        "skill": "writing",
        "expected_cefr": "A2",
        "text": "I enjoy learning English every day. It is fun and useful.",
    }))

    result = CliRunner().invoke(app, ["score", "--sample", str(sample_path)])
    assert result.exit_code == 0, result.output
    # Rich table output should contain key dimensions
    assert "Score" in result.output
    assert "CEFR" in result.output
    assert "Language" in result.output


def test_score_sample_rejects_missing_file() -> None:
    """nokaman score --sample with nonexistent file exits non-zero."""
    result = CliRunner().invoke(app, ["score", "--sample", "/nonexistent/path.json"])
    assert result.exit_code != 0
