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


def test_eval_score_text_prints_table() -> None:
    text = "Because the sun was bright, I walked to the market and bought fruit."
    result = CliRunner().invoke(
        app, ["eval", "score", "--text", text, "--lang", "en"],
    )
    assert result.exit_code == 0, result.output
    out = result.output
    # Rich table must appear with the named dimensions.
    for dim in ("Writing (overall)", "Vocabulary", "Grammar", "Reading", "Listening", "Speaking"):
        assert dim in out, f"missing dimension {dim} in: {out}"
    assert "Overall" in out
    assert "CEFR" in out


def test_eval_score_text_json_is_valid() -> None:
    text = "The cat sat on the mat because it was tired."
    result = CliRunner().invoke(
        app, ["eval", "score", "--text", text, "--lang", "en", "--json"],
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert "score" in data
    assert "cefr" in data
    assert "language" in data


def test_eval_score_sample_prints_table() -> None:
    result = CliRunner().invoke(
        app, ["eval", "score", "--text", "The project was large and complex.", "--lang", "en"],
    )
    assert result.exit_code == 0, result.output


def test_eval_score_requires_input() -> None:
    result = CliRunner().invoke(app, ["eval", "score"])
    assert result.exit_code == 1, result.output
    assert "Provide --sample or --text" in result.output
