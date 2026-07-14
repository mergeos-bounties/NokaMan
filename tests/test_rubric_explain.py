from __future__ import annotations

import json

from typer.testing import CliRunner

from nokaman.cli import app


def test_rubrics_explain_json_reports_weights() -> None:
    result = CliRunner().invoke(app, ["rubrics", "explain", "--lang", "en", "--json"])

    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    skills = {row["skill"]: row for row in report["skills"]}
    assert report["language"] == "en"
    assert "CEFR" in report["frameworks"]
    assert skills["writing"]["weight"] == 1.2
    assert skills["grammar"]["weight"] == 1.0


def test_rubrics_explain_rejects_unknown_language() -> None:
    result = CliRunner().invoke(app, ["rubrics", "explain", "--lang", "xx", "--json"])

    assert result.exit_code == 1
    assert "unsupported language" in result.output
