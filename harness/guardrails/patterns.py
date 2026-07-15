"""Layer 3: Regex pattern blacklist for dangerous command arguments."""
import re
from harness.models import GuardResult, GuardAction


DANGEROUS_PATTERNS: list[tuple[str, GuardAction, str]] = [
    (r"rm\s+-rf\s+/", GuardAction.BLOCK, "Recursive delete of root directory"),
    (r"rm\s+-rf\s+~", GuardAction.BLOCK, "Recursive delete of home directory"),
    (r"DROP\s+(TABLE|DATABASE)", GuardAction.BLOCK, "Database destructive operation"),
    (r"TRUNCATE\s+(TABLE|DATABASE)", GuardAction.BLOCK, "Database destructive operation"),
    (r"git\s+push\s+--force.*origin.*main", GuardAction.ASK_HUMAN, "Force push to main branch"),
    (r"git\s+push\s+--force.*origin.*master", GuardAction.ASK_HUMAN, "Force push to master branch"),
    (r"curl.*\|.*(bash|sh|python)", GuardAction.ASK_HUMAN, "Pipe remote script to interpreter"),
    (r"wget.*\|.*(bash|sh)", GuardAction.ASK_HUMAN, "Pipe remote script to interpreter"),
    (r"chmod\s+777\s+/", GuardAction.ASK_HUMAN, "World-writable permissions on root path"),
    (r"dd\s+if=", GuardAction.ASK_HUMAN, "Low-level disk operation"),
    (r">\s*/dev/sd", GuardAction.BLOCK, "Direct disk write"),
]


class PatternBlacklist:
    """Regex-based dangerous command pattern detection.

    Note: This layer is a best-effort defense. Encoding, base64 obfuscation,
    and indirect execution can bypass regex matching. For production, pair
    with seccomp/AppArmor sandboxing.
    """

    def __init__(self, extra_patterns: list[tuple[str, GuardAction, str]] | None = None):
        self._patterns = list(DANGEROUS_PATTERNS)
        if extra_patterns:
            self._patterns.extend(extra_patterns)

    def check(self, command: str) -> GuardResult:
        for pattern, action, reason in self._patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return GuardResult(action=action, layer=3, reason=reason)
        return GuardResult(action=GuardAction.ALLOW, layer=3)
