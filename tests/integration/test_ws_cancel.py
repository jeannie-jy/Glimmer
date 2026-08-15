"""Cancellation tests: session.cancel must stop an in-flight turn promptly.

Before the fix, the turn ran inline (`await run_one_turn(...)`) and the
`runner` task was never assigned, so a session.cancel sent while the LLM was
still thinking was only processed AFTER the turn finished — the cancel was a
no-op and the frontend's stop button could not interrupt a long turn.
"""
import asyncio
import time

from fastapi.testclient import TestClient

from harness.llm.mock import MockLLMAdapter
from harness.models import LLMResponse, TokenUsage
from server.main import create_app
from server.ws_handler import configure


class SlowLLMAdapter(MockLLMAdapter):
    """Mock LLM that takes ``delay`` seconds before answering, so the test
    can cancel a turn that is genuinely still running."""

    def __init__(self, responses: list[LLMResponse], delay: float):
        super().__init__(responses)
        self.delay = delay

    async def chat(self, messages, tools, stream=True):
        await asyncio.sleep(self.delay)
        return await super().chat(messages, tools, stream=stream)


def _ok_response(text: str) -> LLMResponse:
    return LLMResponse(
        content=text,
        tool_calls=[],
        stop_reason="complete",
        usage=TokenUsage(input_tokens=0, output_tokens=0, total_tokens=0),
    )


def _make_client(
    workspace, monkeypatch,
    delay: float = 8.0,
    responses: list[LLMResponse] | None = None,
) -> tuple[TestClient, SlowLLMAdapter]:
    """Build a test app wired to a slow mock LLM.

    Returns the client and the adapter the app actually uses, so tests can
    assert on the adapter's recorded call history.
    """
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.chdir(workspace)
    app = create_app(project_root=workspace)
    rs = responses if responses is not None else [_ok_response("All done.")]
    adapter = SlowLLMAdapter(rs, delay=delay)
    configure(app, llm_override=adapter)
    return TestClient(app), adapter


def _receive_until(ws, msg_type: str, max_msgs=60) -> dict:
    for _ in range(max_msgs):
        msg = ws.receive_json()
        if msg.get("type") == msg_type:
            return msg
    raise AssertionError(f"Never received {msg_type!r}")


def test_cancel_stops_inflight_turn_and_session_stays_usable(tmp_path, monkeypatch):
    """Cancelling a turn that is blocked in the LLM stops it in seconds and
    leaves the session loop usable for follow-up messages."""
    client, _ = _make_client(tmp_path, monkeypatch, delay=8.0)
    with client.websocket_connect("/ws/session") as ws:
        ws.send_json({"type": "task.submit", "content": "slow task"})
        # Let the turn start (it blocks inside the mock LLM for 8s)
        time.sleep(0.5)
        started = time.monotonic()
        ws.send_json({"type": "session.cancel"})
        msg = _receive_until(ws, "session.error")
        elapsed = time.monotonic() - started
        assert elapsed < 5.0, f"cancel took {elapsed:.1f}s to stop an in-flight turn"
        assert "cancel" in (msg.get("message") or "").lower(), msg

        # The session loop must remain usable after a cancelled turn
        ws.send_json({"type": "files.list"})
        reply = _receive_until(ws, "files.list")
        assert reply["type"] == "files.list"


def test_resubmit_after_cancelled_subsequent_turn_runs(tmp_path, monkeypatch):
    """A cancelled second turn must not wedge the session: the next submit
    resumes the same session and actually reaches the LLM.

    Root cause regression: cancelling a turn that was running via
    ``continue_turn`` leaves the session stuck in a mid-run state (e.g.
    ``planning``). The old dispatch only handled IDLE/COMPLETED/ERROR and
    silently skipped the resubmit — the follow-up task never reached the LLM.
    """
    client, adapter = _make_client(tmp_path, monkeypatch, delay=2.0, responses=[
        _ok_response("one"),
        _ok_response("two"),
        _ok_response("three"),
    ])
    with client.websocket_connect("/ws/session") as ws:
        ws.send_json({"type": "task.submit", "content": "first task"})
        _receive_until(ws, "session.complete")

        ws.send_json({"type": "task.submit", "content": "second task"})
        time.sleep(0.5)  # the turn is now blocked inside the slow LLM
        ws.send_json({"type": "session.cancel"})
        _receive_until(ws, "session.error")

        # The session is stuck mid-run now. A new submit must still run.
        ws.send_json({"type": "task.submit", "content": "third task"})
        time.sleep(3.0)  # allow the resumed turn to reach and finish the LLM

    # The third task must actually have been handed to the LLM (the second
    # was cancelled during the LLM delay, so it never recorded a call).
    last_user = [
        m for m in adapter.call_history[-1]["messages"]
        if getattr(m, "role", None) == "user"
    ]
    assert last_user and last_user[-1].content == "third task"
