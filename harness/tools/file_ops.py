"""File operation tools — local or sandbox-container aware."""
import posixpath
import shlex
import time
from pathlib import Path
from harness.tools.registry import Tool
from harness.models import ToolResult


def _sandbox_path(path: str) -> str:
    """Ensure a path is under /workspace for sandbox containers.

    posix semantics throughout — these paths are resolved against the Linux
    container filesystem regardless of the host platform (on a Windows host,
    ``Path`` would rewrite ``/workspace/x`` into ``\\workspace\\x`` and the
    container would create a literal backslash directory).
    """
    clean = path.replace("\\", "/")
    if clean.startswith("/"):
        return clean
    return f"/workspace/{clean}"


class ReadFileTool(Tool):
    def __init__(self, docker_mgr=None, container_id=None, workspace_root: Path | None = None):
        self._docker_mgr = docker_mgr
        self._container_id = container_id
        # Local mode: resolve relative paths under the workspace root
        # (WORKSPACE_ROOT) when set; otherwise relative to the process cwd.
        self._workspace_root = workspace_root

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return "Read the contents of a file."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file to read"},
                "offset": {"type": "integer", "description": "Line number to start reading from"},
                "limit": {"type": "integer", "description": "Maximum number of lines to read"},
            },
            "required": ["path"],
        }

    async def execute(self, arguments: dict) -> ToolResult:
        start = time.time()
        path = arguments["path"]
        offset = arguments.get("offset", 0)
        limit = arguments.get("limit")

        if self._docker_mgr and self._container_id:
            spath = _sandbox_path(path)
            try:
                result = await self._docker_mgr.exec(self._container_id, f"cat {shlex.quote(spath)}", timeout=10)
                if result.exit_code != 0:
                    return ToolResult(tool_name="read_file", exit_code=1,
                        stderr=result.stderr or f"File not found: {path}",
                        duration_ms=int((time.time() - start) * 1000))
                lines = result.stdout.splitlines()
                if offset > 0: lines = lines[offset - 1:]
                if limit is not None: lines = lines[:limit]
                return ToolResult(tool_name="read_file", exit_code=0, stdout="\n".join(lines),
                    duration_ms=int((time.time() - start) * 1000))
            except Exception as e:
                return ToolResult(tool_name="read_file", exit_code=1, stderr=str(e),
                    duration_ms=int((time.time() - start) * 1000))

        try:
            p = self._workspace_root / path if self._workspace_root else Path(path)
            content = p.read_text(encoding="utf-8")
            lines = content.splitlines()
            if offset > 0: lines = lines[offset - 1:]
            if limit is not None: lines = lines[:limit]
            return ToolResult(tool_name="read_file", exit_code=0, stdout="\n".join(lines),
                duration_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(tool_name="read_file", exit_code=1, stderr=str(e),
                duration_ms=int((time.time() - start) * 1000))


class WriteFileTool(Tool):
    def __init__(self, docker_mgr=None, container_id=None, workspace_root: Path | None = None,
                 snapshots=None):
        self._docker_mgr = docker_mgr
        self._container_id = container_id
        # Local mode: resolve relative paths under the workspace root
        # (WORKSPACE_ROOT) when set; otherwise relative to the process cwd.
        self._workspace_root = workspace_root
        # Pre-overwrite snapshot store (harness.tools.snapshots.SnapshotStore).
        # Duck-typed reference to avoid a circular import.
        self._snapshots = snapshots

    @property
    def name(self) -> str:
        return "write_file"

    @property
    def description(self) -> str:
        return "Create or overwrite a file with new content."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file to write"},
                "content": {"type": "string", "description": "Content to write to the file"},
            },
            "required": ["path", "content"],
        }

    async def execute(self, arguments: dict) -> ToolResult:
        start = time.time()
        path = arguments["path"]
        content = arguments["content"]

        if self._docker_mgr and self._container_id:
            spath = _sandbox_path(path)
            try:
                # Snapshot the current content before overwriting.
                if self._snapshots is not None:
                    prev = await self._docker_mgr.exec(self._container_id, f"cat {shlex.quote(spath)}", timeout=5)
                    if prev.exit_code == 0:
                        self._snapshots.save(path, prev.stdout)
                import base64
                parent = posixpath.dirname(spath)
                await self._docker_mgr.exec(self._container_id, f"mkdir -p {shlex.quote(parent)}", timeout=5)
                encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
                result = await self._docker_mgr.exec(self._container_id,
                    f"echo {shlex.quote(encoded)} | base64 -d > {shlex.quote(spath)}", timeout=10)
                if result.exit_code != 0:
                    return ToolResult(tool_name="write_file", exit_code=1,
                        stderr=result.stderr or "Write failed",
                        duration_ms=int((time.time() - start) * 1000))
                return ToolResult(tool_name="write_file", exit_code=0,
                    stdout=f"Wrote {len(content)} bytes to {spath}",
                    duration_ms=int((time.time() - start) * 1000))
            except Exception as e:
                return ToolResult(tool_name="write_file", exit_code=1, stderr=str(e),
                    duration_ms=int((time.time() - start) * 1000))

        try:
            p = self._workspace_root / path if self._workspace_root else Path(path)
            # Snapshot before overwriting an existing file so restore_file
            # can roll the change back.
            if self._snapshots is not None and p.exists():
                self._snapshots.save(path, p.read_text(encoding="utf-8", errors="replace"))
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return ToolResult(tool_name="write_file", exit_code=0,
                stdout=f"Wrote {len(content)} bytes to {path}",
                duration_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(tool_name="write_file", exit_code=1, stderr=str(e),
                duration_ms=int((time.time() - start) * 1000))
