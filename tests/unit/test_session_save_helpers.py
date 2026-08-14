"""Unit tests for the session-save helpers (ChatGPT-style history persistence).

The helpers decide (a) whether a session is worth persisting — no junk
"Untitled session" rows for conversations that never got a message — and
(b) how a harness session state maps to the status shown in the history
sidebar (running / completed / error).
"""
import pytest

from harness.models import Message, Session, State
from server.ws_handler import _session_has_content, _session_status


class TestSessionStatus:
    @pytest.mark.parametrize(
        ("state", "expected"),
        [
            (State.COMPLETED, "completed"),
            (State.AWAITING_HUMAN, "completed"),
            (State.ERROR, "error"),
            (State.IDLE, "running"),
            (State.PLANNING, "running"),
            (State.EXECUTING, "running"),
            (State.OBSERVING, "running"),
            (State.CORRECTING, "running"),
        ],
    )
    def test_maps_states_to_history_status(self, state, expected):
        assert _session_status(state.value) == expected


class TestSessionHasContent:
    def _session(self, task="", messages=None) -> Session:
        return Session(
            id="00000000-0000-0000-0000-000000000001",
            task=task,
            state=State.IDLE,
            messages=messages or [],
        )

    def test_empty_session_is_not_persisted(self):
        assert _session_has_content(self._session()) is False

    def test_session_with_task_is_persisted(self):
        # The user message is added by the loop during the turn; a submitted
        # task alone already makes the session worth saving (auto-save on
        # submit, before the loop appends the message).
        assert _session_has_content(self._session(task="fix the bug")) is True

    def test_session_with_user_message_is_persisted(self):
        s = self._session(messages=[Message(role="user", content="hello")])
        assert _session_has_content(s) is True

    def test_system_only_messages_do_not_count(self):
        s = self._session(messages=[Message(role="system", content="prompt")])
        assert _session_has_content(s) is False
