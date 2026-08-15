"""Directory listing tool — local or sandbox-container aware."""
import shlex
import time
from datetime import datetime
from pathlib import Path
from harness.tools.registry import Tool
from harness.models import ToolResult

# Directories never listed: dependency trees and harness internals. Mirrors
# the server's local file-list skip set so agent-visible structure is clean.
SKIP_DIRS = {
    ".git", ".harness", ".claude", "node_modules", "__pycache__", ".venv", "venv",
    "harness", "server", "web", "tests", "docs",
    ".github", ".agents", ".superpowers", ".pytest_cache", "dist", "build",
}

MAX_FILES_IN_STDOUT = 300


class ListFilesTool(Tool):
    def __init__(self, docker_mgr=None, container_id=None, workspace_root: Path | None = None):
        self._docker_mgr = docker_mgr
        self._container_id = container_id
        self._workspace_root = workspace_root

    @property
    def name(self) -> str:
        return "list_files"

    @property
    def description(self) -> str:
        return "List files in a directory of the workspace (bounded depth; excludes dependency/tooling directories). Use before reading files to learn the project structure."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory to list (default: workspace root)"},
                "max_depth": {"type": "integer", "description": "Maximum recursion depth (default: 3, max: 6)"},
            },
            "required": [],
        }

    async def execute(self, arguments: dict) -> ToolResult:
        start = time.time()
        raw_path = arguments.get("path", "")
        max_depth = min(int(arguments.get("max_depth", 3)), 6)

        if self._docker_mgr and self._container_id:
            return await self._execute_docker(raw_path, max_depth, start)

        root = (self._workspace_root or Path.cwd()).resolve()
        target = (root / raw_path).resolve() if raw_path else root
        if not (target == root or target.is_relative_to(root)):
            return ToolResult(tool_name="list_files", exit_code=1, stdout="",
                stderr=f"Path outside workspace: {raw_path}",
                duration_ms=int((time.time() - start) * 1000))
        if not target.is_dir():
            return ToolResult(tool_name="list_files", exit_code=1, stdout="",
                stderr=f"Not a directory: {raw_path}",
                duration_ms=int((time.time() - start) * 1000))

        base_depth = len(target.relative_to(root).parts)
        files = []
        for p in sorted(target.rglob("*")):
            if not p.is_file() or p.is_symlink():
                continue
            rel = p.relative_to(root)
            if any(part in SKIP_DIRS for part in rel.parts):
                continue
            if len(rel.parts) - base_depth > max_depth:
                continue
            st = p.stat()
            files.append({
                "name": rel.as_posix(),
                "size": st.st_size,
                "modified": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%dT%H:%M"),
            })
        return self._render(files, start)

    def _render(self, files, start) -> ToolResult:
        stdout = "\n".join(f["name"] for f in files[:MAX_FILES_IN_STDOUT])
        if len(files) > MAX_FILES_IN_STDOUT:
            stdout += f"\n... ({len(files) - MAX_FILES_IN_STDOUT} more files)"
        if not stdout:
            stdout = "(empty directory)"
        return ToolResult(tool_name="list_files", exit_code=0,
            stdout=stdout, structured={"files": files},
            duration_ms=int((time.time() - start) * 1000))

    async def _execute_docker(self, raw_path, max_depth, start) -> ToolResult:
        clean = (raw_path or "").replace("\\", "/").lstrip("/")
        safe = "/workspace" + (f"/{clean}" if clean else "")
        cmd = f"find {shlex.quote(safe)} -maxdepth {max_depth} -type f -printf '%P\\t%s\\t%TY-%Tm-%TdT%TH:%TM\\n' 2>/dev/null"
        result = await self._docker_mgr.exec(self._container_id, cmd, timeout=10)
        if result.exit_code not in (0, 1):
            return ToolResult(tool_name="list_files", exit_code=1, stdout="",
                stderr=result.stderr or f"find failed on {safe}",
                duration_ms=int((time.time() - start) * 1000))
        files = []
        for line in (result.stdout or "").splitlines():
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            name = f"{clean}/{parts[0]}" if clean else parts[0]
            try:
                size = int(parts[1])
            except ValueError:
                continue
            files.append({"name": name, "size": size, "modified": parts[2]})
        files.sort(key=lambda f: f["name"])
        return self._render(files, start)
