"""Shared test fixtures."""
import pytest
from harness.models import ConfigData


@pytest.fixture
def default_config() -> ConfigData:
    return ConfigData()


@pytest.fixture
def sample_tool_result_pass() -> dict:
    return {
        "tool_name": "run_tests",
        "exit_code": 0,
        "stdout": "3 passed in 0.15s",
        "stderr": "",
        "duration_ms": 150,
        "structured": {"passed": 3, "failed": 0, "errors": 0},
    }


@pytest.fixture
def sample_tool_result_fail() -> dict:
    return {
        "tool_name": "run_tests",
        "exit_code": 1,
        "stdout": "1 passed, 2 failed in 0.23s",
        "stderr": "",
        "duration_ms": 230,
        "structured": {
            "passed": 1,
            "failed": 2,
            "errors": 0,
            "failures": [
                {"file": "tests/test_login.py", "line": 42, "function": "test_valid_login", "message": "AssertionError: expected 200 got 401"},
                {"file": "tests/test_login.py", "line": 58, "function": "test_token_expiry", "message": "AssertionError: expected True got False"},
            ],
        },
    }
