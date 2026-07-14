from __future__ import annotations

import json

from typer.testing import CliRunner

from nokaman.cli import app
from nokaman.data.coverage import language_skill_coverage


def test_language_skill_coverage_counts_samples() -> None:
    report = language_skill_coverage()
    rows = {row["code"]: row for row in report["languages"]}

    assert report["skills"] == [
        "vocabulary",
        "grammar",
        "reading",
        "writing",
        "listening",
        "speaking",
    ]
    assert rows["en"]["total"] >= 1
    assert rows["en"]["skills"]["writing"] >= 1
    assert rows["en"]["has_rubric"] is True


def test_languages_coverage_json_command() -> None:
    result = CliRunner().invoke(app, ["languages", "coverage", "--json"])

    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    rows = {row["code"]: row for row in report["languages"]}
    assert rows["ja"]["skills"]["writing"] >= 1
    assert rows["ja"]["has_rubric"] is True
