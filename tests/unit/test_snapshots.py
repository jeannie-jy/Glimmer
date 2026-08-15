"""Unit tests for the snapshot store and restore_file tool."""
import asyncio
from types import SimpleNamespace

from harness.tools.snapshots import SnapshotStore, RestoreFileTool, snapshot_key


class FakeDocker:
    def __init__(self):
        self.calls: list[str] = []

    async def exec(self, container_id, cmd, timeout=10):
        self.calls.append(cmd)
        return SimpleNamespace(exit_code=0, stdout="", stderr="")


def test_snapshot_key_rejects_traversal():
    assert snapshot_key("../etc/passwd") is None
    assert snapshot_key("a/../../b") is None
    assert snapshot_key("..") is None
    assert snapshot_key("src/app.py") == "src/app.py"
    assert snapshot_key("/abs/path") == "abs/path"


def test_store_is_a_stack_latest_wins(tmp_path):
    store = SnapshotStore(tmp_path)
    store.save("a.txt", "v1")
    store.save("a.txt", "v2")
    assert store.load("a.txt") == "v2"
    assert store.load("missing.txt") is None


def test_restore_file_local(tmp_path):
    store = SnapshotStore(tmp_path / "snaps")
    store.save("a.txt", "original")
    (tmp_path / "a.txt").write_text("broken")

    tool = RestoreFileTool(workspace_root=tmp_path, snapshots=store)
    result = asyncio.run(tool.execute({"path": "a.txt"}))

    assert result.exit_code == 0
    assert (tmp_path / "a.txt").read_text() == "original"


def test_restore_file_no_snapshot_errors(tmp_path):
    tool = RestoreFileTool(workspace_root=tmp_path, snapshots=SnapshotStore(tmp_path / "s"))
    result = asyncio.run(tool.execute({"path": "a.txt"}))
    assert result.exit_code == 1
    assert "No snapshot" in result.stderr


def test_restore_file_docker_uses_base64_write(tmp_path):
    store = SnapshotStore(tmp_path / "snaps")
    store.save("a.txt", "original")
    docker = FakeDocker()

    tool = RestoreFileTool(docker_mgr=docker, container_id="c1", workspace_root=tmp_path, snapshots=store)
    result = asyncio.run(tool.execute({"path": "a.txt"}))

    assert result.exit_code == 0
    assert any("base64 -d" in c for c in docker.calls)


def test_write_file_snapshots_then_restore(tmp_path):
    from harness.tools.file_ops import WriteFileTool

    (tmp_path / "a.txt").write_text("v1")
    store = SnapshotStore(tmp_path / "snaps")
    writer = WriteFileTool(workspace_root=tmp_path, snapshots=store)
    assert asyncio.run(writer.execute({"path": "a.txt", "content": "v2"})).exit_code == 0
    assert (tmp_path / "a.txt").read_text() == "v2"

    restorer = RestoreFileTool(workspace_root=tmp_path, snapshots=store)
    assert asyncio.run(restorer.execute({"path": "a.txt"})).exit_code == 0
    assert (tmp_path / "a.txt").read_text() == "v1"
