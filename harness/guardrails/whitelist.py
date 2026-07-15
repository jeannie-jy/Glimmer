"""Layer 2: Command whitelist."""
from harness.models import GuardResult, GuardAction


DEFAULT_WHITELIST = {
    # File ops
    "ls", "cat", "head", "tail", "find", "grep", "wc",
    # Dev tools
    "python", "python3", "pytest", "pip", "npm", "node", "cargo",
    "git", "docker", "make", "cmake", "npx",
    # System
    "echo", "mkdir", "cp", "mv", "touch", "chmod", "which", "rm", "rmdir",
}


class CommandWhitelist:
    """Only allow commands from a configurable whitelist."""

    def __init__(self, extra: list[str] | None = None):
        self._whitelist = DEFAULT_WHITELIST | set(extra or [])

    def check(self, command: str) -> GuardResult:
        # Extract first token (the executable name)
        tokens = command.strip().split()
        if not tokens:
            return GuardResult(action=GuardAction.ALLOW, layer=2)
        executable = tokens[0]
        if executable in self._whitelist:
            return GuardResult(action=GuardAction.ALLOW, layer=2)
        return GuardResult(
            action=GuardAction.ASK_HUMAN,
            layer=2,
            reason=f"Command '{executable}' is not in the whitelist",
        )
