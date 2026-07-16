"""File operation tools — local or sandbox-container aware."""
import shlex
import time
from pathlib import Path
from harness.tools.registry import Tool
from harness.models import ToolResult


def _sandbox_path(path: str) -> str:
    """Ensure a path is under /workspace for sandbox containers."""
    p = Path(path)
    if p.is_absolute():
        return str(p)
    return f"/workspace/{p}"


class ReadFileTool(Tool):
    def __init__(self, docker_mgr=None, container_id=None):
        self._docker_mgr = docker_mgr
        self._container_id = container_id

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
            content = Path(path).read_text(encoding="utf-8")
            lines = content.splitlines()
            if offset > 0: lines = lines[offset - 1:]
            if limit is not None: lines = lines[:limit]
            return ToolResult(tool_name="read_file", exit_code=0, stdout="\n".join(lines),
                duration_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(tool_name="read_file", exit_code=1, stderr=str(e),
                duration_ms=int((time.time() - start) * 1000))


class WriteFileTool(Tool):
    def __init__(self, docker_mgr=None, container_id=None):
        self._docker_mgr = docker_mgr
        self._container_id = container_id

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
                import base64
                parent = str(Path(spath).parent)
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
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return ToolResult(tool_name="write_file", exit_code=0,
                stdout=f"Wrote {len(content)} bytes to {path}",
                duration_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(tool_name="write_file", exit_code=1, stderr=str(e),
                duration_ms=int((time.time() - start) * 1000))
