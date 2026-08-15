"""Guardrail engine — orchestrates four layers of defense."""
import re

from harness.models import ToolCall, GuardResult, GuardAction
from harness.guardrails.path_sandbox import PathSandbox
from harness.guardrails.whitelist import CommandWhitelist
from harness.guardrails.patterns import PatternBlacklist
from harness.guardrails.secrets import SecretScanner
from harness.netguard import validate_url

_URL_RE = re.compile(r"https?://[^\s\"'`]+", re.IGNORECASE)


class GuardrailEngine:
    """Four-layer safety check for all tool invocations.

    Layer 1: Path sandbox — restricts filesystem access boundaries
    Layer 2: Command whitelist — only known-safe executables
    Layer 3: Pattern blacklist — intercepts dangerous argument patterns
    Layer 4: Secret scan + egress SSRF — ASK_HUMAN on high-confidence
    credential patterns; hard BLOCK on private/loopback/cloud-metadata
    URLs in shell commands and web_fetch targets
    """

    def __init__(self, sandbox_root: str, whitelist_extra: list[str] | None = None):
        self._path_sandbox = PathSandbox(sandbox_root)
        self._whitelist = CommandWhitelist(extra=whitelist_extra)
        self._patterns = PatternBlacklist()
        self._secrets = SecretScanner()

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

        # Layer 4a: high-confidence secret patterns in written content
        # (ASK_HUMAN — one approve click, not a blocked write). Shell
        # commands are scanned later, inside the command block below, so the
        # egress BLOCK always fires first.
        if tool_call.name == "write_file":
            result = self._secrets.check(str(tool_call.arguments.get("content", "")))
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
                # Layer 4b: egress URLs in the command must pass netguard —
                # private/loopback/cloud-metadata targets are hard-blocked.
                # Checked BEFORE the secret scan and the whitelist: curl etc.
                # are not whitelisted and would otherwise surface as ASK_HUMAN
                # first, and an approve-click on a secret must never mask a
                # hard BLOCK underneath it.
                for m in _URL_RE.finditer(command):
                    reason = validate_url(m.group(0))
                    if reason:
                        return GuardResult(action=GuardAction.BLOCK, layer=4, reason=reason)
                # Layer 4a: secret scan for shell commands — AFTER egress so a
                # BLOCK always wins over an ASK_HUMAN approval.
                if tool_call.name == "execute_shell":
                    result = self._secrets.check(str(command))
                    if result.action != GuardAction.ALLOW:
                        return result
                # Layer 2: Whitelist
                result = self._whitelist.check(command)
                if result.action != GuardAction.ALLOW:
                    return result
                # Layer 3: Pattern blacklist
                result = self._patterns.check(command)
                if result.action != GuardAction.ALLOW:
                    return result

        return GuardResult(action=GuardAction.ALLOW, layer=0, reason="All checks passed")
