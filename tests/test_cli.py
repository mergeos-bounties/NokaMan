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


def test_score_sample_rich_table(tmp_path) -> None:
    """score --sample with rich table output."""
    sample_path = tmp_path / "test_sample.json"
    sample_path.write_text(
        json.dumps(
            {
                "id": "test_sample",
                "language": "en",
                "skill": "writing",
                "expected_cefr": "B1",
                "text": "I enjoy learning new things and always try my best to improve every day.",
            }
        ),
        encoding="utf-8",
    )
    result = CliRunner().invoke(app, ["score", "--sample", str(sample_path)])
    assert result.exit_code == 0, result.output
    assert "Dimension" in result.output
    assert "Vocabulary" in result.output
    assert "Grammar" in result.output
    assert "Reading" in result.output
    assert "Writing" in result.output
    assert "Listening" in result.output
    assert "Speaking" in result.output
    assert "Overall" in result.output
    assert "Features" in result.output


def test_score_sample_json_output(tmp_path) -> None:
    """score --sample --json returns valid JSON."""
    sample_path = tmp_path / "test_sample.json"
    sample_path.write_text(
        json.dumps(
            {
                "id": "test_sample_json",
                "language": "en",
                "skill": "writing",
                "expected_cefr": "A2",
                "text": "Hello. I am learning English.",
            }
        ),
        encoding="utf-8",
    )
    result = CliRunner().invoke(app, ["score", "--sample", str(sample_path), "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["sample_id"] == "test_sample_json"
    assert data["language"] == "en"
    assert "skills" in data
    assert "vocabulary" in data["skills"]
    assert "overall" in data
    assert "cefr" in data


def test_score_sample_non_english(tmp_path) -> None:
    """score --sample with non-English sample."""
    sample_path = tmp_path / "ja_sample.json"
    sample_path.write_text(
        json.dumps(
            {
                "id": "ja_sample",
                "language": "ja",
                "skill": "writing",
                "expected_cefr": "B1",
                "text": "日本語を勉強しています。毎日たくさん練習します。",
            }
        ),
        encoding="utf-8",
    )
    result = CliRunner().invoke(app, ["score", "--sample", str(sample_path)])
    assert result.exit_code == 0, result.output
    assert "Dimension" in result.output
    assert "Overall" in result.output
    assert "JLPT" in result.output  # Framework bands for Japanese


def test_score_sample_lang_override(tmp_path) -> None:
    """score --sample --lang override works."""
    sample_path = tmp_path / "en_sample.json"
    sample_path.write_text(
        json.dumps(
            {
                "id": "en_sample",
                "language": "en",
                "skill": "writing",
                "text": "The weather is nice today and I went for a walk.",
            }
        ),
        encoding="utf-8",
    )
    result = CliRunner().invoke(
        app, ["score", "--sample", str(sample_path), "--lang", "ko"]
    )
    assert result.exit_code == 0, result.output
    # Should show TOPIK bands since we overrode to Korean
    assert "TOPIK" in result.output
