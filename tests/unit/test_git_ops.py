"""Unit tests for the read-only git tool."""
import asyncio
import subprocess
from types import SimpleNamespace

from harness.tools.git_ops import GitTool


class FakeDocker:
    def __init__(self):
        self.calls: list[str] = []

    async def exec(self, container_id, cmd, timeout=10):
        self.calls.append(cmd)
        return SimpleNamespace(exit_code=0, stdout="", stderr="")


def test_unknown_subcommand_rejected():
    tool = GitTool()
    result = asyncio.run(tool.execute({"subcommand": "push"}))
    assert result.exit_code == 1
    assert "Unsupported" in result.stderr


def test_status_parses_porcelain(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "a.txt").write_text("x")
    subprocess.run(["git", "add", "a.txt"], cwd=tmp_path, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init"], cwd=tmp_path, check=True)
    (tmp_path / "a.txt").write_text("changed")

    tool = GitTool(cwd=tmp_path)
    result = asyncio.run(tool.execute({"subcommand": "status"}))

    assert result.exit_code == 0
    assert result.structured["branch"] in ("main", "master")
    assert any(c["status"] == "M" and c["path"] == "a.txt" for c in result.structured["changes"])


def test_not_a_repo_returns_clear_error(tmp_path):
    tool = GitTool(cwd=tmp_path)
    result = asyncio.run(tool.execute({"subcommand": "status"}))
    assert result.exit_code == 1
    assert "Not a git repository" in result.stderr


def test_docker_mode_uses_container_git():
    docker = FakeDocker()
    tool = GitTool(docker_mgr=docker, container_id="c1")
    result = asyncio.run(tool.execute({"subcommand": "diff"}))
    assert any(call.startswith("git -C /workspace") for call in docker.calls)
    assert result.exit_code == 0
