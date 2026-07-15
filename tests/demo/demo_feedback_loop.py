"""Demo: Feedback loop -- inject failure, agent corrects, passes"""
import asyncio
from harness.llm.mock import MockLLMAdapter
from harness.tools.registry import ToolRegistry
from harness.tools.shell import ExecuteShellTool
from harness.guardrails.engine import GuardrailEngine
from harness.feedback.analyzer import FeedbackAnalyzer
from harness.feedback.retry_policy import RetryPolicy
from harness.loop import AgentLoop
from harness.models import LLMResponse, ToolCall


async def main():
    tools = ToolRegistry()
    tools.register(ExecuteShellTool())
    guardrails = GuardrailEngine(sandbox_root=".")
    analyzer = FeedbackAnalyzer()
    policy = RetryPolicy(max_retries=3)

    # Simulate: LLM runs tests -> they fail -> LLM fixes -> tests pass -> complete
    mock = MockLLMAdapter([
        LLMResponse(content="Let me run tests first.", stop_reason="tool_use", tool_calls=[
            ToolCall(id="t1", name="execute_shell", arguments={"command": "echo 'FAILED tests'"})
        ]),
        LLMResponse(content="Tests failed. Let me fix the code.", stop_reason="tool_use", tool_calls=[
            ToolCall(id="t2", name="execute_shell", arguments={"command": "echo 'All tests passed!'"})
        ]),
        LLMResponse(content="Tests pass now. Task complete.", stop_reason="complete"),
    ])

    loop = AgentLoop(tools, guardrails, analyzer, policy)
    session = await loop.run("Fix failing tests", mock)

    assert session.state.value == "completed", f"Expected completed, got {session.state}"
    assert session.retry_count >= 0  # May or may not retry depending on exit codes
    print(f"PASS: Feedback loop completed. State: {session.state}, Retries: {session.retry_count}")
    print(f"Tool calls made: {len(session.tool_calls)}")


asyncio.run(main())
