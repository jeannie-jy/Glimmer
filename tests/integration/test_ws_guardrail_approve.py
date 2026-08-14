"""Integration tests for the guardrail approve/reject flow over WebSocket.

While a turn awaits a human decision the pump forwards ``guardrail.approve`` /
``guardrail.reject`` to the in-flight runner; both must resume the loop, emit
a ``state.change`` leaving ``awaiting_human`` (the frontend uses this to
dismiss the modal), and complete the session.
"""

from starlette.testclient import TestClient

from harness.llm.mock import MockLLMAdapter
from harness.models import LLMResponse, ToolCall
from server.main import create_app
from server.ws_handler import configure


def _make_app(tmp_path, responses):
    app = create_app(project_root=tmp_path)
    configure(app, llm_override=MockLLMAdapter(responses))
    return app


def _recv_until(ws, wanted: str, limit: int = 60) -> dict:
    for _ in range(limit):
        msg = ws.receive_json()
        if msg.get("type") == wanted:
            return msg
        if msg.get("type") == "session.error":
            raise AssertionError(f"session.error: {msg.get('message')}")
    raise AssertionError(f"never received {wanted}")


def _scripted_responses():
    """First response asks for a non-whitelisted command (ASK_HUMAN trigger);
    approving runs it harmlessly (command does not exist) and the loop moves
    to the scripted final response."""
    return [
        LLMResponse(
            content="",
            tool_calls=[
                ToolCall(
                    id="t1",
                    name="execute_shell",
                    arguments={"command": "mysterycmd --check"},
                )
            ],
            stop_reason="tool_use",
        ),
        LLMResponse(content="done", tool_calls=[], stop_reason="complete"),
    ]


def test_approve_resumes_turn_and_completes(tmp_path):
    app = _make_app(tmp_path, _scripted_responses())
    with TestClient(app).websocket_connect("/ws/session?token=local") as ws:
        ws.send_json({"type": "task.submit", "content": "trigger guardrail"})

        pending = _recv_until(ws, "guardrail.pending")
        assert pending.get("action") == "ask_human"
        assert "mysterycmd" in pending.get("reason", "")

        ws.send_json({"type": "guardrail.approve"})

        # Approval resumes the loop: the next state.change must land somewhere
        # other than awaiting_human (the signal the frontend uses to dismiss
        # the modal — approve_pending advances the state to observing first,
        # so the emitted change carries from=observing, not from=awaiting_human).
        leaving = _recv_until(ws, "state.change")
        assert leaving.get("to") != "awaiting_human"
        _recv_until(ws, "session.complete")


def test_reject_resumes_turn_and_completes(tmp_path):
    app = _make_app(tmp_path, _scripted_responses())
    with TestClient(app).websocket_connect("/ws/session?token=local") as ws:
        ws.send_json({"type": "task.submit", "content": "trigger guardrail"})

        pending = _recv_until(ws, "guardrail.pending")
        assert pending.get("action") == "ask_human"

        ws.send_json({"type": "guardrail.reject"})

        leaving = _recv_until(ws, "state.change")
        assert leaving.get("to") != "awaiting_human"
        _recv_until(ws, "session.complete")
