"""Main feedback analyzer — strategy dispatch based on tool type."""
import re
from pathlib import Path
from harness.models import ToolResult, Feedback, Verdict, Failure
from harness.feedback.pytest_parser import parse_pytest_structured


class FeedbackAnalyzer:
    """Deterministic analyzer that converts tool results into Feedback signals.

    This is NOT a prompt-based analysis. Every verdict is computed by code:
    exit codes, structured test reports, and file existence checks.
    Remove the LLM and this still produces correct verdicts for testing.
    """

    def analyze(self, result: ToolResult) -> Feedback:
        # Dispatch by tool type
        if result.tool_name == "run_tests":
            return self._analyze_test_results(result)
        elif result.tool_name == "execute_shell":
            return self._analyze_shell(result)
        elif result.tool_name == "write_file":
            return self._analyze_write(result)
        else:
            # read_file, search_code — no objective signal
            return Feedback(
                verdict=Verdict.UNKNOWN,
                summary=f"No objective feedback available for {result.tool_name}",
            )

    def _analyze_test_results(self, result: ToolResult) -> Feedback:
        if result.exit_code == 0:
            return Feedback(verdict=Verdict.PASS, summary=result.stdout[:500])

        failures: list[Failure] = []
        if result.structured:
            failures = parse_pytest_structured(result.structured)

        summary = f"{len(failures)} test(s) failed" if failures else result.stderr[:500] or result.stdout[:500]

        suggested_fix = self._build_suggested_fix(failures, result)

        return Feedback(
            verdict=Verdict.FAIL,
            failures=failures,
            summary=summary,
            suggested_fix=suggested_fix,
        )

    def _analyze_shell(self, result: ToolResult) -> Feedback:
        if result.exit_code == 0:
            return Feedback(verdict=Verdict.PASS, summary=result.stdout[:500])
        return Feedback(
            verdict=Verdict.FAIL,
            summary=result.stderr[:500] or f"Command failed with exit code {result.exit_code}",
            failures=[Failure(file="shell", message=result.stderr[:200])],
        )

    def _analyze_write(self, result: ToolResult) -> Feedback:
        if result.exit_code == 0:
            summary = result.stdout
            # Syntax check for .py files
            for match in re.finditer(r'(\S+\.py)\b', result.stdout or "", re.IGNORECASE):
                py_path = match.group(1)
                try:
                    p = Path(py_path)
                    if p.exists():
                        source = p.read_text(encoding="utf-8")
                        compile(source, str(p), "exec")
                except SyntaxError as e:
                    return Feedback(
                        verdict=Verdict.FAIL,
                        summary=f"Syntax error in {py_path}: {e}",
                        failures=[Failure(file=py_path, message=str(e))],
                    )
                except Exception:
                    pass  # file may not exist yet or other transient errors
            return Feedback(verdict=Verdict.PASS, summary=summary)
        return Feedback(
            verdict=Verdict.FAIL,
            summary=result.stderr or "File write failed",
        )

    @staticmethod
    def _build_suggested_fix(failures: list[Failure], result: ToolResult) -> str:
        if not failures:
            return result.stderr[:500] if result.stderr else "Investigate the failure and fix the issue."
        lines = ["The following tests failed. Please fix the code to make them pass:\n"]
        for f in failures:
            loc = f"{f.file}:{f.line}" if f.line else f.file
            lines.append(f"- {f.function} ({loc}): {f.message[:120]}")
        return "\n".join(lines)
