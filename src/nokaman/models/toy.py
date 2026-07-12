from __future__ import annotations

import re
from collections.abc import Iterable

from nokaman.models.cefr import score_to_cefr
from nokaman.rubrics.registry import SKILLS, load_language_rubric


class ToyAbilityModel:
    """
    Offline demo assessor:
    - writing/text: length, unique tokens, simple complexity heuristics
    - multi-skill demo: blend text features with declared skill hints
    Real models (transformers / LLM graders) replace this via bounties.
    """

    def __init__(self, language: str = "en"):
        self.language = language.strip().lower()
        self.rubric = load_language_rubric(self.language)

    def score_text(self, text: str, skill: str = "writing") -> dict:
        text = (text or "").strip()
        skill = (skill or "writing").strip().lower()
        tokens = _tokenize(text)
        unique = set(tokens)
        n = len(tokens)
        uniq = len(unique)

        # Heuristic feature mix → 0..100
        length_score = min(100.0, n * 2.5)  # ~40 tokens → 100
        diversity = (uniq / n * 100.0) if n else 0.0
        avg_len = (sum(len(t) for t in tokens) / n) if n else 0.0
        complexity = min(100.0, avg_len * 12.0)
        punct = min(20.0, len(re.findall(r"[.!?。！？]", text)) * 5.0)

        # Language-aware soft prior (script density)
        script_bonus = _script_bonus(text, self.language)

        base = 0.35 * length_score + 0.30 * diversity + 0.25 * complexity + 0.10 * punct
        base = min(100.0, base + script_bonus)

        # Skill tilt
        skill_weights = {
            "vocabulary": 0.45 * diversity + 0.55 * base,
            "grammar": 0.40 * complexity + 0.30 * punct + 0.30 * base,
            "reading": base * 0.95,
            "writing": base,
            "listening": base * 0.9,
            "speaking": 0.5 * diversity + 0.5 * base,
        }
        skill_score = float(skill_weights.get(skill, base))
        skill_score = max(0.0, min(100.0, skill_score))

        return {
            "language": self.language,
            "skill": skill,
            "score": round(skill_score, 2),
            "cefr": score_to_cefr(skill_score),
            "features": {
                "tokens": n,
                "unique_tokens": uniq,
                "avg_token_len": round(avg_len, 3),
                "script_bonus": round(script_bonus, 2),
            },
            "model": "ToyAbilityModel",
        }

    def score_multi_skill(self, text: str, skills: Iterable[str] | None = None) -> dict:
        skill_list = list(skills) if skills else list(SKILLS)
        skill_scores = {}
        for skill in skill_list:
            skill_scores[skill] = self.score_text(text, skill=skill)["score"]
        weights = {}
        for skill in skill_list:
            w = float((self.rubric.get("skills") or {}).get(skill, {}).get("weight", 1.0))
            weights[skill] = w
        total_w = sum(weights.values()) or 1.0
        overall = sum(skill_scores[s] * weights[s] for s in skill_list) / total_w
        return {
            "language": self.language,
            "skills": {k: round(v, 2) for k, v in skill_scores.items()},
            "overall": round(overall, 2),
            "cefr": score_to_cefr(overall),
            "model": "ToyAbilityModel",
        }


def _tokenize(text: str) -> list[str]:
    # Word-ish tokens + CJK characters as units
    parts = re.findall(r"[\w']+|[一-龥ぁ-ゖァ-ヺ가-힣]", text, flags=re.UNICODE)
    return [p.lower() for p in parts if p.strip()]


def _script_bonus(text: str, language: str) -> float:
    if not text:
        return 0.0
    if language == "ko" and re.search(r"[가-힣]", text):
        return 8.0
    if language == "ja" and re.search(r"[ぁ-ゖァ-ヺ一-龥]", text):
        return 8.0
    if language == "zh" and re.search(r"[一-龥]", text):
        return 8.0
    if language == "en" and re.search(r"[A-Za-z]", text):
        return 4.0
    if language == "vi" and re.search(r"[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]", text, re.I):
        return 6.0
    return 0.0
