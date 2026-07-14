from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from typing import Any

from nokaman.models.cefr import score_to_cefr
from nokaman.models.toy import ToyAbilityModel

# Env vars (no secrets committed; values only ever come from the environment)
ENV_MODE = "NOKAMAN_GRADER"  # "toy" (default) | "llm"
ENV_BASE_URL = "NOKAMAN_GRADER_BASE_URL"  # OpenAI-compatible base URL (SpaceXAI etc.)
ENV_API_KEY = "NOKAMAN_GRADER_API_KEY"
ENV_MODEL = "NOKAMAN_GRADER_MODEL"

DEFAULT_MODEL = "gpt-4o-mini"

RUBRIC_PROMPT = """You are an expert language examiner. Score the learner's text on a 0-100 scale \
for the skill "{skill}" using a CEFR-aligned rubric. Respond ONLY with compact JSON of the form \
{{"score": <0-100 number>, "rationale": "<short reason>"}}. No prose, no markdown fences.

Text:
{text}
"""


class GraderClient(ABC):
    """Common interface every rubric grader (toy, stub, live) must implement."""

    name: str = "GraderClient"

    @abstractmethod
    def score_text(self, text: str, skill: str = "writing", language: str = "en") -> dict[str, Any]:
        """Return a dict with at least: score, cefr, skill, language, model."""
        raise NotImplementedError


class ToyGraderClient(GraderClient):
    """Wraps the existing offline heuristic model behind the grader interface."""

    name = "ToyAbilityModel"

    def score_text(self, text: str, skill: str = "writing", language: str = "en") -> dict[str, Any]:
        model = ToyAbilityModel(language=language)
        return model.score_text(text, skill=skill)


class StubGraderClient(GraderClient):
    """
    Deterministic, network-free grader used in tests/CI when no API key is configured.
    Produces stable, reasonable scores derived only from text length so behavior
    is fully predictable without ever calling an LLM.
    """

    name = "StubLLMGrader"

    def score_text(self, text: str, skill: str = "writing", language: str = "en") -> dict[str, Any]:
        text = (text or "").strip()
        n_chars = len(text)
        # Deterministic, bounded pseudo-score - no network, no randomness.
        score = max(0.0, min(100.0, 20.0 + n_chars * 0.6))
        return {
            "language": language,
            "skill": skill,
            "score": round(score, 2),
            "cefr": score_to_cefr(score),
            "rationale": "stub grader: deterministic length-based placeholder score",
            "model": self.name,
        }


class LiveLLMGraderClient(GraderClient):
    """
    Calls an OpenAI-compatible /chat/completions endpoint (works with SpaceXAI and
    similar configurable-base-URL providers) to grade text against a CEFR rubric.
    httpx is imported lazily so the base install never requires it; install with
    `pip install -e ".[llm]"` to use this client.
    """

    name = "LiveLLMGrader"

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = (base_url or os.getenv(ENV_BASE_URL, "https://api.openai.com/v1")).rstrip("/")
        self.api_key = api_key or os.getenv(ENV_API_KEY)
        self.model = model or os.getenv(ENV_MODEL, DEFAULT_MODEL)
        self.timeout = timeout
        if not self.api_key:
            raise ValueError(
                f"{ENV_API_KEY} is not set; cannot construct LiveLLMGraderClient. "
                "Use StubGraderClient or ToyGraderClient instead."
            )

    def score_text(self, text: str, skill: str = "writing", language: str = "en") -> dict[str, Any]:
        try:
            import httpx
        except ImportError as exc:  # pragma: no cover - exercised only without extra installed
            raise ImportError(
                'httpx is required for LiveLLMGraderClient. Install with: pip install -e ".[llm]"'
            ) from exc

        prompt = RUBRIC_PROMPT.format(skill=skill, text=text)
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        content = data["choices"][0]["message"]["content"].strip()
        content = content.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        parsed = json.loads(content)
        score = max(0.0, min(100.0, float(parsed["score"])))
        return {
            "language": language,
            "skill": skill,
            "score": round(score, 2),
            "cefr": score_to_cefr(score),
            "rationale": parsed.get("rationale", ""),
            "model": f"{self.name}:{self.model}",
        }


def get_grader_client() -> GraderClient:
    """
    Factory selecting the active grader:
    - default ("toy" or unset): ToyGraderClient — no config needed, always available.
    - "llm": LiveLLMGraderClient if an API key is configured, otherwise falls back to
      StubGraderClient so CI stays green with no secrets present.
    """
    mode = os.getenv(ENV_MODE, "toy").strip().lower()
    if mode != "llm":
        return ToyGraderClient()
    if os.getenv(ENV_API_KEY):
        return LiveLLMGraderClient()
    return StubGraderClient()