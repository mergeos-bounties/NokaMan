from __future__ import annotations

import hashlib
import json
import random
import re
from pathlib import Path
from typing import Any

from nokaman.config import RUNS_DIR
from nokaman.data.loader import list_sample_files, load_sample
from nokaman.eval.pipeline import evaluate_sample_file

MODEL_NAME = "ToyAbilityModel"
DEFAULT_EPOCHS = 3
DEFAULT_SEED = 7


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""
    if value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]

    lowered = value.lower()
    if lowered in {"true", "yes", "on"}:
        return True
    if lowered in {"false", "no", "off"}:
        return False
    if lowered in {"null", "none"}:
        return None

    try:
        return int(value)
    except ValueError:
        pass

    try:
        return float(value)
    except ValueError:
        return value


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    """
    Parse the small YAML subset used by calibration config files without
    requiring PyYAML at runtime.
    """
    payload: dict[str, Any] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            raise ValueError(f"unsupported config line: {line!r}")

        key, raw_value = stripped.split(":", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"missing config key in line: {line!r}")
        payload[key] = _parse_scalar(raw_value.split(" #", 1)[0])
    return payload


def load_calibration_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load a JSON or simple YAML calibration config."""
    if path is None:
        return {}

    config_path = Path(path)
    text = config_path.read_text(encoding="utf-8")
    if config_path.suffix.lower() == ".json":
        payload = json.loads(text)
    else:
        payload = _parse_simple_yaml(text)

    if not isinstance(payload, dict):
        raise ValueError("calibration config must be a mapping")
    return payload


def _clean_run_id(run_id: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", run_id).strip(".-")
    return cleaned or "toy-calibration"


def _stable_run_id(config: dict[str, Any]) -> str:
    requested = config.get("run_id")
    if requested:
        return _clean_run_id(str(requested))

    digest = hashlib.sha256(json.dumps(config, sort_keys=True).encode("utf-8")).hexdigest()
    return f"toy-{digest[:12]}"


def _config_hash(config: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(config, sort_keys=True).encode("utf-8")).hexdigest()[:12]


def _completed_report(path: Path, epochs: int, config_hash: str) -> dict[str, Any] | None:
    if not path.exists():
        return None

    report = json.loads(path.read_text(encoding="utf-8"))
    history = report.get("history") or []
    if (
        report.get("status") == "complete"
        and report.get("config_hash") == config_hash
        and len(history) >= epochs
    ):
        return report
    return None


def train_toy(
    epochs: int | None = None,
    *,
    config_path: str | Path | None = None,
    seed: int | None = None,
    run_id: str | None = None,
    resume: bool | None = None,
) -> dict:
    """
    Calibration loop for the toy model: evaluate bundled samples each epoch
    and report exact CEFR hit-rate when expected_cefr is present.
    """
    file_config = load_calibration_config(config_path)
    resolved_config = {
        "model": MODEL_NAME,
        "epochs": int(epochs if epochs is not None else file_config.get("epochs", DEFAULT_EPOCHS)),
        "seed": int(seed if seed is not None else file_config.get("seed", DEFAULT_SEED)),
        "resume": bool(resume if resume is not None else file_config.get("resume", True)),
    }
    if run_id is not None:
        resolved_config["run_id"] = run_id
    elif file_config.get("run_id") is not None:
        resolved_config["run_id"] = str(file_config["run_id"])
    else:
        resolved_config["run_id"] = _stable_run_id(
            {
                "model": resolved_config["model"],
                "epochs": resolved_config["epochs"],
                "seed": resolved_config["seed"],
            }
        )
    resolved_config["run_id"] = _clean_run_id(str(resolved_config["run_id"]))
    config_hash = _config_hash(
        {
            "model": resolved_config["model"],
            "epochs": resolved_config["epochs"],
            "seed": resolved_config["seed"],
            "run_id": resolved_config["run_id"],
        }
    )

    samples = list_sample_files()
    if not samples:
        raise FileNotFoundError("no samples under data/samples")

    random.seed(resolved_config["seed"])
    run_dir = RUNS_DIR / resolved_config["run_id"]
    report_path = run_dir / "toy_train_report.json"
    dashboard_path = run_dir / "dashboard.json"
    if resolved_config["resume"]:
        existing = _completed_report(report_path, resolved_config["epochs"], config_hash)
        if existing is not None and dashboard_path.exists():
            return {
                "report_path": str(report_path),
                "dashboard_path": str(dashboard_path),
                "resumed": True,
                **existing,
            }

    history = []
    for epoch in range(1, max(1, resolved_config["epochs"]) + 1):
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
    run_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "run_id": resolved_config["run_id"],
        "model": MODEL_NAME,
        "status": "complete",
        "epochs": resolved_config["epochs"],
        "seed": resolved_config["seed"],
        "config_hash": config_hash,
        "history": history,
    }
    last = history[-1]
    dashboard = {
        "run_id": resolved_config["run_id"],
        "model": MODEL_NAME,
        "status": "complete",
        "metrics": {
            "exact_cefr_hit_rate": last["exact_cefr_hit_rate"],
            "n_labeled": last["n_labeled"],
            "n_samples": last["n_samples"],
        },
        "report_path": str(report_path),
    }

    report["dashboard_path"] = str(dashboard_path)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    dashboard_path.write_text(json.dumps(dashboard, indent=2) + "\n", encoding="utf-8")
    legacy_path = RUNS_DIR / "toy_train_report.json"
    legacy_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return {
        "report_path": str(report_path),
        "dashboard_path": str(dashboard_path),
        "resumed": False,
        **report,
    }
