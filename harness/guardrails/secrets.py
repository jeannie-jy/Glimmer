"""Layer 4a: high-confidence secret-pattern detection (zero dependencies).

Only high-confidence patterns are matched — false positives must cost the
user nothing more than a single approve click (ASK_HUMAN), not a blocked
write. Test fixtures with example keys still flow through the guardrail
approve/reject modal, which is exactly the intended UX.
"""
import re

from harness.models import GuardResult, GuardAction

PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"), "private key"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS access key"),
    (re.compile(r"\bghp_[A-Za-z0-9]{36}\b"), "GitHub token"),
    (re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b"), "Anthropic API key"),
    (re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"), "OpenAI-style API key"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{32,}\b"), "JWT"),
]


def _mask(match_text: str) -> str:
    return match_text[:12] + "***" if len(match_text) > 15 else "***"


class SecretScanner:
    """Detect likely secrets in tool arguments."""

    def check(self, text: str) -> GuardResult:
        for pattern, label in PATTERNS:
            m = pattern.search(text or "")
            if m:
                return GuardResult(
                    action=GuardAction.ASK_HUMAN,
                    layer=4,
                    reason=f"Possible {label} in content: {_mask(m.group(0))}",
                )
        return GuardResult(action=GuardAction.ALLOW, layer=4)
