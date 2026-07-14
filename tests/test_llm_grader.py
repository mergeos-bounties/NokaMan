from __future__ import annotations

import pytest

from nokaman.models.llm_grader import (
    ENV_API_KEY,
    ENV_MODE,
    GraderClient,
    LiveLLMGraderClient,
    StubGraderClient,
    ToyGraderClient,
    get_grader_client,
)


def _clear_env(monkeypatch):
    monkeypatch.delenv(ENV_MODE, raising=False)
    monkeypatch.delenv(ENV_API_KEY, raising=False)


def test_toy_grader_is_default(monkeypatch):
    _clear_env(monkeypatch)
    client = get_grader_client()
    assert isinstance(client, ToyGraderClient)
    assert isinstance(client, GraderClient)


def test_llm_mode_without_api_key_falls_back_to_stub(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv(ENV_MODE, "llm")
    client = get_grader_client()
    assert isinstance(client, StubGraderClient)


def test_llm_mode_with_api_key_returns_live_client(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv(ENV_MODE, "llm")
    monkeypatch.setenv(ENV_API_KEY, "sk-not-a-real-key")
    client = get_grader_client()
    assert isinstance(client, LiveLLMGraderClient)


def test_stub_grader_shape_and_bounds():
    client = StubGraderClient()
    result = client.score_text("Hello world, this is a short sample sentence.", skill="writing")
    assert set(["language", "skill", "score", "cefr", "model"]).issubset(result.keys())
    assert 0.0 <= result["score"] <= 100.0
    assert result["model"] == "StubLLMGrader"


def test_stub_grader_is_deterministic():
    client = StubGraderClient()
    text = "Repeatable input text for grading."
    first = client.score_text(text, skill="writing")
    second = client.score_text(text, skill="writing")
    assert first["score"] == second["score"]
    assert first["cefr"] == second["cefr"]


def test_toy_grader_matches_interface():
    client = ToyGraderClient()
    result = client.score_text("A reasonably complete sentence for grading.", skill="writing", language="en")
    assert "score" in result and "cefr" in result


def test_live_client_requires_api_key(monkeypatch):
    monkeypatch.delenv(ENV_API_KEY, raising=False)
    with pytest.raises(ValueError):
        LiveLLMGraderClient(api_key=None)


def test_live_client_does_not_require_httpx_at_import_time():
    # Constructing the client (with a key) must not itself require a network call
    # or httpx import - only score_text() does the lazy import.
    client = LiveLLMGraderClient(api_key="sk-test", base_url="https://example-llm.invalid/v1")
    assert client.model  # constructed fine without any network access