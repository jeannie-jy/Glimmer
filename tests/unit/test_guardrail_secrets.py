"""Unit tests for secret scanning and egress guardrails."""
import ipaddress
import socket

import pytest

from harness.guardrails.engine import GuardrailEngine
from harness.guardrails.secrets import SecretScanner
from harness.models import ToolCall, GuardAction


@pytest.fixture(autouse=True)
def _fake_dns(monkeypatch):
    """Deterministic DNS: literals resolve to themselves (public IPs pass)."""
    def fake(host, port):
        try:
            ipaddress.ip_address(host)
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (host, 0))]
        except ValueError:
            pass
        raise socket.gaierror("no such host")

    monkeypatch.setattr(socket, "getaddrinfo", fake)


def test_scanner_hits_high_confidence_patterns():
    scanner = SecretScanner()
    samples = [
        "-----BEGIN RSA PRIVATE KEY-----",
        "AKIAIOSFODNN7EXAMPLE",
        "token ghp_abcdefghijklmnopqrstuvwxyz0123456789",
        "sk-ant-api03-abcdefghijklmnopqrstuvwxyz012345",
        "sk-abcdefghijklmnopqrstuvwxyz0123456789",
        "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0In0.abcdefghijklmnopqrstuvwxyz012345",
    ]
    for s in samples:
        result = scanner.check(s)
        assert result.action == GuardAction.ASK_HUMAN, s
        assert "***" in result.reason  # masked


def test_scanner_passes_ordinary_content():
    scanner = SecretScanner()
    assert scanner.check("def foo(): return 42").action == GuardAction.ALLOW
    assert scanner.check("echo hello world").action == GuardAction.ALLOW


def test_engine_asks_human_on_secret_in_write_file():
    engine = GuardrailEngine(sandbox_root=".")
    call = ToolCall(id="t1", name="write_file",
                    arguments={"path": "x.txt", "content": "key = 'sk-ant-abcdefghijklmnopqrstuvwxyz012345'"})
    result = engine.check(call)
    assert result.action == GuardAction.ASK_HUMAN
    assert result.layer == 4


def test_engine_blocks_internal_urls_in_shell_command():
    engine = GuardrailEngine(sandbox_root=".")
    call = ToolCall(id="t2", name="execute_shell",
                    arguments={"command": "pip install http://169.254.169.254/x"})
    result = engine.check(call)
    assert result.action == GuardAction.BLOCK
    assert "169.254.169.254" in result.reason


def test_engine_allows_public_urls_in_shell_command():
    engine = GuardrailEngine(sandbox_root=".")
    call = ToolCall(id="t3", name="execute_shell",
                    arguments={"command": "pip install https://8.8.8.8/simple/"})
    result = engine.check(call)
    assert result.action == GuardAction.ALLOW
