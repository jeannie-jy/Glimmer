"""Security tests: search_code must not escape the workspace sandbox."""
import asyncio
from types import SimpleNamespace

from harness.tools.code_search import SearchCodeTool


class FakeDocker:
    def __init__(self):
        self.calls: list[str] = []

    async def exec(self, container_id, cmd, timeout=10):
        self.calls.append(cmd)
        return SimpleNamespace(exit_code=0, stdout="", stderr="")


# ---- Local mode ----

def test_search_local_relative_traversal_rejected(tmp_path, monkeypatch):
    workspace = tmp_path / "ws"
    workspace.mkdir()
    (tmp_path / "secret.txt").write_text("secret-needle")
    monkeypatch.chdir(workspace)

    tool = SearchCodeTool()
    result = asyncio.run(tool.execute({"pattern": "secret-needle", "path": ".."}))
    assert result.exit_code != 0
    assert "outside" in (result.stderr or "").lower()


def test_search_local_absolute_outside_path_rejected(tmp_path, monkeypatch):
    workspace = tmp_path / "ws"
    workspace.mkdir()
    (tmp_path / "secret.txt").write_text("secret-needle")
    monkeypatch.chdir(workspace)

    tool = SearchCodeTool()
    result = asyncio.run(tool.execute({"pattern": "secret-needle", "path": str(tmp_path)}))
    assert result.exit_code != 0


def test_search_local_finds_matches_inside_workspace(tmp_path, monkeypatch):
    workspace = tmp_path / "ws"
    workspace.mkdir()
    (workspace / "code.py").write_text("print('needle-xyz')\n")
    monkeypatch.chdir(workspace)

    tool = SearchCodeTool()
    result = asyncio.run(tool.execute({"pattern": "needle-xyz", "path": "."}))
    assert result.exit_code == 0
    assert "needle-xyz" in result.stdout


# ---- Docker mode ----

def test_search_docker_runs_rg_inside_container():
    fake = FakeDocker()
    tool = SearchCodeTool(docker_mgr=fake, container_id="cid123")
    asyncio.run(tool.execute({"pattern": "needle; touch /tmp/pwn", "path": "src"}))
    assert len(fake.calls) == 1
    assert fake.calls[0].startswith("rg ")
    assert "/workspace/src" in fake.calls[0]
    # A pattern with shell metacharacters must arrive as one quoted argument
    assert "'needle; touch /tmp/pwn'" in fake.calls[0]


def test_search_docker_absolute_path_mapped_into_workspace():
    fake = FakeDocker()
    tool = SearchCodeTool(docker_mgr=fake, container_id="cid123")
    asyncio.run(tool.execute({"pattern": "needle", "path": "/etc"}))
    assert len(fake.calls) == 1
    # Absolute paths must be mapped UNDER /workspace, never searched at
    # their host/container location.
    assert "/workspace/etc" in fake.calls[0]
