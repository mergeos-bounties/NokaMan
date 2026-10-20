from __future__ import annotations

import os
from typing import Optional

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

from nokaman.rubrics.registry import load_language_rubric
from nokaman.models.toy import ToyAbilityModel


def _is_enabled() -> bool:
    """Check if LLM grader is enabled via environment variable."""
    val = os.getenv("ENABLE_LLM_GRADER", "").strip().lower()
    return val in ("true", "1", "yes", "on")


class LLMRubricGrader:
    """
    Optional LLM-based rubric grader (httpx extra).
    
    Uses an LLM API to score text against rubric criteria.
    Falls back to heuristic grader if API unavailable.
    
    Requires: pip install httpx
    Set environment variable: ENABLE_LLM_GRADER=true, LLM_API_KEY, LLM_API_URL
    """

    def __init__(
        self,
        language: str = "en",
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        model: str = "gpt-4o-mini",
    ):
        self.language = language.strip().lower()
        self.rubric = load_language_rubric(self.language)
        self.toy_model = ToyAbilityModel(language=self.language)
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.api_url = api_url or os.getenv("LLM_API_URL", "https://api.openai.com/v1/chat/completions")
        self.model = model
        self.enabled = _is_enabled() and HTTPX_AVAILABLE

    def is_available(self) -> bool:
        return self.enabled

    def score_text(self, text: str, skill: str = "writing") -> dict:
        """Score text using LLM against rubric, fallback to Toy model."""
        if not self.enabled or not text.strip():
            result = self.toy_model.score_text(text, skill=skill)
            if self.enabled and not self.api_key:
                result["llm_fallback_reason"] = "LLM_API_KEY not set"
            elif self.enabled and not HTTPX_AVAILABLE:
                result["llm_fallback_reason"] = "httpx not installed"
            return result

        # Enabled but no API key - fallback with reason
        if not self.api_key:
            result = self.toy_model.score_text(text, skill=skill)
            result["llm_fallback_reason"] = "LLM_API_KEY not set"
            return result

        skill_rubric = (self.rubric.get("skills") or {}).get(skill, {})
        criteria = skill_rubric.get("criteria", [])
        band_descriptors = self.rubric.get("bands", [])

        prompt = self._build_prompt(text, skill, criteria, band_descriptors)

        try:
            import httpx
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are an expert language assessor. Score the text against the provided rubric and return ONLY valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.1,
                "max_tokens": 500,
            }
            with httpx.Client(timeout=30.0) as client:
                response = client.post(self.api_url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return self._parse_response(content)
        except Exception as e:
            result = self.toy_model.score_text(text, skill=skill)
            result["llm_fallback_reason"] = f"LLM grading failed: {e}"
            return result

    def score_multi_skill(self, text: str, skills: list[str] | None = None) -> dict:
        """Score multiple skills using LLM or fallback."""
        if not self.enabled or not text.strip():
            return self.toy_model.score_multi_skill(text, skills)
        # For multi-skill, just use toy for now (LLM would need multiple calls)
        return self.toy_model.score_multi_skill(text, skills)

    def _build_prompt(self, text: str, skill: str, criteria: list, bands: list) -> str:
        criteria_text = "\n".join(f"- {c}" for c in criteria) if criteria else "No specific criteria defined."
        bands_text = ", ".join(bands) if bands else "A1, A2, B1, B2, C1, C2"

        return f"""
Language: {self.language}
Skill: {skill}
Bands: {bands_text}
Criteria:
{criteria_text}

Text to assess:
\"\"\"
{text}
\"\"\"

Return a JSON object with:
{{
  "score": 0-100,
  "cefr": "A1|A2|B1|B2|C1|C2",
  "criteria_scores": {{"criterion_name": score_0_100, ...}},
  "feedback": "brief feedback",
  "confidence": 0.0-1.0
}}
"""

    def _parse_response(self, content: str) -> dict:
        import json
        try:
            # Try to extract JSON from response
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(content[start:end])
            else:
                data = json.loads(content)
            # Validate and clamp
            data["score"] = max(0, min(100, float(data.get("score", 0))))
            data["cefr"] = str(data.get("cefr", "A1")).upper()
            data["confidence"] = max(0.0, min(1.0, float(data.get("confidence", 0.5))))
            data["model"] = "LLMRubricGrader"
            return data
        except Exception:
            result = self.toy_model.score_text("", skill="writing")
            result["llm_fallback_reason"] = "Failed to parse LLM response"
            return result


# Backward compatibility alias
LLMGrader = LLMRubricGrader


def create_llm_grader(language: str = "en", **kwargs) -> LLMRubricGrader:
    """Factory function to create LLM grader."""
    return LLMRubricGrader(language=language, **kwargs)