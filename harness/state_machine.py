"""Deterministic state machine for the agent loop."""
from enum import Enum
from harness.models import State


class EventType(str, Enum):
    """Events that trigger state transitions."""
    TASK_SUBMIT = "task_submit"
    LLM_FINISH = "llm_finish"
    LLM_TOOL_USE = "llm_tool_use"
    GUARD_ALLOW = "guard_allow"
    GUARD_BLOCK = "guard_block"
    GUARD_ASK_HUMAN = "guard_ask_human"
    FEEDBACK_PASS = "feedback_pass"
    FEEDBACK_FAIL = "feedback_fail"
    FEEDBACK_WARNING = "feedback_warning"
    FEEDBACK_UNKNOWN = "feedback_unknown"
    HUMAN_APPROVE = "human_approve"
    HUMAN_REJECT = "human_reject"
    RETRY = "retry"
    MAX_RETRIES = "max_retries"
    ERROR = "error"


# State transition table: (current_state, event) -> next_state
TRANSITIONS: dict[tuple[State, EventType], State] = {
    (State.IDLE, EventType.TASK_SUBMIT): State.PLANNING,

    (State.PLANNING, EventType.LLM_FINISH): State.COMPLETED,
    (State.PLANNING, EventType.LLM_TOOL_USE): State.EXECUTING,

    (State.EXECUTING, EventType.GUARD_ALLOW): State.OBSERVING,
    (State.EXECUTING, EventType.GUARD_BLOCK): State.AWAITING_HUMAN,
    (State.EXECUTING, EventType.GUARD_ASK_HUMAN): State.AWAITING_HUMAN,

    (State.AWAITING_HUMAN, EventType.HUMAN_APPROVE): State.OBSERVING,
    (State.AWAITING_HUMAN, EventType.HUMAN_REJECT): State.PLANNING,

    (State.OBSERVING, EventType.FEEDBACK_PASS): State.PLANNING,
    (State.OBSERVING, EventType.FEEDBACK_FAIL): State.CORRECTING,
    (State.OBSERVING, EventType.FEEDBACK_WARNING): State.PLANNING,
    (State.OBSERVING, EventType.FEEDBACK_UNKNOWN): State.PLANNING,

    (State.CORRECTING, EventType.RETRY): State.PLANNING,
    (State.CORRECTING, EventType.MAX_RETRIES): State.COMPLETED,

    (State.ERROR, EventType.TASK_SUBMIT): State.PLANNING,
}


def transition(current: State, event: EventType) -> State:
    """Compute the next state given current state and event.

    This is a pure function -- no LLM, no I/O, no side effects.
    Removing the LLM entirely, this still deterministically returns the correct next state.
    """
    # ERROR event transitions from any state
    if event == EventType.ERROR:
        return State.ERROR

    key = (current, event)
    if key not in TRANSITIONS:
        raise ValueError(
            f"No transition defined for ({current.value}, {event.value})"
        )
    return TRANSITIONS[key]
