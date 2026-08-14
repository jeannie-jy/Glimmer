"""Code search tool using ripgrep with Python fallback."""
import posixpath
import re
import shlex
import subprocess
import time
from pathlib import Path
from harness.tools.registry import Tool
from harness.models import ToolResult


class SearchCodeTool(Tool):
    def __init__(
        self,
        cwd: Path | None = None,
        timeout: int = 15,
        docker_mgr=None,
        container_id: str | None = None,
    ):
        self._cwd = cwd
        self._timeout = timeout
        # In Docker mode the search must run INSIDE the sandbox container —
        # searching on the host would escape the workspace and also find the
        # host filesystem instead of the agent's.
        self._docker_mgr = docker_mgr
        self._container_id = container_id

    @property
    def name(self) -> str:
        return "search_code"

    @property
    def description(self) -> str:
        return "Search codebase for a pattern using ripgrep (falls back to Python grep)."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Regex pattern to search for"},
                "path": {"type": "string", "description": "Directory to search in (default: project root)"},
                "glob": {"type": "string", "description": "File glob filter (e.g., '*.py')"},
            },
            "required": ["pattern"],
        }

    async def execute(self, arguments: dict) -> ToolResult:
        start = time.time()
        pattern = arguments["pattern"]
        raw_path = arguments.get("path")
        glob_filter = arguments.get("glob")

        if self._docker_mgr is not None and self._container_id:
            return await self._execute_docker(pattern, raw_path, glob_filter, start)

        # ---- Local mode: search inside cwd only ----
        root = (self._cwd or Path.cwd()).resolve()
        if raw_path:
            candidate = Path(raw_path)
            if candidate.is_absolute():
                candidate = candidate.resolve()
            else:
                candidate = (root / candidate).resolve()
        else:
            candidate = root
        if not candidate.is_relative_to(root):
            return ToolResult(
                tool_name="search_code",
                exit_code=1,
                stdout="",
                stderr="Search path is outside the workspace.",
                duration_ms=int((time.time() - start) * 1000),
            )

        # Try ripgrep first
        try:
            cmd = ["rg", "--line-number", "--no-heading", pattern, str(candidate)]
            if glob_filter:
                cmd.extend(["--glob", glob_filter])
            proc = subprocess.run(
                cmd,
                shell=False,
                timeout=self._timeout,
                capture_output=True,
                text=True,
            )
            return ToolResult(
                tool_name="search_code",
                exit_code=proc.returncode if proc.returncode <= 1 else proc.returncode,
                stdout=proc.stdout if proc.stdout else "No matches found.",
                stderr=proc.stderr,
                duration_ms=int((time.time() - start) * 1000),
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            # ripgrep not available or timed out — fall back to Python
            results = []
            for file_path in candidate.rglob("*"):
                if file_path.is_dir():
                    continue
                if glob_filter and not file_path.match(glob_filter):
                    continue
                try:
                    for i, line in enumerate(file_path.read_text(errors="ignore").splitlines(), 1):
                        if re.search(pattern, line):
                            results.append(f"{file_path}:{i}:{line.strip()}")
                except Exception:
                    continue
            output = "\n".join(results[:200]) if results else "No matches found."
            return ToolResult(
                tool_name="search_code",
                exit_code=0,
                stdout=output,
                duration_ms=int((time.time() - start) * 1000),
            )

    async def _execute_docker(self, pattern, raw_path, glob_filter, start) -> ToolResult:
        """Run ripgrep inside the sandbox container, mapped under /workspace."""
        # Absolute-looking paths are mapped UNDER /workspace — they are never
        # searched at their own container location.
        clean = (raw_path or "").lstrip("/")
        if clean.startswith("workspace/"):
            clean = clean[len("workspace/"):]
        safe = posixpath.normpath(posixpath.join("/workspace", clean))
        if not safe.startswith("/workspace/"):
            return ToolResult(
                tool_name="search_code",
                exit_code=1,
                stdout="",
                stderr="Search path is outside the workspace.",
                duration_ms=int((time.time() - start) * 1000),
            )

        cmd = f"rg --line-number --no-heading {shlex.quote(pattern)} {shlex.quote(safe)}"
        if glob_filter:
            cmd += f" --glob {shlex.quote(glob_filter)}"
        result = await self._docker_mgr.exec(self._container_id, cmd, timeout=self._timeout)
        return ToolResult(
            tool_name="search_code",
            exit_code=result.exit_code if result.exit_code <= 1 else result.exit_code,
            stdout=result.stdout if result.stdout else "No matches found.",
            stderr=result.stderr,
            duration_ms=int((time.time() - start) * 1000),
        )
