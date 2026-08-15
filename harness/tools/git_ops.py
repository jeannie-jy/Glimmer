"""Read-only git tool — status / diff / log, sandbox-aware."""
import shlex
import subprocess
import time
from pathlib import Path
from harness.tools.registry import Tool
from harness.models import ToolResult

_READ_ONLY: dict[str, list[str]] = {
    "status": ["status", "--porcelain"],
    "diff": ["diff", "HEAD"],
    "log": ["log", "--oneline", "-n", "20"],
}


class GitTool(Tool):
    """Inspect the workspace git repository (read-only subcommands only)."""

    def __init__(self, docker_mgr=None, container_id=None, cwd: Path | None = None):
        self._docker_mgr = docker_mgr
        self._container_id = container_id
        self._cwd = cwd

    @property
    def name(self) -> str:
        return "git"

    @property
    def description(self) -> str:
        return "Inspect the git repository: status (porcelain), diff (HEAD), or recent log. Read-only — committing stays with execute_shell."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "subcommand": {"type": "string", "enum": ["status", "diff", "log"],
                               "description": "Which read-only git view to produce"},
                "path": {"type": "string", "description": "Repo path (default: workspace root)"},
            },
            "required": ["subcommand"],
        }

    async def execute(self, arguments: dict) -> ToolResult:
        start = time.time()
        sub = arguments.get("subcommand", "")
        if sub not in _READ_ONLY:
            return ToolResult(tool_name="git", exit_code=1, stdout="",
                stderr=f"Unsupported subcommand: {sub}",
                duration_ms=int((time.time() - start) * 1000))
        path = arguments.get("path", "")

        if self._docker_mgr and self._container_id:
            clean = (path or "").replace("\\", "/").lstrip("/")
            repo = "/workspace" + (f"/{clean}" if clean else "")
            cmd = f"git -C {shlex.quote(repo)} {' '.join(_READ_ONLY[sub])}"
            result = await self._docker_mgr.exec(self._container_id, cmd, timeout=30)
            return await self._build_result(sub, result.exit_code, result.stdout, result.stderr, repo, start)

        cwd = (self._cwd or Path.cwd()).resolve()
        repo = str(cwd / path) if path else str(cwd)
        try:
            proc = subprocess.run(
                ["git", "-C", repo] + _READ_ONLY[sub],
                shell=False, timeout=30, capture_output=True, text=True,
            )
        except Exception as e:
            return ToolResult(tool_name="git", exit_code=1, stdout="", stderr=str(e),
                duration_ms=int((time.time() - start) * 1000))
        return await self._build_result(sub, proc.returncode, proc.stdout, proc.stderr, repo, start)

    async def _build_result(self, sub, code, stdout, stderr, repo, start) -> ToolResult:
        if code == 128 and "not a git repository" in stderr:
            return ToolResult(tool_name="git", exit_code=1, stdout="",
                stderr=f"Not a git repository: {repo}",
                duration_ms=int((time.time() - start) * 1000))
        if code not in (0, 1):
            return ToolResult(tool_name="git", exit_code=code, stdout=stdout, stderr=stderr,
                duration_ms=int((time.time() - start) * 1000))

        structured = None
        if sub == "status":
            branch = ""
            try:
                if self._docker_mgr and self._container_id:
                    br = await self._docker_mgr.exec(self._container_id,
                        f"git -C {shlex.quote(repo)} rev-parse --abbrev-ref HEAD", timeout=10)
                    branch = br.stdout.strip() if br.exit_code == 0 else ""
                else:
                    br = subprocess.run(["git", "-C", repo, "rev-parse", "--abbrev-ref", "HEAD"],
                                        shell=False, timeout=10, capture_output=True, text=True)
                    branch = br.stdout.strip() if br.returncode == 0 else ""
            except Exception:
                pass
            changes = []
            for line in (stdout or "").splitlines():
                if len(line) < 4:
                    continue
                changes.append({"status": line[:2].strip() or "??", "path": line[3:]})
            structured = {"branch": branch, "changes": changes}

        return ToolResult(tool_name="git", exit_code=0, stdout=stdout, stderr=stderr,
            structured=structured, duration_ms=int((time.time() - start) * 1000))
