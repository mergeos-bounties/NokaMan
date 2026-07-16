from __future__ import annotations

import json
import socket
from pathlib import Path

from nokaman.eval.pipeline import evaluate_sample_file
from nokaman.rubrics.registry import CEFR_BANDS


ROOT = Path(__file__).parent.parent
FIXTURE = Path(__file__).parent / "fixtures" / "multilingual_smoke_samples.json"


def test_five_language_sample_smoke_runs_without_network(monkeypatch) -> None:
    def blocked_network(*args, **kwargs):
        raise AssertionError("offline sample scoring must not open a network connection")

    monkeypatch.setattr(socket, "create_connection", blocked_network)
    cases = json.loads(FIXTURE.read_text(encoding="utf-8"))

    assert len(cases) >= 5
    assert len({case["language"] for case in cases}) >= 5
    for case in cases:
        result = evaluate_sample_file(ROOT / "data" / "samples" / case["file"])
        assert result["language"] == case["language"]
        assert 0 <= result["score"] <= 100
        assert result["cefr"] in CEFR_BANDS
