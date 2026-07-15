"""Tests for retry policy."""
import pytest
from harness.feedback.retry_policy import RetryPolicy
from harness.models import Feedback, Verdict, Failure


class TestRetryPolicy:
    @pytest.fixture
    def policy(self):
        return RetryPolicy(max_retries=3)

    def test_allows_retry_within_limit(self, policy):
        assert policy.should_retry(0) is True
        assert policy.should_retry(1) is True
        assert policy.should_retry(2) is True

    def test_blocks_retry_at_limit(self, policy):
        assert policy.should_retry(3) is False

    def test_early_termination_on_repeated_failure(self, policy):
        f1 = Feedback(verdict=Verdict.FAIL, failures=[Failure(file="a.py", function="test_x", message="E1")])
        f2 = Feedback(verdict=Verdict.FAIL, failures=[Failure(file="a.py", function="test_x", message="E1")])
        f3 = Feedback(verdict=Verdict.FAIL, failures=[Failure(file="a.py", function="test_x", message="E1")])

        policy.record(f1)
        policy.record(f2)
        policy.record(f3)

        assert policy.is_stuck() is True

    def test_different_failures_not_stuck(self, policy):
        policy.record(Feedback(verdict=Verdict.FAIL, failures=[Failure(file="a.py", function="test_x", message="E1")]))
        policy.record(Feedback(verdict=Verdict.FAIL, failures=[Failure(file="b.py", function="test_y", message="E2")]))

        assert policy.is_stuck() is False
