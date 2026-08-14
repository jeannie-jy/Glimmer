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


def _make_client(workspace, monkeypatch, delay: float = 8.0) -> TestClient:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.chdir(workspace)
    app = create_app(project_root=workspace)
    configure(app, llm_override=SlowLLMAdapter([_ok_response("All done.")], delay=delay))
    return TestClient(app)


def _receive_until(ws, msg_type: str, max_msgs=60) -> dict:
    for _ in range(max_msgs):
        msg = ws.receive_json()
        if msg.get("type") == msg_type:
            return msg
    raise AssertionError(f"Never received {msg_type!r}")


def test_cancel_stops_inflight_turn_and_session_stays_usable(tmp_path, monkeypatch):
    """Cancelling a turn that is blocked in the LLM stops it in seconds and
    leaves the session loop usable for follow-up messages."""
    client = _make_client(tmp_path, monkeypatch, delay=8.0)
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
