from __future__ import annotations

import json
from pathlib import Path

from nokaman.config import RUNS_DIR
from nokaman.data.loader import list_sample_files, load_sample
from nokaman.eval.pipeline import evaluate_sample_file


def train_toy(epochs: int = 3) -> dict:
    """
    Calibration loop for the toy model: evaluate bundled samples each epoch
    and report exact CEFR hit-rate when expected_cefr is present.
    """
    samples = list_sample_files()
    if not samples:
        raise FileNotFoundError("no samples under data/samples")

    history = []
    for epoch in range(1, max(1, epochs) + 1):
        hits = 0
        scored = 0
        for path in samples:
            sample = load_sample(path)
            if not sample.get("expected_cefr"):
                continue
            scored += 1
            result = evaluate_sample_file(path)
            if result.get("band_check", {}).get("exact_match"):
                hits += 1
        acc = (hits / scored) if scored else 0.0
        history.append(
            {
                "epoch": epoch,
                "exact_cefr_hit_rate": round(acc, 4),
                "n_labeled": scored,
                "n_samples": len(samples),
            }
        )

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = RUNS_DIR / "toy_train_report.json"
    report = {
        "model": "ToyAbilityModel",
        "epochs": epochs,
        "history": history,
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return {"report_path": str(report_path), **report}
