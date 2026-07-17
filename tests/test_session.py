"""Tests for adaptive quiz session state machine."""

from __future__ import annotations

import pytest
from nokaman.eval.session import SessionManager, SessionState


class TestSessionManager:
    def test_start_creates_active_session(self) -> None:
        mgr = SessionManager("en")
        out = mgr.start()
        assert mgr.state == SessionState.ACTIVE
        assert out["state"] == "active"
        assert out["n_answers"] == 0
        assert out["ability_score"] == 42.0  # A2 default
        assert out["cefr"] == "A2"
        assert out["next_prompt"] is not None
        assert "prompt" in out["next_prompt"]

    def test_start_twice_raises(self) -> None:
        mgr = SessionManager("en")
        mgr.start()
        with pytest.raises(RuntimeError, match="cannot start"):
            mgr.start()

    def test_submit_answer_updates_ability(self) -> None:
        mgr = SessionManager("en")
        mgr.start()
        out = mgr.submit_answer(
            "I study Korean every day because it helps me communicate with more people."
        )
        assert mgr.state == SessionState.ACTIVE
        assert out["n_answers"] == 1
        assert out["ability_score"] > 0
        assert "next_prompt" in out
        assert out["next_prompt"] is not None
        # second answer should move cefr target
        history = mgr.snapshot()["history"]
        assert len(history) == 1
        assert "estimated_score" in history[0]

    def test_submit_before_start_raises(self) -> None:
        mgr = SessionManager("en")
        with pytest.raises(RuntimeError, match="cannot submit answer"):
            mgr.submit_answer("hello")

    def test_end_marks_complete(self) -> None:
        mgr = SessionManager("en")
        mgr.start()
        out = mgr.end()
        assert out["state"] == "complete"
        assert mgr.state == SessionState.COMPLETE

    def test_session_exhausts_prompt_bank(self) -> None:
        """After administering all prompts, session should auto-complete."""
        mgr = SessionManager("en")
        out = mgr.start()
        # en has 6 prompts (A1-C2)
        for i in range(6):
            assert out["next_prompt"] is not None, f"ran out at answer {i}"
            out = mgr.submit_answer(f"This is my test answer number {i} for the adaptive session.")
        # After 6 answers, all prompts administered
        assert mgr.state == SessionState.COMPLETE
        assert out["next_prompt"] is None

    def test_snapshot_returns_current_state(self) -> None:
        mgr = SessionManager("ko")
        mgr.start()
        mgr.submit_answer("한국어를 공부하고 있습니다.")
        snap = mgr.snapshot()
        assert snap["session_id"] == mgr.session_id
        assert snap["language"] == "ko"
        assert snap["n_answers"] == 1
        assert snap["state"] == "active"

    def test_custom_session_id(self) -> None:
        mgr = SessionManager("en", session_id="my-custom-id")
        assert mgr.session_id == "my-custom-id"

    def test_session_start_returns_first_prompt_with_expected_shape(self) -> None:
        mgr = SessionManager("en")
        out = mgr.start()
        np_ = out["next_prompt"]
        assert "id" in np_
        assert "target_score" in np_
        assert "difficulty_cefr" in np_
        assert "prompt" in np_
        assert np_["difficulty_cefr"] == "A2"

    def test_answer_with_bad_text_does_not_crash(self) -> None:
        mgr = SessionManager("en")
        mgr.start()
        out = mgr.submit_answer("")  # empty — should still produce an estimate
        assert out["n_answers"] == 1
        assert "next_prompt" in out
