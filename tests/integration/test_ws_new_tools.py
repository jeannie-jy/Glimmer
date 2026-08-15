"""Integration tests: new tools reachable through the WebSocket agent loop."""
from pathlib import Path

from fastapi.testclient import TestClient

from harness.llm.mock import MockLLMAdapter
from harness.models import LLMResponse, ToolCall
from server.main import create_app
from server.ws_handler import configure


def _ok(text: str = "") -> LLMResponse:
    return LLMResponse(content=text, tool_calls=[], stop_reason="complete")


def _tool_use(name: str, arguments: dict) -> LLMResponse:
    return LLMResponse(
        content="", tool_calls=[ToolCall(id=f"tc-{name}", name=name, arguments=arguments)],
        stop_reason="tool_use",
    )


def _make_client(workspace: Path, monkeypatch, responses: list[LLMResponse]) -> TestClient:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("WORKSPACE_ROOT", raising=False)
    monkeypatch.chdir(workspace)
    app = create_app(project_root=workspace)
    configure(app, llm_override=MockLLMAdapter(responses))
    return TestClient(app)


def _receive_until(ws, msg_type: str, max_msgs=60) -> dict:
    for _ in range(max_msgs):
        msg = ws.receive_json()
        if msg.get("type") == msg_type:
            return msg
    raise AssertionError(f"Never received {msg_type!r}")


def test_list_files_via_agent_loop(tmp_path, monkeypatch):
    (tmp_path / "hello.txt").write_text("hi")
    client = _make_client(tmp_path, monkeypatch, [
        _tool_use("list_files", {}),
        _ok("Listed."),
    ])
    with client.websocket_connect("/ws/session") as ws:
        ws.send_json({"type": "task.submit", "content": "List the workspace"})
        result = _receive_until(ws, "tool.result")
        assert result["tool_name"] == "list_files"
        assert result["exit_code"] == 0
        assert "hello.txt" in result["stdout"]
        assert any(f["name"] == "hello.txt" for f in (result.get("structured") or {}).get("files", []))
        _receive_until(ws, "session.complete")


def test_snapshot_and_restore_via_agent_loop(tmp_path, monkeypatch):
    (tmp_path / "x.txt").write_text("v1")
    monkeypatch.setenv("SNAPSHOT_DIR", str(tmp_path / ".snaps"))
    client = _make_client(tmp_path, monkeypatch, [
        _tool_use("write_file", {"path": "x.txt", "content": "v2"}),
        _tool_use("restore_file", {"path": "x.txt"}),
        _ok("Restored."),
    ])
    with client.websocket_connect("/ws/session") as ws:
        ws.send_json({"type": "task.submit", "content": "Overwrite then restore x.txt"})
        _receive_until(ws, "tool.result")  # write_file
        _receive_until(ws, "tool.result")  # restore_file
        _receive_until(ws, "session.complete")
    assert (tmp_path / "x.txt").read_text() == "v1"
    assert list((tmp_path / ".snaps").glob("*"))  # per-session snapshot dir exists
