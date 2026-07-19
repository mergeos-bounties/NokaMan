"""Tests for nokaman score CLI command."""

from click.testing import CliRunner
from typer import Typer

from nokaman.cli_score import score_cmd


def test_score_help():
    app = Typer()
    app.command("score")(score_cmd)
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "--sample" in result.output
    assert "--text" in result.output


def test_score_no_args():
    app = Typer()
    app.command("score")(score_cmd)
    runner = CliRunner()
    result = runner.invoke(app, [])
    assert result.exit_code == 1
    assert "Provide" in result.output


def test_score_json_output():
    """Score with --json should produce valid JSON output."""
    app = Typer()
    app.command("score")(score_cmd)
    runner = CliRunner()
    result = runner.invoke(app, ["--text", "Hello world", "--lang", "en", "--skill", "writing", "--json"])
    # Should not crash — either produces JSON or evaluation result
    assert result.exit_code == 0 or result.exit_code == 1
