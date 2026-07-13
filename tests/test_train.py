from __future__ import annotations

import json
from pathlib import Path

from nokaman.train import toy_train as toy_train_mod
from nokaman.train.toy_train import load_calibration_config, train_toy


def test_train_toy_report(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(toy_train_mod, "RUNS_DIR", tmp_path / "runs")
    report = train_toy(epochs=2)
    assert "history" in report
    assert Path(report["report_path"]).exists()


def test_train_toy_loads_yaml_config_and_dashboard(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(toy_train_mod, "RUNS_DIR", tmp_path / "runs")
    config_path = tmp_path / "calibration.yaml"
    config_path.write_text(
        "\n".join(
            [
                "run_id: smoke-calibration",
                "epochs: 2",
                "seed: 123",
                "resume: true",
            ]
        ),
        encoding="utf-8",
    )

    assert load_calibration_config(config_path)["epochs"] == 2
    report = train_toy(config_path=config_path)

    assert report["run_id"] == "smoke-calibration"
    assert report["epochs"] == 2
    assert report["seed"] == 123
    assert Path(report["report_path"]).exists()
    dashboard_path = Path(report["dashboard_path"])
    assert dashboard_path.exists()
    dashboard = json.loads(dashboard_path.read_text(encoding="utf-8"))
    assert sorted(dashboard) == ["metrics", "model", "report_path", "run_id", "status"]
    assert dashboard["metrics"]["n_samples"] >= 1


def test_train_toy_resumes_existing_completed_run(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(toy_train_mod, "RUNS_DIR", tmp_path / "runs")

    first = train_toy(epochs=1, run_id="stable-run", seed=99)
    second = train_toy(epochs=1, run_id="stable-run", seed=99)

    assert second["resumed"] is True
    assert second["report_path"] == first["report_path"]
    assert second["dashboard_path"] == first["dashboard_path"]
    assert second["history"] == first["history"]
