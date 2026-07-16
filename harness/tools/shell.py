"""Shell execution tool (sandboxed)."""
import shlex
import subprocess
import time
from pathlib import Path
from harness.tools.registry import Tool
from harness.models import ToolResult


class ExecuteShellTool(Tool):
    """Execute a shell command in a sandboxed subprocess."""

    def __init__(self, cwd: Path | None = None, timeout: int = 30, docker_mgr=None, container_id=None):
        self._cwd = cwd
        self._timeout = timeout
        self._docker_mgr = docker_mgr
        self._container_id = container_id

    @property
    def name(self) -> str:
        return "execute_shell"

    @property
    def description(self) -> str:
        return "Execute a shell command. Use for running tests, builds, git commands, etc."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The shell command to execute"},
                "cwd": {"type": "string", "description": "Working directory (defaults to project root)"},
            },
            "required": ["command"],
        }

    async def execute(self, arguments: dict) -> ToolResult:
        start = time.time()
        command = arguments["command"]

        # Docker execution path
        if self._docker_mgr and self._container_id:
            result = await self._docker_mgr.exec(self._container_id, command, timeout=self._timeout)
            return ToolResult(
                tool_name="execute_shell",
                exit_code=result.exit_code,
                stdout=result.stdout,
                stderr=result.stderr,
                duration_ms=int((time.time() - start) * 1000),
            )

        cwd = Path(arguments.get("cwd", str(self._cwd or Path.cwd())))

        try:
            proc = subprocess.run(
                shlex.split(command),
                shell=False,
                cwd=str(cwd),
                timeout=self._timeout,
                capture_output=True,
                text=True,
            )
            return ToolResult(
                tool_name="execute_shell",
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                duration_ms=int((time.time() - start) * 1000),
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                tool_name="execute_shell",
                exit_code=-1,
                stderr=f"Command timed out after {self._timeout}s",
                duration_ms=self._timeout * 1000,
            )
        except Exception as e:
            return ToolResult(
                tool_name="execute_shell",
                exit_code=-1,
                stderr=str(e),
                duration_ms=int((time.time() - start) * 1000),
            )


class RunTestsTool(Tool):
    """Run pytest and collect structured results."""

    def __init__(self, cwd: Path | None = None, timeout: int = 60, docker_mgr=None, container_id=None):
        self._cwd = cwd
        self._timeout = timeout
        self._docker_mgr = docker_mgr
        self._container_id = container_id

    @property
    def name(self) -> str:
        return "run_tests"

    @property
    def description(self) -> str:
        return "Run the test suite using pytest and return structured results."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Specific test path (default: tests/)"},
            },
            "required": [],
        }

    async def execute(self, arguments: dict) -> ToolResult:
        import json
        import tempfile
        start = time.time()
        test_path = arguments.get("path", "tests/")

        # Docker execution path
        if self._docker_mgr and self._container_id:
            cmd = f"python -m pytest {test_path} -v 2>&1"
            result = await self._docker_mgr.exec(self._container_id, cmd, timeout=self._timeout)
            return ToolResult(
                tool_name="run_tests",
                exit_code=result.exit_code,
                stdout=result.stdout,
                stderr=result.stderr,
                duration_ms=int((time.time() - start) * 1000),
            )

        cwd = self._cwd or Path.cwd()

        # Use pytest's JSON report for structured output
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            report_path = f.name

        try:
            proc = subprocess.run(
                [
                    "python", "-m", "pytest", test_path,
                    f"--json-report-file={report_path}",
                    "--json-report-summary",
                    "-q",
                ],
                shell=False,
                cwd=str(cwd),
                timeout=self._timeout,
                capture_output=True,
                text=True,
            )
            structured = None
            try:
                with open(report_path) as f:
                    report = json.load(f)
                    summary = report.get("summary", {})
                    failures = []
                    for test in report.get("tests", []):
                        if test.get("outcome") in ("failed", "error"):
                            failures.append({
                                "file": test.get("nodeid", "").split("::")[0],
                                "function": test.get("nodeid", "").split("::")[-1],
                                "line": test.get("lineno"),
                                "message": test.get("call", {}).get("longrepr", ""),
                            })
                    structured = {
                        "passed": summary.get("passed", 0),
                        "failed": summary.get("failed", 0),
                        "errors": summary.get("error", 0),
                        "failures": failures,
                    }
            except Exception:
                pass

            return ToolResult(
                tool_name="run_tests",
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                duration_ms=int((time.time() - start) * 1000),
                structured=structured,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                tool_name="run_tests",
                exit_code=-1,
                stderr=f"Tests timed out after {self._timeout}s",
                duration_ms=self._timeout * 1000,
            )
        except Exception as e:
            return ToolResult(
                tool_name="run_tests",
                exit_code=-1,
                stderr=str(e),
                duration_ms=int((time.time() - start) * 1000),
            )
        finally:
            try:
                Path(report_path).unlink()
            except Exception:
                pass
