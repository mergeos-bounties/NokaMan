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
