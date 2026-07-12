from __future__ import annotations

from pathlib import Path

from nokaman.train import toy_train as toy_train_mod
from nokaman.train.toy_train import train_toy


def test_train_toy_report(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(toy_train_mod, "RUNS_DIR", tmp_path / "runs")
    report = train_toy(epochs=2)
    assert "history" in report
    assert Path(report["report_path"]).exists()
