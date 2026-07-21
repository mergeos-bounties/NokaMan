from __future__ import annotations

import os
from typing import Any, Protocol

from nokaman.models.toy import ToyAbilityModel


class AbilityGrader(Protocol):
    """Common grading interface for offline and optional LLM-backed assessors."""

    def score_text(self, text: str, skill: str = "writing") -> dict[str, Any]:
        ...


class ToyAbilityGrader:
    """Default deterministic grader used in CI and offline demos."""

    def __init__(self, language: str = "en"):
        self._model = ToyAbilityModel(language=language)

    def score_text(self, text: str, skill: str = "writing") -> dict[str, Any]:
        return self._model.score_text(text, skill=skill)


class HttpLLMGrader:
    """
    Optional HTTP LLM grader.

    The client follows OpenAI-compatible chat/completions patterns by default,
    but keeps endpoint/model/base URL configurable for SpaceXAI-style gateways.
    """

    def __init__(
        self,
        *,
        language: str = "en",
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        endpoint: str = "/v1/chat/completions",
        timeout: float = 20.0,
        client: Any | None = None,
    ):
        self.language = language.strip().lower()
        self.base_url = (base_url or os.getenv("NOKAMAN_LLM_BASE_URL") or "").rstrip("/")
        self.api_key = api_key if api_key is not None else os.getenv("NOKAMAN_LLM_API_KEY")
        self.model = model or os.getenv("NOKAMAN_LLM_MODEL") or "spacexai"
        self.endpoint = endpoint
        self.timeout = timeout
        self._client = client

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.api_key)

    def score_text(self, text: str, skill: str = "writing") -> dict[str, Any]:
        if not self.configured:
            raise RuntimeError("LLM grader requires NOKAMAN_LLM_BASE_URL and NOKAMAN_LLM_API_KEY")

        import httpx

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a strict language-learning ability grader. "
                        "Return only compact JSON with score, cefr, and feedback."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Language: {self.language}\n"
                        f"Skill: {skill}\n"
                        "Grade this learner response on a 0-100 scale and CEFR band.\n\n"
                        f"{text}"
                    ),
                },
            ],
            "temperature": 0,
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        client = self._client or httpx.Client(timeout=self.timeout)
        close_client = self._client is None
        try:
            response = client.post(f"{self.base_url}{self.endpoint}", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        finally:
            if close_client:
                client.close()

        parsed = _extract_jsonish_grading(data)
        parsed.setdefault("language", self.language)
        parsed.setdefault("skill", skill)
        parsed["model"] = f"HttpLLMGrader:{self.model}"
        return parsed


def build_grader(language: str = "en", kind: str = "toy", **kwargs: Any) -> AbilityGrader:
    key = (kind or "toy").strip().lower()
    if key in {"toy", "offline", "default"}:
        return ToyAbilityGrader(language=language)
    if key in {"llm", "http", "spacexai"}:
        return HttpLLMGrader(language=language, **kwargs)
    raise ValueError(f"unknown grader kind: {kind}")


def _extract_jsonish_grading(data: dict[str, Any]) -> dict[str, Any]:
    if "score" in data:
        return dict(data)

    content = (
        ((data.get("choices") or [{}])[0].get("message") or {}).get("content")
        if isinstance(data.get("choices"), list)
        else None
    )
    if isinstance(content, str):
        import json
        import re

        match = re.search(r"\{.*\}", content, flags=re.S)
        if match:
            return json.loads(match.group(0))

    raise ValueError("LLM grader response did not contain a grading JSON object")
