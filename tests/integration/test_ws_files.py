"""WS file-operation regression tests (files.upload/download/delete/list).

Before the fix, the ws_handler main loop had no files.upload / files.delete
branches at all, and in local mode files.list / files.download never sent a
reply — the FilePanel's upload/delete/download buttons were dead in both
deployment modes.
"""
import base64

from fastapi.testclient import TestClient

from harness.llm.mock import MockLLMAdapter
from harness.models import LLMResponse, TokenUsage
from server.main import create_app
from server.ws_handler import configure


def _ok_response(text: str) -> LLMResponse:
    return LLMResponse(
        content=text,
        tool_calls=[],
        stop_reason="complete",
        usage=TokenUsage(input_tokens=0, output_tokens=0, total_tokens=0),
    )


def _make_client(workspace, monkeypatch) -> TestClient:
    """Local-mode app with a mock LLM so the WS loop can run a turn.

    ``workspace`` is the directory the server's cwd is pointed at — the root
    the local-mode file helpers treat as the agent workspace.
    """
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.chdir(workspace)
    app = create_app(project_root=workspace)
    configure(app, llm_override=MockLLMAdapter([_ok_response("All done.")]))
    return TestClient(app)


def _drain(ws, until_types=("session.complete", "session.error"), max_msgs=80) -> list[dict]:
    """Consume messages until one of until_types arrives (or the WS closes)."""
    seen = []
    for _ in range(max_msgs):
        try:
            msg = ws.receive_json()
        except Exception:
            break
        seen.append(msg)
        if msg.get("type") in until_types:
            break
    return seen


def _receive_until(ws, msg_type: str, max_msgs=80) -> dict:
    """Receive messages until one of the given type arrives."""
    for _ in range(max_msgs):
        msg = ws.receive_json()
        if msg.get("type") == msg_type:
            return msg
    raise AssertionError(f"Never received {msg_type!r}")


def test_local_mode_file_roundtrip_via_ws(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    with client.websocket_connect("/ws/session") as ws:
        ws.send_json({"type": "task.submit", "content": "hello"})
        seen = _drain(ws)
        assert any(m.get("type") in ("session.complete", "session.error") for m in seen), seen

        # Upload writes a real file under the local workspace (server cwd)
        ws.send_json({
            "type": "files.upload",
            "path": "notes/hello.txt",
            "content": base64.b64encode(b"hello file").decode(),
        })
        msg = _receive_until(ws, "file.created")
        assert msg["path"] == "notes/hello.txt"
        assert (tmp_path / "notes" / "hello.txt").read_text() == "hello file"

        # List reports the uploaded file
        ws.send_json({"type": "files.list"})
        msg = _receive_until(ws, "files.list")
        assert any(f["name"] == "notes/hello.txt" for f in msg["files"])

        # Download returns the content
        ws.send_json({"type": "files.download", "path": "notes/hello.txt"})
        msg = _receive_until(ws, "files.content")
        assert msg["content"] == "hello file"
        assert not msg.get("error")

        # Delete removes the file and confirms it
        ws.send_json({"type": "files.delete", "path": "notes/hello.txt"})
        msg = _receive_until(ws, "files.deleted")
        assert msg["path"] == "notes/hello.txt"
        assert not (tmp_path / "notes" / "hello.txt").exists()


def test_upload_path_traversal_rejected(tmp_path, monkeypatch):
    workspace = tmp_path / "ws"
    workspace.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("secret")
    client = _make_client(workspace, monkeypatch)
    with client.websocket_connect("/ws/session") as ws:
        ws.send_json({"type": "task.submit", "content": "hi"})
        _drain(ws)

        ws.send_json({
            "type": "files.upload",
            "path": "../outside.txt",
            "content": base64.b64encode(b"pwn").decode(),
        })
        # Upload must not overwrite the file outside the workspace. The next
        # files.list reply is the first message that follows the (silently
        # rejected) upload, so checking its files proves nothing was written.
        ws.send_json({"type": "files.list"})
        msg = _receive_until(ws, "files.list")
        names = [f["name"] for f in msg["files"]]
        assert "outside.txt" not in names
        assert outside.read_text() == "secret"


def test_delete_and_download_path_traversal_rejected(tmp_path, monkeypatch):
    workspace = tmp_path / "ws"
    workspace.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("secret")
    client = _make_client(workspace, monkeypatch)
    with client.websocket_connect("/ws/session") as ws:
        ws.send_json({"type": "task.submit", "content": "hi"})
        _drain(ws)

        # Download of an escaping path must not leak content
        ws.send_json({"type": "files.download", "path": "../outside.txt"})
        msg = _receive_until(ws, "files.content")
        assert msg.get("error"), msg
        assert msg["content"] != "secret"

        # Delete of an escaping path must not remove the file
        ws.send_json({"type": "files.delete", "path": "../outside.txt"})
        ws.send_json({"type": "files.list"})
        _receive_until(ws, "files.list")
        assert outside.exists()
        assert outside.read_text() == "secret"
