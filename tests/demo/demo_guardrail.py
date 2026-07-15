"""Demo: Guardrail intercepts rm -rf /"""
from harness.llm.mock import MockLLMAdapter
from harness.tools.registry import ToolRegistry
from harness.tools.shell import ExecuteShellTool
from harness.guardrails.engine import GuardrailEngine
from harness.feedback.analyzer import FeedbackAnalyzer
from harness.feedback.retry_policy import RetryPolicy
from harness.loop import AgentLoop
from harness.models import LLMResponse, ToolCall, GuardAction

# Setup
tools = ToolRegistry()
tools.register(ExecuteShellTool())
guardrails = GuardrailEngine(sandbox_root=".")
analyzer = FeedbackAnalyzer()
policy = RetryPolicy(max_retries=2)

# Mock LLM that tries rm -rf /
mock = MockLLMAdapter([
    LLMResponse(content="Let me clean up.", stop_reason="tool_use", tool_calls=[
        ToolCall(id="bad1", name="execute_shell", arguments={"command": "rm -rf /"})
    ]),
])

# Also test guardrail directly
result = guardrails.check(ToolCall(id="test", name="execute_shell", arguments={"command": "rm -rf /"}))
assert result.action == GuardAction.BLOCK, f"Expected BLOCK, got {result.action}"
print(f"PASS: rm -rf / blocked by Layer {result.layer}: {result.reason}")

# Test path sandbox
from harness.guardrails.path_sandbox import PathSandbox
sandbox = PathSandbox(root="/tmp/test")
result = sandbox.validate("/etc/passwd", "read")
assert result.action == GuardAction.BLOCK
print(f"PASS: /etc/passwd read blocked: {result.reason}")

# Test pattern blacklist
from harness.guardrails.patterns import PatternBlacklist
bl = PatternBlacklist()
result = bl.check("DROP TABLE users")
assert result.action == GuardAction.BLOCK
print(f"PASS: DROP TABLE blocked: {result.reason}")

print("\nAll guardrail demos passed!")
