"""Unit tests for the web_fetch tool (fake transport, no real network)."""
import asyncio
import ipaddress
import socket

import pytest

from harness.tools import web_fetch


@pytest.fixture(autouse=True)
def _fake_dns(monkeypatch):
    """Deterministic DNS: literals resolve to themselves, example.com public."""
    def fake(host, port):
        try:
            ipaddress.ip_address(host)
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (host, 0))]
        except ValueError:
            pass
        if host == "example.com":
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]
        raise socket.gaierror("no such host")

    monkeypatch.setattr(socket, "getaddrinfo", fake)


class FakeResponse:
    def __init__(self, status_code=200, headers=None, text="ok", url="https://example.com/"):
        self.status_code = status_code
        self.headers = headers or {"content-type": "text/html"}
        self.text = text
        self.url = url


class FakeClient:
    def __init__(self, timeout=None, follow_redirects=False):
        self.gets: list[str] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def get(self, url, headers=None):
        self.gets.append(url)
        return FakeResponse()


def test_blocked_url_never_reaches_client():
    tool = web_fetch.WebFetchTool()
    result = asyncio.run(tool.execute({"url": "http://169.254.169.254/latest/meta-data/"}))
    assert result.exit_code == 1
    assert "169.254.169.254" in result.stderr


def test_fetch_returns_structured_content(monkeypatch):
    monkeypatch.setattr(web_fetch.httpx, "AsyncClient", FakeClient)
    tool = web_fetch.WebFetchTool()
    result = asyncio.run(tool.execute({"url": "https://example.com/"}))
    assert result.exit_code == 0
    assert result.structured["status_code"] == 200
    assert result.structured["content"] == "ok"
    assert "ok" in result.stdout  # LLM sees stdout


def test_redirect_to_private_target_is_blocked(monkeypatch):
    class RedirectClient(FakeClient):
        async def get(self, url, headers=None):
            return FakeResponse(status_code=302,
                                headers={"content-type": "text/html", "location": "http://10.0.0.1/steal"})
    monkeypatch.setattr(web_fetch.httpx, "AsyncClient", RedirectClient)
    tool = web_fetch.WebFetchTool()
    result = asyncio.run(tool.execute({"url": "https://example.com/"}))
    assert result.exit_code == 1
    assert "10.0.0.1" in result.stderr


def test_non_text_content_type_rejected(monkeypatch):
    class ImageClient(FakeClient):
        async def get(self, url, headers=None):
            return FakeResponse(headers={"content-type": "image/png"})
    monkeypatch.setattr(web_fetch.httpx, "AsyncClient", ImageClient)
    tool = web_fetch.WebFetchTool()
    result = asyncio.run(tool.execute({"url": "https://example.com/x.png"}))
    assert result.exit_code == 1
    assert "Content type" in result.stderr
