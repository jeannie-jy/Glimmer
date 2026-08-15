"""Guardrail engine — orchestrates three layers of defense."""
from harness.models import ToolCall, GuardResult, GuardAction
from harness.guardrails.path_sandbox import PathSandbox
from harness.guardrails.whitelist import CommandWhitelist
from harness.guardrails.patterns import PatternBlacklist
from harness.netguard import validate_url


class GuardrailEngine:
    """Three-layer safety check for all tool invocations.

    Layer 1: Path sandbox — restricts filesystem access boundaries
    Layer 2: Command whitelist — only known-safe executables
    Layer 3: Pattern blacklist — intercepts dangerous argument patterns
    """

    def __init__(self, sandbox_root: str, whitelist_extra: list[str] | None = None):
        self._path_sandbox = PathSandbox(sandbox_root)
        self._whitelist = CommandWhitelist(extra=whitelist_extra)
        self._patterns = PatternBlacklist()

    def check(self, tool_call: ToolCall) -> GuardResult:
        # Layer 1: Path sandbox for file operations
        if tool_call.name in ("read_file", "write_file"):
            mode = "write" if tool_call.name == "write_file" else "read"
            result = self._path_sandbox.validate(tool_call.arguments.get("path", ""), mode)
            if result.action != GuardAction.ALLOW:
                return result

        # Layer 1 also: Path sandbox for run_tests path
        if tool_call.name == "run_tests":
            test_path = tool_call.arguments.get("path", "tests/") or "tests/"
            result = self._path_sandbox.validate(test_path, "read")
            if result.action != GuardAction.ALLOW:
                return result

        # Layer 1 also: Path sandbox for list_files path
        if tool_call.name == "list_files":
            raw_path = tool_call.arguments.get("path") or ""
            if raw_path:
                result = self._path_sandbox.validate(raw_path, "read")
                if result.action != GuardAction.ALLOW:
                    return result

        # Layer 1 also: Path sandbox for restore_file path
        if tool_call.name == "restore_file":
            result = self._path_sandbox.validate(tool_call.arguments.get("path", ""), "write")
            if result.action != GuardAction.ALLOW:
                return result

        # Layer 1 also: Path sandbox for git repo path
        if tool_call.name == "git":
            raw_path = tool_call.arguments.get("path") or ""
            if raw_path:
                result = self._path_sandbox.validate(raw_path, "read")
                if result.action != GuardAction.ALLOW:
                    return result

        # Layer 4: web_fetch URL must pass the SSRF guard (defense in depth
        # behind the tool's own check)
        if tool_call.name == "web_fetch":
            reason = validate_url(tool_call.arguments.get("url", ""))
            if reason:
                return GuardResult(action=GuardAction.BLOCK, layer=4, reason=reason)

        # Layer 2 & 3: Command safety for shell execution
        if tool_call.name in ("execute_shell", "run_tests"):
            command = tool_call.arguments.get("command", "")
            if tool_call.name == "run_tests" and not command:
                path = tool_call.arguments.get("path", "tests/")
                command = f"python -m pytest {path} -q"
            if command:
                # Layer 2: Whitelist
                result = self._whitelist.check(command)
                if result.action != GuardAction.ALLOW:
                    return result
                # Layer 3: Pattern blacklist
                result = self._patterns.check(command)
                if result.action != GuardAction.ALLOW:
                    return result

        return GuardResult(action=GuardAction.ALLOW, layer=0, reason="All checks passed")
