"""Integration tests for the full agent loop with MockLLM."""
import pytest
from harness.loop import AgentLoop
from harness.llm.mock import MockLLMAdapter
from harness.tools.registry import ToolRegistry
from harness.tools.shell import ExecuteShellTool
from harness.guardrails.engine import GuardrailEngine
from harness.feedback.analyzer import FeedbackAnalyzer
from harness.feedback.retry_policy import RetryPolicy
from harness.models import LLMResponse, Message, State, ToolCall, ToolDef


@pytest.fixture
def tools():
    registry = ToolRegistry()
    registry.register(ExecuteShellTool())
    return registry


@pytest.fixture
def guardrails(tmp_path):
    return GuardrailEngine(sandbox_root=str(tmp_path))


@pytest.fixture
def analyzer():
    return FeedbackAnalyzer()


@pytest.fixture
def policy():
    return RetryPolicy(max_retries=2)


class TestAgentLoop:
    @pytest.mark.asyncio
    async def test_simple_complete_flow(self, tools, guardrails, analyzer, policy):
        """Agent completes a task in one LLM turn (no tools needed)."""
        mock = MockLLMAdapter([
            LLMResponse(content="Task completed successfully!", stop_reason="complete"),
        ])
        loop = AgentLoop(tools, guardrails, analyzer, policy)

        session = await loop.run("Say hello", mock)

        assert session.state == State.COMPLETED
        assert len(session.messages) >= 3  # system + user + assistant
        assert "Task completed" in session.messages[-1].content

    @pytest.mark.asyncio
    async def test_tool_use_and_recovery_flow(self, tools, guardrails, analyzer, policy):
        """Agent uses a tool, gets feedback, and self-corrects."""
        mock = MockLLMAdapter([
            # Turn 1: LLM wants to run tests
            LLMResponse(
                content="Let me run the tests first.",
                stop_reason="tool_use",
                tool_calls=[ToolCall(id="t1", name="execute_shell", arguments={"command": "python -m pytest tests/ -q"})],
            ),
            # Turn 2: After observing failure, LLM fixes code
            LLMResponse(
                content="I see the test failure. Let me fix it.",
                stop_reason="tool_use",
                tool_calls=[ToolCall(id="t2", name="execute_shell", arguments={"command": "echo 'fix applied'"})],
            ),
            # Turn 3: LLM completes
            LLMResponse(content="The fix is applied and tests should pass now.", stop_reason="complete"),
        ])
        loop = AgentLoop(tools, guardrails, analyzer, policy)

        session = await loop.run("Fix the failing tests", mock)

        assert session.state == State.COMPLETED
        # Should have tool calls in history
        assert len(session.tool_calls) >= 2

    @pytest.mark.asyncio
    async def test_guardrail_intercepts_dangerous_command(self, tools, guardrails, analyzer, policy):
        """Guardrail should block rm -rf / even when LLM tries it."""
        mock = MockLLMAdapter([
            LLMResponse(
                content="",
                stop_reason="tool_use",
                tool_calls=[ToolCall(id="bad1", name="execute_shell", arguments={"command": "rm -rf /"})],
            ),
        ])
        loop = AgentLoop(tools, guardrails, analyzer, policy)

        session = await loop.run("Clean up", mock)

        # Should block, not execute
        assert session.state == State.AWAITING_HUMAN
