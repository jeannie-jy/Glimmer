"""Code search tool using ripgrep with Python fallback."""
import subprocess
import time
from pathlib import Path
from harness.tools.registry import Tool
from harness.models import ToolResult


class SearchCodeTool(Tool):
    def __init__(self, cwd: Path | None = None, timeout: int = 15):
        self._cwd = cwd
        self._timeout = timeout

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
        import re
        start = time.time()
        pattern = arguments["pattern"]
        search_path = Path(arguments.get("path", str(self._cwd or Path.cwd())))
        glob_filter = arguments.get("glob")

        # Try ripgrep first
        try:
            cmd = ["rg", "--line-number", "--no-heading", pattern, str(search_path)]
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
            for file_path in search_path.rglob("*"):
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
