"""Agent main loop — the state machine executor."""
import uuid
from datetime import datetime
from harness.models import (
    State, Message, Session, ToolCall, ToolResult,
    GuardAction, Verdict,
)
from harness.state_machine import transition, EventType
from harness.llm.adapter import LLMAdapter
from harness.tools.registry import ToolRegistry, Tool
from harness.guardrails.engine import GuardrailEngine
from harness.feedback.analyzer import FeedbackAnalyzer
from harness.feedback.retry_policy import RetryPolicy


MAX_ITERATIONS = 50


class AgentLoop:
    """Main agent loop — drives the state machine, coordinates all components.

    Orchestrates the full agent lifecycle:
      IDLE -> PLANNING -> EXECUTING -> OBSERVING -> (CORRECTING ->)* -> COMPLETED

    Each state transition is governed by the deterministic state machine,
    with guardrails, feedback analysis, and retry policy acting as decision
    points along the way.
    """

    def __init__(
        self,
        tools: ToolRegistry,
        guardrails: GuardrailEngine,
        analyzer: FeedbackAnalyzer,
        policy: RetryPolicy,
    ):
        self._tools = tools
        self._guardrails = guardrails
        self._analyzer = analyzer
        self._policy = policy

    async def run(self, task: str, llm: LLMAdapter) -> Session:
        """Execute a task using the LLM-driven agent loop.

        Args:
            task: The user task/instruction to execute.
            llm: An LLM adapter (real or mock) for generating responses.

        Returns:
            A completed Session with full message history, tool calls,
            token usage, and final state.
        """
        session = Session(id=str(uuid.uuid4()), task=task, state=State.IDLE)
        tool_defs = self._tools.list_defs()
        tool_desc = "\n".join(f"- {t.name}: {t.description}" for t in tool_defs)

        session.messages.append(Message(role="system", content=(
            "You are a coding agent. You help developers write, fix, and improve code.\n"
            "Available tools:\n" + tool_desc + "\n"
            "When you complete a task, explain what you did clearly."
        )))
        session.messages.append(Message(role="user", content=task))
        session.state = transition(State.IDLE, EventType.TASK_SUBMIT)

        pending_tool_calls: list[ToolCall] = []
        last_tool_result: ToolResult | None = None
        last_feedback = None
        iteration = 0

        while session.state not in (State.COMPLETED, State.ERROR, State.AWAITING_HUMAN) and iteration < MAX_ITERATIONS:
            iteration += 1

            if session.state == State.PLANNING:
                # Filter messages: send the LLM a clean conversation history
                msgs = [m for m in session.messages if m.role != "tool" or m.content.startswith("Exit code")]
                response = await llm.chat(msgs, tool_defs)
                session.total_tokens.input_tokens += response.usage.input_tokens
                session.total_tokens.output_tokens += response.usage.output_tokens
                session.total_tokens.total_tokens += response.usage.total_tokens

                assistant_msg = Message(role="assistant", content=response.content)
                session.messages.append(assistant_msg)

                if response.tool_calls:
                    pending_tool_calls = list(response.tool_calls)
                    session.state = transition(session.state, EventType.LLM_TOOL_USE)
                else:
                    session.state = transition(session.state, EventType.LLM_FINISH)

            elif session.state == State.EXECUTING:
                if not pending_tool_calls:
                    session.state = transition(session.state, EventType.GUARD_ALLOW)
                    continue

                tc = pending_tool_calls.pop(0)
                guard_result = self._guardrails.check(tc)

                if guard_result.action == GuardAction.BLOCK:
                    session.messages.append(Message(
                        role="tool",
                        content=f"BLOCKED: {guard_result.reason}",
                        tool_call_id=tc.id,
                    ))
                    session.state = transition(session.state, EventType.GUARD_BLOCK)
                elif guard_result.action == GuardAction.ASK_HUMAN:
                    session._pending_approval = tc  # type: ignore
                    session._guard_reason = guard_result.reason  # type: ignore
                    session.state = transition(session.state, EventType.GUARD_ASK_HUMAN)
                else:
                    try:
                        result = await self._tools.dispatch(tc)
                    except Exception as e:
                        result = ToolResult(tool_name=tc.name, exit_code=-1, stderr=str(e))

                    session.tool_calls.append(tc)
                    last_tool_result = result
                    session.messages.append(Message(
                        role="tool",
                        content=f"Exit code: {result.exit_code}\n{result.stdout[:2000]}\n{result.stderr[:1000]}",
                        tool_call_id=tc.id,
                        tool_result=result,
                    ))
                    session.state = transition(session.state, EventType.GUARD_ALLOW)

            elif session.state == State.OBSERVING:
                if last_tool_result is None:
                    session.state = State.ERROR
                    break

                feedback = self._analyzer.analyze(last_tool_result)
                feedback.retry_count = session.retry_count
                last_feedback = feedback

                if feedback.verdict == Verdict.PASS:
                    session.state = transition(session.state, EventType.FEEDBACK_PASS)
                elif feedback.verdict == Verdict.FAIL:
                    self._policy.record(feedback)
                    session.state = transition(session.state, EventType.FEEDBACK_FAIL)
                elif feedback.verdict == Verdict.WARNING:
                    session.state = transition(session.state, EventType.FEEDBACK_WARNING)
                else:
                    session.state = transition(session.state, EventType.FEEDBACK_UNKNOWN)

            elif session.state == State.CORRECTING:
                if not self._policy.should_retry(session.retry_count) or self._policy.is_stuck():
                    session.state = transition(session.state, EventType.MAX_RETRIES)
                else:
                    session.retry_count += 1
                    if last_feedback:
                        session.messages.append(Message(
                            role="user",
                            content=f"Previous attempt failed. {last_feedback.suggested_fix}\nPlease fix and try again.",
                        ))
                    session.state = transition(session.state, EventType.RETRY)

        # Graceful termination for states that didn't complete naturally
        if session.state not in (State.COMPLETED, State.AWAITING_HUMAN, State.ERROR):
            session.state = State.COMPLETED
        session.completed_at = datetime.now()
        return session

    def approve_pending(self, session: Session) -> Session:
        """Approve a tool call that was flagged as ASK_HUMAN.

        Called externally (e.g., by a WebSocket handler) to continue
        execution after human approval.
        """
        if session.state == State.AWAITING_HUMAN:
            session.state = transition(session.state, EventType.HUMAN_APPROVE)
        return session

    def reject_pending(self, session: Session) -> Session:
        """Reject a tool call that was flagged as ASK_HUMAN.

        Adds a rejection message to the conversation and returns the
        session to PLANNING.
        """
        tc = getattr(session, "_pending_approval", None)
        if tc and session.state == State.AWAITING_HUMAN:
            session.messages.append(Message(
                role="tool",
                content=f"Rejected: {tc.name}",
                tool_call_id=tc.id,
            ))
            session.state = transition(session.state, EventType.HUMAN_REJECT)
        return session
