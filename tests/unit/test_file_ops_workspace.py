"""Unit tests for workspace_root support in the file tools (local mode).

On deployed servers without a Docker socket, agent file operations must
target WORKSPACE_ROOT instead of the application source directory — this is
what keeps the Files panel and the agent's read/write tools consistent.
"""
import asyncio
from pathlib import Path

from harness.tools.file_ops import ReadFileTool, WriteFileTool


def test_write_file_under_workspace_root(tmp_path):
    ws = tmp_path / "workspace"
    tool = WriteFileTool(workspace_root=ws)
    result = asyncio.run(tool.execute({"path": "notes/a.txt", "content": "hi"}))
    assert result.exit_code == 0
    assert (ws / "notes" / "a.txt").read_text(encoding="utf-8") == "hi"
    assert not (tmp_path / "notes").exists()


def test_read_file_under_workspace_root(tmp_path):
    ws = tmp_path / "workspace"
    ws.mkdir()
    (ws / "b.py").write_text("x = 1", encoding="utf-8")
    tool = ReadFileTool(workspace_root=ws)
    result = asyncio.run(tool.execute({"path": "b.py"}))
    assert result.exit_code == 0
    assert result.stdout == "x = 1"


def test_file_tools_default_to_cwd_without_workspace_root(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tool = WriteFileTool()
    result = asyncio.run(tool.execute({"path": "here.txt", "content": "v"}))
    assert result.exit_code == 0
    assert (tmp_path / "here.txt").read_text(encoding="utf-8") == "v"


def test_file_tools_ignore_workspace_root_in_docker_mode(tmp_path):
    """docker_mgr set means the container path is used — workspace_root must
    not leak into the container-executed command."""
    class FakeDocker:
        def __init__(self):
            self.calls = []
        async def exec(self, cid, cmd, timeout=10):
            self.calls.append(cmd)
            from types import SimpleNamespace
            return SimpleNamespace(exit_code=0, stdout="ok", stderr="")

    docker = FakeDocker()
    ws = tmp_path / "workspace"
    tool = WriteFileTool(docker_mgr=docker, container_id="cid", workspace_root=ws)
    result = asyncio.run(tool.execute({"path": "notes/a.txt", "content": "hi"}))
    assert result.exit_code == 0
    assert len(docker.calls) == 2  # mkdir + base64 write
    assert docker.calls[0] == "mkdir -p /workspace/notes"
    assert not (ws / "notes").exists()
