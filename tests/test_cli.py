from __future__ import annotations

import json

from typer.testing import CliRunner

from nokaman.cli import app
from nokaman.data.loader import catalog_samples, filter_sample_catalog


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


def test_samples_list_table_filters_language_and_skill() -> None:
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["samples", "list", "--language", "en", "--skill", "writing"],
    )

    assert result.exit_code == 0, result.output
    assert "Samples (" in result.output
    assert "en_writing_b1" in result.output
    assert "en_speaking" not in result.output
    data_lines = [line for line in result.output.splitlines() if "│" in line and "en_" in line]
    assert data_lines
    assert all("writing" in line for line in data_lines)


def test_samples_list_json_and_empty_filter() -> None:
    runner = CliRunner()
    json_result = runner.invoke(app, ["samples", "list", "--language", "EN", "--json"])
    assert json_result.exit_code == 0, json_result.output
    rows = json.loads(json_result.output)
    assert rows
    assert all(row["language"] == "en" for row in rows)

    empty = runner.invoke(
        app,
        ["samples", "list", "--language", "zz", "--skill", "writing"],
    )
    assert empty.exit_code == 0, empty.output
    assert "No samples match" in empty.output


def test_filter_sample_catalog_helper(tmp_path) -> None:
    sample = {
        "id": "xx_writing_a1",
        "language": "xx",
        "skill": "writing",
        "expected_cefr": "A1",
        "text": "Hello.",
    }
    path = tmp_path / "xx_writing_a1.json"
    path.write_text(json.dumps(sample) + "\n", encoding="utf-8")

    catalog = catalog_samples(tmp_path)
    assert len(catalog) == 1
    assert catalog[0]["text_length"] == len("Hello.")

    filtered = filter_sample_catalog(catalog, language="XX", skill="Writing")
    assert len(filtered) == 1
    assert filter_sample_catalog(catalog, skill="speaking") == []
