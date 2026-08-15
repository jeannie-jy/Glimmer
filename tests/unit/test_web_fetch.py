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


class FakeStreamResponse:
    """Minimal httpx streaming response: headers + aiter_bytes()."""

    def __init__(self, status_code=200, headers=None, body=b"ok", url="https://example.com/"):
        self.status_code = status_code
        self.headers = headers or {"content-type": "text/html"}
        self.body = body
        self.url = url
        self.delivered = 0  # total bytes yielded to the caller

    async def aiter_bytes(self):
        for b in self.body:
            self.delivered += 1
            yield bytes([b])


class _FakeStreamContext:
    def __init__(self, resp):
        self._resp = resp

    async def __aenter__(self):
        return self._resp

    async def __aexit__(self, *args):
        pass


class FakeClient:
    """Fake httpx.AsyncClient: stream() returns a fake response context."""

    def __init__(self, timeout=None, follow_redirects=False):
        self.gets: list[str] = []
        self.responses: list[FakeStreamResponse] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    def stream(self, method, url, headers=None):
        self.gets.append(url)
        resp = self._make_response(url)
        self.responses.append(resp)
        return _FakeStreamContext(resp)

    def _make_response(self, url):
        return FakeStreamResponse(url=url)


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
        def _make_response(self, url):
            return FakeStreamResponse(status_code=302,
                                      headers={"content-type": "text/html", "location": "http://10.0.0.1/steal"},
                                      url=url)
    monkeypatch.setattr(web_fetch.httpx, "AsyncClient", RedirectClient)
    tool = web_fetch.WebFetchTool()
    result = asyncio.run(tool.execute({"url": "https://example.com/"}))
    assert result.exit_code == 1
    assert "10.0.0.1" in result.stderr


def test_non_text_content_type_rejected(monkeypatch):
    class ImageClient(FakeClient):
        def _make_response(self, url):
            return FakeStreamResponse(headers={"content-type": "image/png"}, url=url)
    monkeypatch.setattr(web_fetch.httpx, "AsyncClient", ImageClient)
    tool = web_fetch.WebFetchTool()
    result = asyncio.run(tool.execute({"url": "https://example.com/x.png"}))
    assert result.exit_code == 1
    assert "Content type" in result.stderr


def test_oversized_body_truncated_at_cap_without_unbounded_read(monkeypatch):
    # 1000 bytes past the cap — must be truncated, and the fake transport
    # must never be asked to deliver more than MAX_BYTES + 1 bytes.
    body = b"x" * (web_fetch.MAX_BYTES + 1000)
    clients: list[FakeClient] = []

    class BigClient(FakeClient):
        def __init__(self, timeout=None, follow_redirects=False):
            super().__init__(timeout=timeout, follow_redirects=follow_redirects)
            clients.append(self)

        def _make_response(self, url):
            return FakeStreamResponse(body=body, url=url)

    monkeypatch.setattr(web_fetch.httpx, "AsyncClient", BigClient)
    tool = web_fetch.WebFetchTool()
    result = asyncio.run(tool.execute({"url": "https://example.com/big"}))

    assert result.exit_code == 0
    assert len(result.structured["content"]) == web_fetch.MAX_BYTES
    assert result.structured["content"] == "x" * web_fetch.MAX_BYTES
    assert clients[0].gets == ["https://example.com/big"]
    delivered = sum(r.delivered for c in clients for r in c.responses)
    assert delivered <= web_fetch.MAX_BYTES + 1
