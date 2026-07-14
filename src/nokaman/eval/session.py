"""Adaptive quiz session state machine.

Tracks session lifecycle and drives next-item selection based on
running ability estimate.  States:

    - CREATED   fresh, no answers yet
    - ACTIVE    collecting responses, selecting next prompt
    - COMPLETE  session ended (prompt bank exhausted or manual end)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from nokaman.eval.adaptive import (
    CEFR_TARGETS,
    _running_ability,
    estimate_answer_scores,
    select_next_prompt,
    build_prompt_bank,
)
from nokaman.models.cefr import score_to_cefr


class SessionState(Enum):
    CREATED = "created"
    ACTIVE = "active"
    COMPLETE = "complete"


@dataclass
class Session:
    """Mutable session container.  External code calls SessionManager."""

    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    language: str = ""
    language_name: str = ""
    state: SessionState = SessionState.CREATED
    answers: list[dict] = field(default_factory=list)
    administered_ids: set[str] = field(default_factory=set)
    ability_score: float = field(default_factory=lambda: CEFR_TARGETS["A2"])
    cefr_target: str = "A2"
    prompt_bank: list[dict] = field(default_factory=list)
    history: list[dict] = field(default_factory=list)


class SessionManager:
    """Lightweight session state machine.

    One manager per language session.  Pure Python, no external store.
    Swap the store backend later without changing the public API.
    """

    def __init__(self, language: str, session_id: str | None = None) -> None:
        code = language.strip().lower()
        bank = build_prompt_bank(code)
        name = (bank[0]["language"] if bank else code)
        self._session = Session(
            session_id=session_id or uuid.uuid4().hex[:12],
            language=code,
            language_name=name,
            prompt_bank=bank,
        )

    # ── public API ──────────────────────────────────────────────

    @property
    def session_id(self) -> str:
        return self._session.session_id

    @property
    def state(self) -> SessionState:
        return self._session.state

    def snapshot(self) -> dict[str, Any]:
        """Return a serialisable snapshot of the current session."""
        s = self._session
        return {
            "session_id": s.session_id,
            "language": s.language,
            "language_name": s.language_name,
            "state": s.state.value,
            "n_answers": len(s.answers),
            "ability_score": round(s.ability_score, 2),
            "cefr": score_to_cefr(s.ability_score),
            "cefr_target": s.cefr_target,
            "history": list(s.history),
        }

    def start(self) -> dict[str, Any]:
        """Transition CREATED → ACTIVE and return first prompt."""
        if self._session.state != SessionState.CREATED:
            raise RuntimeError(
                f"cannot start session {self._session.session_id} "
                f"in state {self._session.state.value}"
            )
        self._session.state = SessionState.ACTIVE
        self._session.ability_score = CEFR_TARGETS["A2"]
        self._session.cefr_target = "A2"
        return self._next_prompt()

    def submit_answer(self, answer_text: str) -> dict[str, Any]:
        """Store an answer, re-estimate ability, return next prompt or session-end."""
        if self._session.state != SessionState.ACTIVE:
            raise RuntimeError(
                f"cannot submit answer in state {self._session.state.value}"
            )
        estimates = estimate_answer_scores(self._session.language, [answer_text])
        if not estimates:
            raise ValueError("empty estimate from answer")

        # Record the answer
        entry = {
            "answer": answer_text,
            "estimated_score": estimates[0]["score"],
            "estimated_cefr": estimates[0]["cefr"],
        }
        self._session.answers.append(estimates[0])
        self._session.history.append(entry)

        # Recompute running ability
        self._session.ability_score = _running_ability(self._session.answers)
        self._session.cefr_target = score_to_cefr(self._session.ability_score)

        return self._next_prompt()

    def end(self) -> dict[str, Any]:
        """Manually end the session."""
        self._session.state = SessionState.COMPLETE
        return self.snapshot()

    # ── internal helpers ────────────────────────────────────────

    def _next_prompt(self) -> dict[str, Any]:
        """Select the next prompt or mark session complete."""
        s = self._session
        prompt = select_next_prompt(
            ability_score=s.ability_score,
            prompt_bank=s.prompt_bank,
            administered_ids=s.administered_ids,
        )
        if prompt is None:
            s.state = SessionState.COMPLETE
            result = self.snapshot()
            result["next_prompt"] = None
            return result

        s.administered_ids.add(str(prompt["id"]))
        return {
            **self.snapshot(),
            "next_prompt": prompt,
        }
