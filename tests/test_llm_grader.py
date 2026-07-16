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
    monkeypatch.setenv(ENV_API_KEY, "test-placeholder-not-a-real-credential")
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
    client = LiveLLMGraderClient(api_key="test-placeholder-not-a-real-credential", base_url="https://example-llm.invalid/v1")
    assert client.model  # constructed fine without any network access
"""Tests for optional LLM grader behind flag."""

from __future__ import annotations

import os
from nokaman.eval.llm_grader import LLMGrader


class TestLLMGraderDisabled:
    """Default behaviour — ENABLE_LLM_GRADER is not set."""

    def test_disabled_uses_toy(self) -> None:
        grader = LLMGrader("en")
        result = grader.score_text("I study English every day.")
        assert result["model"] == "ToyAbilityModel"
        assert "llm_fallback_reason" not in result
        assert 0 <= result["score"] <= 100

    def test_disabled_multi_skill(self) -> None:
        grader = LLMGrader("en")
        result = grader.score_multi_skill("I study English.")
        assert result["model"] == "ToyAbilityModel"

    def test_disabled_empty_text(self) -> None:
        grader = LLMGrader("en")
        result = grader.score_text("")
        assert result["model"] == "ToyAbilityModel"
        assert result["score"] >= 0


class TestLLMGraderEnabled:
    """When enabled but no API key — falls back to toy."""

    def test_enabled_no_key_falls_back(self) -> None:
        os.environ["ENABLE_LLM_GRADER"] = "true"
        # Ensure key is not set
        os.environ.pop("LLM_API_KEY", None)
        grader = LLMGrader("en")
        result = grader.score_text("I study English.")
        assert result["model"] == "ToyAbilityModel"
        assert "llm_fallback_reason" in result
        assert "LLM_API_KEY not set" in result["llm_fallback_reason"]
        del os.environ["ENABLE_LLM_GRADER"]

    def test_enabled_empty_text_toy(self) -> None:
        os.environ["ENABLE_LLM_GRADER"] = "true"
        os.environ["LLM_API_KEY"] = "sk-test"
        grader = LLMGrader("en")
        # Empty text should fallback immediately
        result = grader.score_text("")
        assert result["model"] == "ToyAbilityModel"
        del os.environ["ENABLE_LLM_GRADER"]
        del os.environ["LLM_API_KEY"]

    def test_environment_variable_name(self) -> None:
        """Verify the env var name is exactly ENABLE_LLM_GRADER."""
        from nokaman.eval.llm_grader import _is_enabled
        os.environ["ENABLE_LLM_GRADER"] = "true"
        assert _is_enabled() is True
        del os.environ["ENABLE_LLM_GRADER"]
        assert _is_enabled() is False

    def test_enabled_variants(self) -> None:
        from nokaman.eval.llm_grader import _is_enabled
        for val in ("true", "1", "yes", "True", "YES"):
            os.environ["ENABLE_LLM_GRADER"] = val
            assert _is_enabled() is True
            del os.environ["ENABLE_LLM_GRADER"]
