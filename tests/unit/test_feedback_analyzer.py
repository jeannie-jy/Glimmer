"""Tests for feedback analyzer."""
import pytest
from harness.feedback.analyzer import FeedbackAnalyzer
from harness.models import ToolResult, Feedback, Verdict, Failure


class TestFeedbackAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return FeedbackAnalyzer()

    def test_passing_tests_produce_pass_verdict(self, analyzer, sample_tool_result_pass):
        result = ToolResult(**sample_tool_result_pass)
        feedback = analyzer.analyze(result)
        assert feedback.verdict == Verdict.PASS

    def test_failing_tests_produce_fail_verdict(self, analyzer, sample_tool_result_fail):
        result = ToolResult(**sample_tool_result_fail)
        feedback = analyzer.analyze(result)
        assert feedback.verdict == Verdict.FAIL

    def test_extracts_failure_details(self, analyzer, sample_tool_result_fail):
        result = ToolResult(**sample_tool_result_fail)
        feedback = analyzer.analyze(result)
        assert len(feedback.failures) == 2
        assert feedback.failures[0].file == "tests/test_login.py"
        assert feedback.failures[0].function == "test_valid_login"
        assert "expected 200 got 401" in feedback.failures[0].message

    def test_nonzero_exit_code_without_structured_is_fail(self, analyzer):
        result = ToolResult(tool_name="execute_shell", exit_code=1, stdout="", stderr="command not found")
        feedback = analyzer.analyze(result)
        assert feedback.verdict == Verdict.FAIL

    def test_read_file_returns_unknown(self, analyzer):
        result = ToolResult(tool_name="read_file", exit_code=0, stdout="file contents")
        feedback = analyzer.analyze(result)
        assert feedback.verdict == Verdict.UNKNOWN

    def test_generates_suggested_fix_for_failures(self, analyzer, sample_tool_result_fail):
        result = ToolResult(**sample_tool_result_fail)
        feedback = analyzer.analyze(result)
        assert "test_valid_login" in feedback.suggested_fix
        assert "test_token_expiry" in feedback.suggested_fix
        assert "AssertionError" in feedback.suggested_fix
