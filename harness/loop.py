"""Agent main loop — the state machine executor."""
import uuid
from datetime import datetime
from typing import Any, Callable

from harness.models import (
    State, Message, Session, ToolCall, ToolResult, ToolDef,
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
        docker_mgr: object | None = None,
        container_id: str | None = None,
    ):
        self._tools = tools
        self._guardrails = guardrails
        self._analyzer = analyzer
        self._policy = policy
        self._docker_mgr = docker_mgr
        self._container_id = container_id
        self._on_event: Callable[..., Any] | None = None

    def on_event(self, handler: Callable[..., Any]) -> None:
        """Register an event handler called with ``event``, ``**data``.

        Handlers are awaited.  Events include:
          ``state.change``, ``tool.invoke``, ``tool.result``,
          ``guardrail.pending``, ``feedback.analysis``,
          ``llm.response``, ``session.complete``, ``session.error``.
        """
        self._on_event = handler

    async def _emit(self, event: str, **data: Any) -> None:
        if self._on_event:
            await self._on_event(event=event, **data)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

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
        await self._emit("state.change", **{"from": "idle", "to": session.state.value})

        return await self._run_loop(session, llm, tool_defs)

    def approve_pending(self, session: Session) -> Session:
        """Approve a tool call that was flagged as ASK_HUMAN.

        Called externally (e.g., by a WebSocket handler) to continue
        execution after human approval. Transitions the session state
        to OBSERVING so that resume() can dispatch the tool.

        After calling this, invoke resume(session, llm) to re-enter the loop.
        """
        if session.state == State.AWAITING_HUMAN:
            session.state = transition(session.state, EventType.HUMAN_APPROVE)
        return session

    def reject_pending(self, session: Session) -> Session:
        """Reject a tool call that was flagged as ASK_HUMAN.

        Adds a rejection message to the conversation and transitions the
        session state to PLANNING.

        After calling this, invoke resume(session, llm) to re-enter the loop.
        """
        tc = session._pending_approval
        if tc and session.state == State.AWAITING_HUMAN:
            session.messages.append(Message(
                role="tool",
                content=f"Rejected: {tc.name}",
                tool_call_id=tc.id,
            ))
            session.state = transition(session.state, EventType.HUMAN_REJECT)
        return session

    async def resume(self, session: Session, llm: LLMAdapter) -> Session:
        """Resume a paused session after human approval or rejection.

        Called after approve_pending() or reject_pending() has transitioned
        the session state. Dispatches the approved tool if applicable, then
        re-enters the main loop.

        Args:
            session: The paused session (state must be OBSERVING or PLANNING).
            llm: An LLM adapter for generating subsequent responses.

        Returns:
            The completed Session after the loop finishes.
        """
        if session.state not in (State.OBSERVING, State.PLANNING):
            raise ValueError(
                f"Cannot resume from state {session.state}. "
                "Call approve_pending() or reject_pending() first."
            )

        pending_tool_calls: list[ToolCall] = []
        last_tool_result: ToolResult | None = None

        if session.state == State.OBSERVING:
            # Approve case: dispatch the pending tool held for human review
            tc = session._pending_approval
            if tc is not None:
                await self._emit("tool.invoke", tool=tc.name, args=tc.arguments)
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
                session._pending_approval = None
                await self._emit(
                    "tool.result",
                    tool_name=result.tool_name, exit_code=result.exit_code,
                    stdout=result.stdout[:2000], stderr=result.stderr[:1000],
                    duration_ms=result.duration_ms,
                )
            else:
                # BLOCK case (no _pending_approval): skip to PLANNING
                prev = session.state
                session.state = State.PLANNING
                await self._emit("state.change", **{"from": prev.value, "to": session.state.value})

        tool_defs = self._tools.list_defs()
        return await self._run_loop(session, llm, tool_defs, pending_tool_calls, last_tool_result)

    # ------------------------------------------------------------------
    # Internal loop
    # ------------------------------------------------------------------

    async def _run_loop(
        self,
        session: Session,
        llm: LLMAdapter,
        tool_defs: list[ToolDef],
        pending_tool_calls: list[ToolCall] | None = None,
        last_tool_result: ToolResult | None = None,
    ) -> Session:
        """Inner agent loop — shared by *run* and *resume*.

        Args:
            session: The session to operate on.
            llm: LLM adapter.
            tool_defs: Tool definitions for the LLM.
            pending_tool_calls: Already-queued tool calls from a prior batch
                (Bug 1 fix: carry-over from a previous LLM response).
            last_tool_result: Result from the most recently dispatched tool
                (used when resuming after human approval).
        """
        if pending_tool_calls is None:
            pending_tool_calls = []
        last_feedback = None
        iteration = 0

        while session.state not in (State.COMPLETED, State.ERROR, State.AWAITING_HUMAN) and iteration < MAX_ITERATIONS:
            iteration += 1

            if session.state == State.PLANNING:
                # Bug 1 fix: skip LLM call if there are pending batch tool calls
                if pending_tool_calls:
                    prev = session.state
                    session.state = transition(session.state, EventType.LLM_TOOL_USE)
                    await self._emit("state.change", **{"from": prev.value, "to": session.state.value})
                    continue

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
                    await self._emit(
                        "llm.response",
                        content=response.content,
                        tool_calls=[t.model_dump() for t in response.tool_calls],
                    )
                    prev = session.state
                    session.state = transition(session.state, EventType.LLM_TOOL_USE)
                    await self._emit("state.change", **{"from": prev.value, "to": session.state.value})
                else:
                    await self._emit("llm.response", content=response.content, tool_calls=[])
                    prev = session.state
                    session.state = transition(session.state, EventType.LLM_FINISH)
                    await self._emit("state.change", **{"from": prev.value, "to": session.state.value})

            elif session.state == State.EXECUTING:
                if not pending_tool_calls:
                    prev = session.state
                    session.state = transition(session.state, EventType.GUARD_ALLOW)
                    await self._emit("state.change", **{"from": prev.value, "to": session.state.value})
                    continue

                tc = pending_tool_calls.pop(0)
                await self._emit("tool.invoke", tool=tc.name, args=tc.arguments)
                guard_result = self._guardrails.check(tc)

                if guard_result.action == GuardAction.BLOCK:
                    session.messages.append(Message(
                        role="tool",
                        content=f"BLOCKED: {guard_result.reason}",
                        tool_call_id=tc.id,
                    ))
                    prev = session.state
                    session.state = transition(session.state, EventType.GUARD_BLOCK)
                    await self._emit("state.change", **{"from": prev.value, "to": session.state.value})
                    await self._emit(
                        "guardrail.pending",
                        action="blocked", reason=guard_result.reason,
                        tool=tc.name, args=tc.arguments,
                    )
                elif guard_result.action == GuardAction.ASK_HUMAN:
                    session._pending_approval = tc
                    session._guard_reason = guard_result.reason
                    prev = session.state
                    session.state = transition(session.state, EventType.GUARD_ASK_HUMAN)
                    await self._emit("state.change", **{"from": prev.value, "to": session.state.value})
                    await self._emit(
                        "guardrail.pending",
                        action="ask_human", reason=guard_result.reason,
                        tool=tc.name, args=tc.arguments,
                    )
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
                    prev = session.state
                    session.state = transition(session.state, EventType.GUARD_ALLOW)
                    await self._emit("state.change", **{"from": prev.value, "to": session.state.value})
                    await self._emit(
                        "tool.result",
                        tool_name=result.tool_name, exit_code=result.exit_code,
                        stdout=result.stdout[:2000], stderr=result.stderr[:1000],
                        duration_ms=result.duration_ms,
                    )

            elif session.state == State.OBSERVING:
                if last_tool_result is None:
                    session.state = State.ERROR
                    await self._emit("session.error", message="No tool result available during OBSERVING")
                    break

                feedback = self._analyzer.analyze(last_tool_result)
                feedback.retry_count = session.retry_count
                last_feedback = feedback

                await self._emit(
                    "feedback.analysis",
                    verdict=feedback.verdict.value,
                    summary=feedback.summary,
                    failures=[f.model_dump() for f in feedback.failures],
                    suggested_fix=feedback.suggested_fix,
                )

                if feedback.verdict == Verdict.FAIL:
                    self._policy.record(feedback)
                    prev = session.state
                    session.state = transition(session.state, EventType.FEEDBACK_FAIL)
                    await self._emit("state.change", **{"from": prev.value, "to": session.state.value})
                elif feedback.verdict == Verdict.PASS:
                    prev = session.state
                    session.state = transition(session.state, EventType.FEEDBACK_PASS)
                    await self._emit("state.change", **{"from": prev.value, "to": session.state.value})
                elif feedback.verdict == Verdict.WARNING:
                    prev = session.state
                    session.state = transition(session.state, EventType.FEEDBACK_WARNING)
                    await self._emit("state.change", **{"from": prev.value, "to": session.state.value})
                else:
                    prev = session.state
                    session.state = transition(session.state, EventType.FEEDBACK_UNKNOWN)
                    await self._emit("state.change", **{"from": prev.value, "to": session.state.value})

                # Bug 1 fix: if more batch tool calls remain, go back to EXECUTING
                # instead of PLANNING, to continue processing the batch
                if session.state == State.PLANNING and pending_tool_calls:
                    prev = session.state
                    session.state = transition(session.state, EventType.BATCH_CONTINUE)
                    await self._emit("state.change", **{"from": prev.value, "to": session.state.value})

            elif session.state == State.CORRECTING:
                if not self._policy.should_retry(session.retry_count) or self._policy.is_stuck():
                    prev = session.state
                    session.state = transition(session.state, EventType.MAX_RETRIES)
                    await self._emit("state.change", **{"from": prev.value, "to": session.state.value})
                else:
                    session.retry_count += 1
                    if last_feedback:
                        escalation_messages = [
                            f"Previous attempt failed. {last_feedback.suggested_fix}\nPlease fix and try again.",
                            f"Second attempt also failed. {last_feedback.suggested_fix}\nPlease be more careful this time.",
                            f"THIRD AND FINAL ATTEMPT. {last_feedback.suggested_fix}\nIf this fails, the task will be terminated.",
                        ]
                        idx = min(session.retry_count - 1, len(escalation_messages) - 1)
                        session.messages.append(Message(
                            role="user",
                            content=escalation_messages[idx],
                        ))
                    prev = session.state
                    session.state = transition(session.state, EventType.RETRY)
                    await self._emit("state.change", **{"from": prev.value, "to": session.state.value})

        # Graceful termination for states that didn't complete naturally
        if session.state not in (State.COMPLETED, State.AWAITING_HUMAN, State.ERROR):
            session.state = State.COMPLETED
        if session.state == State.COMPLETED:
            await self._emit("session.complete", session_id=session.id)
        elif session.state == State.ERROR:
            await self._emit("session.error", message="Agent loop terminated with error")
        session.completed_at = datetime.now()
        return session
