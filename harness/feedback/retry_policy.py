"""Retry policy — limits self-correction attempts and detects stuck loops."""
from harness.models import Feedback


class RetryPolicy:
    """Governs how many times the agent can retry after failure."""

    def __init__(self, max_retries: int = 3):
        self._max_retries = max_retries
        self._history: list[Feedback] = []

    def should_retry(self, current_count: int) -> bool:
        return current_count < self._max_retries

    def record(self, feedback: Feedback) -> None:
        self._history.append(feedback)

    def is_stuck(self) -> bool:
        """Detect if the agent is producing the same failure repeatedly."""
        if len(self._history) < 3:
            return False
        recent = self._history[-3:]
        # Check if last 3 failures have identical failure signatures
        first = recent[0]
        return all(
            len(f.failures) == len(first.failures) and
            all(a.file == b.file and a.function == b.function and a.message == b.message
                for a, b in zip(f.failures, first.failures))
            for f in recent[1:]
        )
