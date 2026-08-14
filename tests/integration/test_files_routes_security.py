"""Security regression tests for /api/files endpoints (IDOR + command injection)."""
import shlex
from types import SimpleNamespace

from fastapi.testclient import TestClient

from server.main import create_app
from server.session_registry import register, unregister

LOCAL_USER_ID = "00000000-0000-0000-0000-000000000000"


class FakeDocker:
    def __init__(self):
        self.calls: list[str] = []

    async def exec(self, container_id, cmd, timeout=10):
        self.calls.append(cmd)
        return SimpleNamespace(
            exit_code=0,
            stdout="/workspace/a.txt\t3\t2026-08-14T10:00\n",
            stderr="",
        )


def _client(monkeypatch, tmp_path) -> TestClient:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    return TestClient(create_app(project_root=tmp_path))


def test_files_endpoints_reject_other_users_session(tmp_path, monkeypatch):
    """IDOR: a session registered to another user must not be accessible."""
    fake = FakeDocker()
    register("sess-victim", fake, "cid-1", "victim-user-id")
    try:
        client = _client(monkeypatch, tmp_path)
        resp = client.get("/api/files", params={"session_id": "sess-victim"})
        assert resp.status_code == 403, resp.text

        resp = client.get(
            "/api/files/download",
            params={"session_id": "sess-victim", "path": "a.txt"},
        )
        assert resp.status_code == 403, resp.text
        assert fake.calls == [], "no container commands may run for someone else's session"
    finally:
        unregister("sess-victim")


def test_files_download_quotes_path_against_injection(tmp_path, monkeypatch):
    """The path is passed to `cat` quoted, so shell metacharacters are inert."""
    fake = FakeDocker()
    register("sess-own", fake, "cid-2", LOCAL_USER_ID)
    try:
        client = _client(monkeypatch, tmp_path)
        evil = "a.txt; echo pwn > /tmp/x"
        resp = client.get(
            "/api/files/download",
            params={"session_id": "sess-own", "path": evil},
        )
        assert resp.status_code == 200, resp.text
        # The whole string must be a single quoted argument to cat
        assert fake.calls[0] == f"cat {shlex.quote('/workspace/' + evil)}"
    finally:
        unregister("sess-own")


def test_files_download_rejects_traversal(tmp_path, monkeypatch):
    fake = FakeDocker()
    register("sess-own2", fake, "cid-3", LOCAL_USER_ID)
    try:
        client = _client(monkeypatch, tmp_path)
        resp = client.get(
            "/api/files/download",
            params={"session_id": "sess-own2", "path": "../.env"},
        )
        assert resp.status_code == 400, resp.text
        assert fake.calls == []
    finally:
        unregister("sess-own2")


def test_files_list_own_session_works(tmp_path, monkeypatch):
    fake = FakeDocker()
    register("sess-own3", fake, "cid-4", LOCAL_USER_ID)
    try:
        client = _client(monkeypatch, tmp_path)
        resp = client.get("/api/files", params={"session_id": "sess-own3"})
        assert resp.status_code == 200, resp.text
        assert resp.json()["files"][0]["name"] == "a.txt"
    finally:
        unregister("sess-own3")
