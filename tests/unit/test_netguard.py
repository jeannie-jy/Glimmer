"""Unit tests for the outbound-request guard (no real DNS/network)."""
import ipaddress
import socket

import pytest

from harness.netguard import validate_url


@pytest.fixture(autouse=True)
def _fake_dns(monkeypatch):
    """Deterministic DNS: literals resolve to themselves, known hosts mapped."""
    def fake(host, port):
        try:
            ipaddress.ip_address(host)
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (host, 0))]
        except ValueError:
            pass
        mapping = {
            "localhost": "127.0.0.1",
            "example.com": "93.184.216.34",
            "docs.python.org": "151.101.1.223",
            "ok.example.com": "93.184.216.34",
        }
        if host in mapping:
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (mapping[host], 0))]
        raise socket.gaierror("no such host")

    monkeypatch.setattr(socket, "getaddrinfo", fake)


def test_allows_public_https():
    assert validate_url("https://example.com/docs") is None
    assert validate_url("https://docs.python.org/3/") is None


def test_blocks_loopback_and_metadata():
    assert validate_url("http://127.0.0.1/") is not None
    assert validate_url("http://localhost/") is not None
    assert validate_url("http://169.254.169.254/latest/meta-data/") is not None
    assert validate_url("http://[::1]/") is not None


def test_blocks_private_ranges():
    assert validate_url("http://10.0.0.1/") is not None
    assert validate_url("http://172.16.0.5/") is not None
    assert validate_url("http://192.168.1.1/") is not None


def test_blocks_bad_schemes_and_ports():
    assert validate_url("file:///etc/passwd") is not None
    assert validate_url("ftp://example.com/") is not None
    assert validate_url("http://example.com:8080/") is not None
    assert validate_url("https://example.com:22/") is not None


def test_blocks_env_deny_list(monkeypatch):
    monkeypatch.setenv("WEB_FETCH_DENY", "evil.com")
    assert validate_url("https://evil.com/x") is not None
    assert validate_url("https://ok.example.com/") is None


def test_malformed_url():
    assert validate_url("not a url") is not None
    assert validate_url("") is not None
