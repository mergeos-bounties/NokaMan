from __future__ import annotations

import csv
import json
from pathlib import Path

from typer.testing import CliRunner

from nokaman.cli import app

runner = CliRunner()


def test_eval_batch_csv_output(tmp_path) -> None:
    """Test that eval batch --format csv writes a valid CSV file."""
    out_path = tmp_path / "batch.csv"
    result = runner.invoke(
        app,
        ["eval", "batch", "--format", "csv", "--out", str(out_path)],
    )
    assert result.exit_code == 0, result.output
    assert out_path.exists(), f"Expected CSV file at {out_path}"
    # Check that it's a valid CSV with header
    with open(out_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # We expect at least one row
        rows = list(reader)
        assert len(rows) >= 1
        # Check that the expected columns are present
        expected_columns = {"file", "language", "skill", "score", "cefr", "expected_cefr", "distance"}
        assert set(reader.fieldnames) == expected_columns


def test_eval_batch_json_output(tmp_path) -> None:
    """Test that eval batch --format json writes a valid JSON file."""
    out_path = tmp_path / "batch.json"
    result = runner.invoke(
        app,
        ["eval", "batch", "--format", "json", "--out", str(out_path)],
    )
    assert result.exit_code == 0, result.output
    assert out_path.exists(), f"Expected JSON file at {out_path}"
    data = json.loads(out_path.read_text(encoding="utf-8"))
    # Check expected keys
    assert "n_samples" in data
    assert "exact_cefr_hit_rate" in data
    assert "adjacent_cefr_hit_rate" in data
    assert "by_language" in data
    assert "rows" in data
    assert isinstance(data["rows"], list)
    assert len(data["rows"]) >= 1


def test_eval_batch_table_output(tmp_path) -> None:
    """Test that eval batch --format table prints a table and creates a JSON report."""
    out_path = tmp_path / "batch.json"
    result = runner.invoke(
        app,
        ["eval", "batch", "--format", "table", "--out", str(out_path)],
    )
    assert result.exit_code == 0, result.output
    # Check that the JSON report was still created (the table format writes JSON then prints table)
    assert out_path.exists(), f"Expected JSON report at {out_path}"
    # Check that the output contains the table header
    assert "By language" in result.output
    assert "Lang" in result.output
    assert "exact" in result.output
    assert "adjacent" in result.output