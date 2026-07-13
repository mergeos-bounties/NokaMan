from __future__ import annotations

import httpx
import pytest

from nokaman.eval.pipeline import evaluate_text
from nokaman.models.grader import HttpLLMGrader, ToyAbilityGrader, build_grader


def test_toy_grader_interface_is_default() -> None:
    result = evaluate_text("en", "I can explain my goals because I practice every day.")

    assert result["model"] == "ToyAbilityModel"
    assert result["language"] == "en"
    assert 0 <= result["score"] <= 100


def test_build_grader_returns_toy_adapter() -> None:
    grader = build_grader("en")

    assert isinstance(grader, ToyAbilityGrader)


def test_http_llm_grader_requires_configuration() -> None:
    grader = HttpLLMGrader(language="en", base_url="", api_key="")

    with pytest.raises(RuntimeError, match="NOKAMAN_LLM_BASE_URL"):
        grader.score_text("hello")


def test_http_llm_grader_parses_openai_compatible_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer test-key"
        body = request.read().decode()
        assert "writing" in body
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": '{"score": 82, "cefr": "B2", "feedback": "clear"}'
                        }
                    }
                ]
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    grader = HttpLLMGrader(
        language="en",
        base_url="https://llm.example.test",
        api_key="test-key",
        model="spacexai-test",
        client=client,
    )

    result = grader.score_text("I can support my opinion with examples.", skill="writing")

    assert result["score"] == 82
    assert result["cefr"] == "B2"
    assert result["language"] == "en"
    assert result["model"] == "HttpLLMGrader:spacexai-test"
