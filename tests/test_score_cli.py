from __future__ import annotations

import json

from typer.testing import CliRunner

from nokaman.cli import app


def test_score_command_basic() -> None:
    result = CliRunner().invoke(
        app,
        ["score", "--sample", "data/samples/en_writing_b2.json"],
    )

    assert result.exit_code == 0, result.output
    # Check table output contains expected fields
    assert "Score Report" in result.output
    assert "en_writing_b2.json" in result.output
    assert "Language" in result.output
    assert "Score" in result.output
    assert "CEFR" in result.output


def test_score_command_json_output() -> None:
    result = CliRunner().invoke(
        app,
        ["score", "--sample", "data/samples/en_writing_b2.json", "--json"],
    )

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["sample_id"] == "en_writing_b2"
    assert data["language"] == "en"
    assert data["skill"] == "writing"
    assert 0 <= data["score"] <= 100
    assert data["cefr"] in {"A1", "A2", "B1", "B2", "C1", "C2"}
    assert "framework_bands" in data
    assert "features" in data


def test_score_command_framework_bands() -> None:
    result = CliRunner().invoke(
        app,
        ["score", "--sample", "data/samples/ja_writing_b1.json"],
    )

    assert result.exit_code == 0, result.output
    assert "Framework Bands" in result.output
    assert "jlpt" in result.output.lower()


def test_score_command_korean_topik() -> None:
    result = CliRunner().invoke(
        app,
        ["score", "--sample", "data/samples/ko_writing_b1.json"],
    )

    assert result.exit_code == 0, result.output
    assert "Framework Bands" in result.output
    assert "topik" in result.output.lower()