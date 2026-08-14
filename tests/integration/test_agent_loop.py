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

    @pytest.mark.asyncio
    async def test_batch_tool_calls(self, tools, guardrails, analyzer, policy):
        """Agent processes multiple tool calls from a single LLM response."""
        mock = MockLLMAdapter([
            LLMResponse(
                content="Let me run both commands.",
                stop_reason="tool_use",
                tool_calls=[
                    ToolCall(id="t1", name="execute_shell", arguments={"command": "echo first"}),
                    ToolCall(id="t2", name="execute_shell", arguments={"command": "echo second"}),
                ],
            ),
            LLMResponse(content="Both commands completed.", stop_reason="complete"),
        ])
        loop = AgentLoop(tools, guardrails, analyzer, policy)

        session = await loop.run("Run two commands", mock)

        assert session.state == State.COMPLETED
        assert len(session.tool_calls) == 2, f"Expected 2 tool calls, got {len(session.tool_calls)}"
        assert session.tool_calls[0].id == "t1"
        assert session.tool_calls[1].id == "t2"

    @pytest.mark.asyncio
    async def test_resume_after_approval(self, tools, guardrails, analyzer, policy):
        """run() pauses at AWAITING_HUMAN, resume() after approve completes."""
        mock = MockLLMAdapter([
            LLMResponse(
                content="Let me run a command.",
                stop_reason="tool_use",
                tool_calls=[ToolCall(
                    id="t1", name="execute_shell",
                    arguments={"command": "nonexistent_tool_xyz"},
                )],
            ),
            # After resume and approval, LLM sees the result and completes
            LLMResponse(content="Command executed. Done.", stop_reason="complete"),
        ])
        loop = AgentLoop(tools, guardrails, analyzer, policy)

        session = await loop.run("Run a command", mock)

        # Guardrail flags unknown command -> AWAITING_HUMAN
        assert session.state == State.AWAITING_HUMAN, f"Expected AWAITING_HUMAN, got {session.state}"
        assert session._pending_approval is not None, "Expected a pending approval"

        # Approve the pending tool
        session = loop.approve_pending(session)
        assert session.state == State.OBSERVING

        # Resume the loop — tool will be dispatched (may fail, but gets a result)
        session = await loop.resume(session, mock)
        assert session.state == State.COMPLETED
        assert len(session.tool_calls) >= 1

    @pytest.mark.asyncio
    async def test_blocked_tool_message_reaches_llm_on_resume(self, tools, guardrails, analyzer, policy):
        """After a guardrail BLOCK + approve, the BLOCKED tool message must stay
        in the LLM context so the assistant tool_use keeps its tool_result pair."""
        mock = MockLLMAdapter([
            LLMResponse(
                content="",
                stop_reason="tool_use",
                tool_calls=[ToolCall(
                    id="bad1", name="execute_shell",
                    arguments={"command": "rm -rf /"},
                )],
            ),
            LLMResponse(content="Understood, I will not do that.", stop_reason="complete"),
        ])
        loop = AgentLoop(tools, guardrails, analyzer, policy)

        session = await loop.run("Clean up", mock)
        assert session.state == State.AWAITING_HUMAN

        session = loop.approve_pending(session)
        session = await loop.resume(session, mock)
        assert session.state == State.COMPLETED

        second_call_messages = mock.call_history[1]["messages"]
        blocked = [m for m in second_call_messages if m.role == "tool" and m.content.startswith("BLOCKED")]
        assert blocked, "BLOCKED tool message must be passed to the LLM to pair with its tool_use"
        assert blocked[0].tool_call_id == "bad1"

    @pytest.mark.asyncio
    async def test_rejected_tool_message_reaches_llm_on_resume(self, tools, guardrails, analyzer, policy):
        """After a guardrail REJECT, the Rejected tool message must stay in the
        LLM context so the assistant tool_use keeps its tool_result pair."""
        mock = MockLLMAdapter([
            LLMResponse(
                content="",
                stop_reason="tool_use",
                tool_calls=[ToolCall(
                    id="t1", name="execute_shell",
                    arguments={"command": "unknown_cmd_xyz"},
                )],
            ),
            LLMResponse(content="OK, skipping that command.", stop_reason="complete"),
        ])
        loop = AgentLoop(tools, guardrails, analyzer, policy)

        session = await loop.run("Do something", mock)
        assert session.state == State.AWAITING_HUMAN

        session = loop.reject_pending(session)
        session = await loop.resume(session, mock)
        assert session.state == State.COMPLETED

        second_call_messages = mock.call_history[1]["messages"]
        rejected = [m for m in second_call_messages if m.role == "tool" and m.content.startswith("Rejected")]
        assert rejected, "Rejected tool message must be passed to the LLM to pair with its tool_use"
        assert rejected[0].tool_call_id == "t1"

    @pytest.mark.asyncio
    async def test_assistant_message_persists_tool_calls(self, tools, guardrails, analyzer, policy):
        """Assistant messages with tool_use must carry their tool_calls so
        adapters can round-trip the conversation to real providers."""
        mock = MockLLMAdapter([
            LLMResponse(
                content="Let me run the tests.",
                stop_reason="tool_use",
                tool_calls=[ToolCall(id="t1", name="execute_shell", arguments={"command": "echo ok"})],
            ),
            LLMResponse(content="Done.", stop_reason="complete"),
        ])
        loop = AgentLoop(tools, guardrails, analyzer, policy)

        session = await loop.run("Run tests", mock)

        assistant_msgs = [m for m in session.messages if m.role == "assistant" and m.tool_calls]
        assert len(assistant_msgs) == 1
        assert assistant_msgs[0].tool_calls[0].id == "t1"
