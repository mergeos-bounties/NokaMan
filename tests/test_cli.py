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
