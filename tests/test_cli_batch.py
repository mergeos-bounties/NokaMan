from __future__ import annotations

import csv
import json

from typer.testing import CliRunner

from nokaman.cli import app

runner = CliRunner()


def test_eval_batch_writes_json(tmp_path) -> None:
    out = tmp_path / "batch.json"
    result = runner.invoke(app, ["eval", "batch", "--out", str(out), "--json-only"])
    assert result.exit_code == 0
    assert "format=json" in result.stdout
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["n_samples"] > 0
    assert payload["rows"]


def test_eval_batch_writes_csv(tmp_path) -> None:
    out = tmp_path / "batch.csv"
    result = runner.invoke(
        app,
        ["eval", "batch", "--format", "csv", "--out", str(out), "--json-only"],
    )
    assert result.exit_code == 0
    assert "format=csv" in result.stdout
    with out.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert rows
    assert set(rows[0]) == {
        "file",
        "language",
        "skill",
        "score",
        "cefr",
        "expected_cefr",
        "distance",
    }
    assert rows[0]["file"].endswith(".json")


def test_eval_batch_rejects_unknown_format(tmp_path) -> None:
    out = tmp_path / "batch.txt"
    result = runner.invoke(app, ["eval", "batch", "--format", "xml", "--out", str(out)])
    assert result.exit_code == 1
    assert "--format must be json or csv" in result.stdout
    assert not out.exists()
