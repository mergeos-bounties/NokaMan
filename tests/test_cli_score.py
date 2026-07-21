from pathlib import Path
import pytest
from typer.testing import CliRunner
from nokaman.cli import app

runner = CliRunner()


def test_eval_score_command():
    """Test the new eval score command."""
    
    # Test with a speaking sample
    result = runner.invoke(
        app,
        ["eval", "score", "data/samples/en_speaking_b1_fluency.json", "--table"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert "Score Details" in result.output
    assert "Overall Score" in result.output
    assert "Continuity" in result.output
    assert "Pace" in result.output


def test_eval_score_json_output():
    """Test JSON output for score command."""
    result = runner.invoke(
        app,
        ["eval", "score", "data/samples/en_speaking_b1_fluency.json", "--json"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert result.output.startswith('{\n  "score":')
    assert '"dimensions"' in result.output


def test_eval_score_non_speaking():
    """Test score command with non-speaking sample."""
    result = runner.invoke(
        app,
        ["eval", "score", "data/samples/en_writing_a1.json", "--json"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert result.output.startswith('{\n  "language": "en"')
    assert '"skill": "writing"' in result.output
