"""Tests for state machine transitions."""
import pytest
from harness.state_machine import transition, EventType
from harness.models import State


class TestStateMachine:
    def test_idle_to_planning_on_submit(self):
        assert transition(State.IDLE, EventType.TASK_SUBMIT) == State.PLANNING

    def test_planning_to_completed_on_finish(self):
        assert transition(State.PLANNING, EventType.LLM_FINISH) == State.COMPLETED

    def test_planning_to_executing_on_tool_use(self):
        assert transition(State.PLANNING, EventType.LLM_TOOL_USE) == State.EXECUTING

    def test_executing_to_awaiting_human_on_block(self):
        assert transition(State.EXECUTING, EventType.GUARD_BLOCK) == State.AWAITING_HUMAN

    def test_executing_to_observing_on_safe(self):
        assert transition(State.EXECUTING, EventType.GUARD_ALLOW) == State.OBSERVING

    def test_observing_to_correcting_on_fail(self):
        assert transition(State.OBSERVING, EventType.FEEDBACK_FAIL) == State.CORRECTING

    def test_observing_to_planning_on_pass(self):
        assert transition(State.OBSERVING, EventType.FEEDBACK_PASS) == State.PLANNING

    def test_correcting_to_planning(self):
        assert transition(State.CORRECTING, EventType.RETRY) == State.PLANNING

    def test_awaiting_human_approve_to_observing(self):
        assert transition(State.AWAITING_HUMAN, EventType.HUMAN_APPROVE) == State.OBSERVING

    def test_awaiting_human_reject_to_planning(self):
        assert transition(State.AWAITING_HUMAN, EventType.HUMAN_REJECT) == State.PLANNING

    def test_invalid_transition_raises(self):
        with pytest.raises(ValueError, match="No transition"):
            transition(State.IDLE, EventType.FEEDBACK_PASS)

    def test_any_state_to_error(self):
        for state in State:
            assert transition(state, EventType.ERROR) == State.ERROR
