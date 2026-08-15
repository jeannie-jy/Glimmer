"""Unit tests for the ListFilesTool."""
import asyncio
from types import SimpleNamespace

from harness.tools.list_files import ListFilesTool


class FakeDocker:
    def __init__(self):
        self.calls: list[str] = []

    async def exec(self, container_id, cmd, timeout=10):
        self.calls.append(cmd)
        return SimpleNamespace(exit_code=0, stdout="", stderr="")


def test_lists_files_with_depth_and_skip_dirs(tmp_path):
    (tmp_path / "a.py").write_text("x")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.py").write_text("y")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "junk.js").write_text("z")

    tool = ListFilesTool(workspace_root=tmp_path)
    result = asyncio.run(tool.execute({}))

    assert result.exit_code == 0
    names = [f["name"] for f in result.structured["files"]]
    assert "a.py" in names
    assert "sub/b.py" in names
    assert "node_modules/junk.js" not in names
    assert "sub/b.py" in result.stdout  # LLM sees stdout, not structured


def test_max_depth_bounds_recursion(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "b").mkdir()
    (tmp_path / "a" / "b" / "c.txt").write_text("deep")

    tool = ListFilesTool(workspace_root=tmp_path)
    result = asyncio.run(tool.execute({"max_depth": 1}))

    assert result.exit_code == 0
    assert result.structured["files"] == []


def test_path_traversal_rejected(tmp_path):
    (tmp_path / "ws").mkdir()
    (tmp_path / "secret.txt").write_text("s")
    tool = ListFilesTool(workspace_root=tmp_path / "ws")
    result = asyncio.run(tool.execute({"path": ".."}))

    assert result.exit_code == 1
    assert "outside" in (result.stderr or "").lower()


def test_docker_mode_runs_find(tmp_path):
    docker = FakeDocker()
    tool = ListFilesTool(docker_mgr=docker, container_id="c1", workspace_root=tmp_path)
    result = asyncio.run(tool.execute({"max_depth": 2}))

    assert "find" in docker.calls[0]
    assert "maxdepth" in docker.calls[0]
    assert result.exit_code == 0
