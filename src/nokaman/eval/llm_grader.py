"""Optional remote LLM grader behind a flag.

Default remains the local ToyAbilityModel.
When ENABLE_LLM_GRADER=true and LLM_API_KEY / LLM_ENDPOINT are set,
the remote grader is used instead.

Uses only stdlib (urllib) — no new pip dependencies.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from nokaman.models.toy import ToyAbilityModel

_ENABLED_VAR = "ENABLE_LLM_GRADER"
_API_KEY_VAR = "LLM_API_KEY"
_ENDPOINT_VAR = "LLM_ENDPOINT"
_MODEL_VAR = "LLM_MODEL"

_DEFAULT_ENDPOINT = "https://api.openai.com/v1/chat/completions"
_DEFAULT_MODEL = "gpt-4o-mini"

SYSTEM_PROMPT = """You are a language assessment grader. Score the user's response on a scale of 0-100.

Consider: grammatical accuracy, vocabulary range, coherence, task completion, and complexity.
Respond with ONLY a JSON object:
{
  "score": <0-100>,
  "cefr": "<A1|A2|B1|B2|C1|C2>",
  "feedback": "<1-2 sentence qualitative feedback>"
}"""


def _is_enabled() -> bool:
    return os.environ.get(_ENABLED_VAR, "").strip().lower() in ("true", "1", "yes")


def _api_key() -> str | None:
    return os.environ.get(_API_KEY_VAR) or None


def _endpoint() -> str:
    return (os.environ.get(_ENDPOINT_VAR) or _DEFAULT_ENDPOINT).rstrip("/")


def _model() -> str:
    return os.environ.get(_MODEL_VAR) or _DEFAULT_MODEL


class LLMGrader:
    """Remote LLM-based grader. Falls back to ToyAbilityModel if disabled or on error."""

    def __init__(self, language: str = "en") -> None:
        self.language = language.strip().lower()
        self._toy = ToyAbilityModel(language=self.language)

    def score_text(self, text: str, skill: str = "writing") -> dict[str, Any]:
        if not _is_enabled():
            return self._toy.score_text(text, skill=skill)

        key = _api_key()
        if not key:
            return self._fallback(text, skill, reason="LLM_API_KEY not set")

        try:
            return self._call_llm(text, skill, key)
        except Exception as exc:
            return self._fallback(text, skill, reason=str(exc))

    def score_multi_skill(self, text: str, skills: list[str] | None = None) -> dict[str, Any]:
        if not _is_enabled():
            return self._toy.score_multi_skill(text, skills=skills)
        # For multi-skill, fallback to toy since LLM per-skill calls are expensive
        return self._toy.score_multi_skill(text, skills=skills)

    # ── internal ───────────────────────────────────────────────

    def _call_llm(self, text: str, skill: str, api_key: str) -> dict[str, Any]:
        if not text.strip():
            return self._toy.score_text(text, skill=skill)

        prompt = (
            f"Language: {self.language}\nSkill being assessed: {skill}\nLearner response:\n{text}"
        )
        payload = json.dumps(
            {
                "model": _model(),
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
                "max_tokens": 200,
            }
        ).encode("utf-8")

        req = urllib.request.Request(
            f"{_endpoint()}",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read().decode("utf-8"))

        content = body["choices"][0]["message"]["content"]
        # Parse JSON from response (handle wrapped in markdown fences)
        content_clean = content.strip()
        if content_clean.startswith("```"):
            content_clean = content_clean.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        parsed = json.loads(content_clean)

        score = float(parsed.get("score", 50))
        cefr = str(parsed.get("cefr", "B1")).upper()
        feedback = str(parsed.get("feedback", ""))

        # Ensure valid CEFR
        valid_cefr = {"A1", "A2", "B1", "B2", "C1", "C2"}
        if cefr not in valid_cefr:
            from nokaman.models.cefr import score_to_cefr

            cefr = score_to_cefr(score)

        return {
            "language": self.language,
            "skill": skill,
            "score": round(score, 2),
            "cefr": cefr,
            "feedback": feedback,
            "model": f"LLMGrader({_model()})",
            "features": {"tokens": len(text.split())},
        }

    def _fallback(self, text: str, skill: str, reason: str = "") -> dict[str, Any]:
        result = self._toy.score_text(text, skill=skill)
        result["llm_fallback_reason"] = reason
        return result
