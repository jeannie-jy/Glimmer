"""Snapshot store + restore tool for write_file overwrite protection.

Snapshots live OUTSIDE the agent-accessible workspace (base dir injected by
the server): ~/.harness/snapshots/{session_id} in-process, or the host-side
WORKSPACE_ROOT/.harness-snapshots/{session_id} in Docker mode (the container
only mounts the user workspace, so it cannot see or tamper with the store).
"""
import base64
import posixpath
import shlex
import time
from pathlib import Path
from harness.tools.registry import Tool
from harness.models import ToolResult


def snapshot_key(path: str) -> str | None:
    """Normalize a tool-supplied path into a safe snapshot-store key.

    Returns None for paths escaping via '..' (the path guardrails reject
    those anyway; the store never trusts them).
    """
    clean = path.replace("\\", "/").lstrip("/")
    if not clean or clean == ".." or clean.startswith("../") or "/../" in clean:
        return None
    return clean


class SnapshotStore:
    """Per-session stack of pre-overwrite file contents."""

    def __init__(self, base_dir: Path):
        self._base = base_dir

    def save(self, path: str, content: str) -> None:
        key = snapshot_key(path)
        if key is None:
            return
        d = self._base / key
        d.mkdir(parents=True, exist_ok=True)
        seq = sum(1 for _ in d.iterdir())
        (d / f"{seq:04d}").write_text(content, encoding="utf-8")

    def load(self, path: str) -> str | None:
        key = snapshot_key(path)
        if key is None:
            return None
        d = self._base / key
        if not d.is_dir():
            return None
        snaps = sorted(d.iterdir())
        if not snaps:
            return None
        return snaps[-1].read_text(encoding="utf-8")


class RestoreFileTool(Tool):
    """Restore a file to its content before the most recent write_file
    overwrite. The snapshot store location is injected by the server and is
    never exposed as a tool parameter."""

    def __init__(self, docker_mgr=None, container_id=None, workspace_root: Path | None = None,
                 snapshots: SnapshotStore | None = None):
        self._docker_mgr = docker_mgr
        self._container_id = container_id
        self._workspace_root = workspace_root
        self._snapshots = snapshots

    @property
    def name(self) -> str:
        return "restore_file"

    @property
    def description(self) -> str:
        return "Restore a file to its content before the most recent write_file overwrite. Use after an unwanted edit."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path of the file to restore"},
            },
            "required": ["path"],
        }

    async def execute(self, arguments: dict) -> ToolResult:
        start = time.time()
        path = arguments["path"]
        if self._snapshots is None:
            return ToolResult(tool_name="restore_file", exit_code=1, stdout="",
                stderr="Snapshots are not enabled for this session",
                duration_ms=int((time.time() - start) * 1000))
        content = self._snapshots.load(path)
        if content is None:
            return ToolResult(tool_name="restore_file", exit_code=1, stdout="",
                stderr=f"No snapshot for: {path}",
                duration_ms=int((time.time() - start) * 1000))

        try:
            if self._docker_mgr and self._container_id:
                from harness.tools.file_ops import _sandbox_path
                spath = _sandbox_path(path)
                parent = posixpath.dirname(spath)
                await self._docker_mgr.exec(self._container_id, f"mkdir -p {shlex.quote(parent)}", timeout=5)
                encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
                result = await self._docker_mgr.exec(self._container_id,
                    f"echo {shlex.quote(encoded)} | base64 -d > {shlex.quote(spath)}", timeout=10)
                if result.exit_code != 0:
                    return ToolResult(tool_name="restore_file", exit_code=1, stdout="",
                        stderr=result.stderr or "Restore failed",
                        duration_ms=int((time.time() - start) * 1000))
            else:
                p = self._workspace_root / path if self._workspace_root else Path(path)
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content, encoding="utf-8")
        except Exception as e:
            return ToolResult(tool_name="restore_file", exit_code=1, stdout="", stderr=str(e),
                duration_ms=int((time.time() - start) * 1000))
        return ToolResult(tool_name="restore_file", exit_code=0,
            stdout=f"Restored {len(content)} bytes to {path}",
            duration_ms=int((time.time() - start) * 1000))
