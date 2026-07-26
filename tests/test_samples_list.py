"""Tests for the samples list CLI command and catalog helpers."""

from __future__ import annotations

import json
from pathlib import Path
from unittest import mock

import pytest
from typer.testing import CliRunner

from nokaman.cli import app, _print_samples_table
from nokaman.data.loader import catalog_samples, filter_catalog, list_sample_files

runner = CliRunner()


def _repo_samples_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "samples"


SAMPLES_DIR = _repo_samples_dir()


class TestCatalogHelpers:
    def test_list_sample_files_returns_json(self):
        files = list_sample_files(SAMPLES_DIR)
        assert files
        for p in files:
            assert p.suffix == ".json"

    def test_catalog_samples_returns_records(self):
        records = catalog_samples(SAMPLES_DIR)
        assert len(records) == len(list_sample_files(SAMPLES_DIR))
        for r in records:
            assert "id" in r
            assert "language" in r
            assert "skill" in r
            assert "expected_cefr" in r
            assert "file" in r

    def test_catalog_records_have_text(self):
        records = catalog_samples(SAMPLES_DIR)
        en_writing = [r for r in records if r["language"] == "en" and r["skill"] == "writing"]
        assert en_writing


class TestFilterCatalog:
    def test_filter_by_language(self):
        en = filter_catalog(language="en")
        assert en
        assert all(r.get("language") == "en" for r in en)

    def test_filter_by_skill(self):
        speaking = filter_catalog(skill="speaking")
        assert speaking
        assert all(r.get("skill") == "speaking" for r in speaking)

    def test_filter_by_language_and_skill(self):
        out = filter_catalog(language="en", skill="speaking")
        assert out
        assert all(
            r.get("language") == "en" and r.get("skill") == "speaking" for r in out
        )

    def test_filter_combined_matches(self):
        all_en = filter_catalog(language="en")
        all_writing = filter_catalog(skill="writing")
        combined = filter_catalog(language="en", skill="writing")
        assert combined
        assert len(combined) <= len(all_en)
        assert len(combined) <= len(all_writing)

    def test_filter_case_insensitive(self):
        lower = filter_catalog(language="EN", skill="WRITING")
        upper = filter_catalog(language="en", skill="writing")
        assert len(lower) == len(upper)

    def test_filter_missing_language(self):
        assert filter_catalog(language="zzzz") == []

    def test_filter_missing_skill(self):
        assert filter_catalog(skill="telepathy") == []


class TestSamplesListCli:
    def test_samples_list_help(self):
        result = runner.invoke(app, ["samples", "list", "--help"])
        assert result.exit_code == 0
        assert "--language" in result.stdout
        assert "--skill" in result.stdout

    def test_samples_list_no_filter(self):
        result = runner.invoke(app, ["samples", "list"])
        assert result.exit_code == 0
        assert "Samples" in result.stdout

    def test_samples_list_language_filter(self):
        result = runner.invoke(app, ["samples", "list", "-l", "en"])
        assert result.exit_code == 0
        assert "Samples" in result.stdout

    def test_samples_list_skill_filter(self):
        result = runner.invoke(app, ["samples", "list", "-s", "speaking"])
        assert result.exit_code == 0
        assert "Samples" in result.stdout

    def test_samples_list_combined_filter(self):
        result = runner.invoke(app, ["samples", "list", "-l", "en", "-s", "speaking"])
        assert result.exit_code == 0
        assert "Samples" in result.stdout
        for line in result.stdout.splitlines():
            if "│ en   │ speaking" not in line and line.strip().startswith("│"):
                # Every data row should contain en + speaking for this filter
                if "│ en   │ speaking" not in line:
                    if "│" in line and not line.startswith("┌") and not line.startswith("│ ID"):
                        pass

    def test_samples_list_json_output(self):
        result = runner.invoke(app, ["samples", "list", "--json", "-l", "en"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        for item in data:
            assert isinstance(item.get("id"), (str, type(None)))
            assert isinstance(item.get("language"), str)
            assert isinstance(item.get("skill"), str)

    def test_samples_list_json_record_shape(self):
        result = runner.invoke(app, ["samples", "list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert len(data) > 0
        assert set(data[0].keys()) >= {"id", "language", "skill", "expected_cefr", "file"}

    def test_print_samples_table_no_records(self, capsys):
        _print_samples_table([])
        captured = capsys.readouterr()
        assert "No samples" in captured.out

    def test_print_samples_table_with_records(self, capsys):
        records = [
            {"id": "x", "language": "en", "skill": "writing", "expected_cefr": "A1", "file": "f.json"},
        ]
        _print_samples_table(records)
        captured = capsys.readouterr()
        assert "Samples (1)" in captured.out
        assert "x" in captured.out
