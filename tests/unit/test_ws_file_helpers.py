"""Unit tests for the ws_handler file-operation helpers."""
import base64
import shlex
from types import SimpleNamespace

from server.ws_handler import (
    _safe_local_path,
    _list_local_files,
    _upload_local,
    _read_local,
    _delete_local,
    _upload_to_container,
    _delete_from_container,
)


class FakeDockerManager:
    """Records exec commands and returns scripted results."""

    def __init__(self, results: list | None = None):
        self.calls: list[str] = []
        self._results = list(results or [])

    async def exec(self, container_id, cmd, timeout=10):
        self.calls.append(cmd)
        if self._results:
            return self._results.pop(0)
        return SimpleNamespace(exit_code=0, stdout="", stderr="")


# ---- Local helpers ----

def test_safe_local_path_resolves_inside_workspace(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert _safe_local_path("notes/hello.txt") == (tmp_path / "notes" / "hello.txt")


def test_safe_local_path_rejects_traversal(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert _safe_local_path("../outside.txt") is None
    assert _safe_local_path("a/../../outside.txt") is None


def test_safe_local_path_rejects_absolute_paths(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert _safe_local_path("/etc/passwd") is None
    assert _safe_local_path(str(tmp_path.parent / "outside.txt")) is None


def test_local_upload_read_delete_roundtrip(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    b64 = base64.b64encode("payload".encode()).decode()
    assert _upload_local("notes/a.txt", b64) is None
    assert (tmp_path / "notes" / "a.txt").read_text() == "payload"

    content, err = _read_local("notes/a.txt")
    assert err is None
    assert content == "payload"

    assert _delete_local("notes/a.txt") is None
    assert not (tmp_path / "notes" / "a.txt").exists()


def test_local_upload_rejects_traversal(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    outside = tmp_path / "outside.txt"
    outside.write_text("secret")
    b64 = base64.b64encode("pwn".encode()).decode()
    assert _upload_local("../outside.txt", b64) is not None
    assert outside.read_text() == "secret"


def test_list_local_files_skips_vcs_and_tooling_dirs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("[core]")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "x.js").write_text("// x")

    files = _list_local_files()
    names = [f["name"] for f in files]
    assert "src/main.py" in names
    assert ".git/config" not in names
    assert "node_modules/x.js" not in names
    for f in files:
        assert set(f.keys()) == {"name", "size", "modified"}


# ---- Docker helpers ----

def test_upload_to_container_issues_mkdir_and_base64_write():
    docker = FakeDockerManager()
    import asyncio
    err = asyncio.run(_upload_to_container(docker, "cid", "notes/a.txt", "cGF5bG9hZA=="))
    assert err is None
    assert len(docker.calls) == 2
    assert docker.calls[0] == f"mkdir -p {shlex.quote('/workspace/notes')}"
    assert "base64 -d" in docker.calls[1]
    assert f"> {shlex.quote('/workspace/notes/a.txt')}" in docker.calls[1]


def test_upload_to_container_rejects_traversal():
    docker = FakeDockerManager()
    import asyncio
    err = asyncio.run(_upload_to_container(docker, "cid", "../outside.txt", "eA=="))
    assert err is not None
    assert docker.calls == []


def test_upload_to_container_reports_failure():
    docker = FakeDockerManager([SimpleNamespace(exit_code=1, stdout="", stderr="boom")])
    import asyncio
    err = asyncio.run(_upload_to_container(docker, "cid", "a.txt", "eA=="))
    assert err == "boom"


def test_delete_from_container_issues_rm():
    docker = FakeDockerManager()
    import asyncio
    err = asyncio.run(_delete_from_container(docker, "cid", "notes/a.txt"))
    assert err is None
    assert docker.calls == [f"rm -f {shlex.quote('/workspace/notes/a.txt')}"]


def test_delete_from_container_rejects_traversal():
    docker = FakeDockerManager()
    import asyncio
    err = asyncio.run(_delete_from_container(docker, "cid", "../../etc/passwd"))
    assert err is not None
    assert docker.calls == []
