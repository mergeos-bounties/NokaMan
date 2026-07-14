from __future__ import annotations

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from nokaman.api.app import app

client = TestClient(app)


def test_health() -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert "en" in r.json()["languages"]


def test_assess_text() -> None:
    r = client.post(
        "/assess/text",
        json={"language": "en", "text": "I practice English every morning.", "skill": "writing"},
    )
    assert r.status_code == 200
    assert "cefr" in r.json()


def test_assess_adaptive() -> None:
    r = client.post(
        "/assess/adaptive",
        json={
            "language": "en",
            "answers": ["I study English every day because it helps me travel."],
        },
    )
    assert r.status_code == 200
    payload = r.json()
    assert payload["model"] == "AdaptiveHeuristicSession"
    assert payload["next_prompt"]["language"] == "en"
