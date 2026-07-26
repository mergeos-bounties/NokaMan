"""Tests for eval score CLI command."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from nokaman.cli import app

SAMPLES = Path(__file__).parent.parent / "data" / "samples"


def test_eval_score_rich_table_output() -> None:
    """nokaman eval score --sample prints a rich table with score dimensions."""
    sample = SAMPLES / "en_writing_a1.json"
    assert sample.exists(), f"Sample not found: {sample}"

    runner = CliRunner()
    result = runner.invoke(app, ["eval", "score", "--sample", str(sample)])

    assert result.exit_code == 0, f"Exit code: {result.exit_code}\n{result.output}"
    assert "Language" in result.output
    assert "Score" in result.output
    assert "CEFR" in result.output
    assert "Features" in result.output
    assert "tokens" in result.output
    assert "Source:" in result.output


def test_eval_score_json_output() -> None:
    """nokaman eval score --sample --json outputs raw JSON."""
    sample = SAMPLES / "en_writing_a1.json"
    assert sample.exists()

    runner = CliRunner()
    result = runner.invoke(
        app, ["eval", "score", "--sample", str(sample), "--json"]
    )

    assert result.exit_code == 0
    assert result.output.strip().startswith("{")
    assert '"language"' in result.output
    assert '"score"' in result.output
    assert '"cefr"' in result.output


def test_eval_score_different_language() -> None:
    """Score works for non-English samples."""
    sample = SAMPLES / "ko_writing_a1.json"
    if not sample.exists():
        # Try alternative path
        alt = SAMPLES / "ja_writing_a1.json"
        if alt.exists():
            sample = alt
        else:
            # Find any non-English sample
            for p in SAMPLES.glob("*_writing_a1.json"):
                if "en_" not in p.name:
                    sample = p
                    break

    if not sample.exists():
        return  # Skip if no suitable sample

    runner = CliRunner()
    result = runner.invoke(app, ["eval", "score", "--sample", str(sample)])

    assert result.exit_code == 0
    assert "Language" in result.output
    assert "Score" in result.output


def test_eval_score_requires_sample() -> None:
    """nokaman eval score without --sample should fail."""
    runner = CliRunner()
    result = runner.invoke(app, ["eval", "score"])

    assert result.exit_code != 0


def test_eval_score_nonexistent_file() -> None:
    """nokaman eval score with a nonexistent file should fail."""
    runner = CliRunner()
    result = runner.invoke(
        app, ["eval", "score", "--sample", "/nonexistent/path.json"]
    )

    assert result.exit_code != 0


def test_eval_score_band_check_displayed() -> None:
    """Band check info appears in the rich table when expected_cefr is present."""
    sample = SAMPLES / "en_writing_a1.json"
    assert sample.exists()

    runner = CliRunner()
    result = runner.invoke(app, ["eval", "score", "--sample", str(sample)])

    assert result.exit_code == 0
    # Band check should be present since the sample has expected_cefr
    assert "Band Check" in result.output


def test_eval_score_README_snippet(tmp_path: Path) -> None:
    """Generate a README snippet showing sample usage."""
    sample = SAMPLES / "en_writing_a1.json"
    assert sample.exists()

    runner = CliRunner()
    result = runner.invoke(app, ["eval", "score", "--sample", str(sample)])

    assert result.exit_code == 0
    snippet = f"""## nokaman eval score

Evaluate a single sample file and view dimension scores:

```console
$ nokaman eval score --sample data/samples/en_writing_a1.json
{result.output.strip()}
```
"""
    readme_path = tmp_path / "SCORE_README.md"
    readme_path.write_text(snippet, encoding="utf-8")
    assert readme_path.exists()
    assert "nokaman eval score" in readme_path.read_text(encoding="utf-8")