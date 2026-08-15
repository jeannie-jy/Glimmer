"""Fetch a public web page over HTTP(S) — always host-side.

Sandbox containers run with network_mode=none, so this tool executes in the
server process in every deployment mode. SSRF is the primary threat: every
hop (including each redirect) passes netguard validation, which blocks
private/loopback/link-local/cloud-metadata targets and non-80/443 ports.
"""
import time
from html.parser import HTMLParser

import httpx

from harness.tools.registry import Tool
from harness.models import ToolResult
from harness.netguard import validate_url

MAX_BYTES = 512 * 1024
MAX_REDIRECTS = 5
MAX_STDOUT_CHARS = 4096  # LLM context contains only stdout
ALLOWED_CONTENT_TYPES = ("text/", "application/json", "application/xml")


# Void elements produce no end tag, so they are never pushed on the skip
# stack — pushing them would misalign it on the next end tag.
_VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input",
              "link", "meta", "param", "source", "track", "wbr"}


class _TextExtractor(HTMLParser):
    """Best-effort HTML→text: title + meta description + visible body text.

    Zero-dependency (stdlib). Skips script/style/noscript/svg/head content
    and hidden/aria-hidden content (invisible to real users — e.g. GitHub's
    SSR "Uh oh!" placeholder) via a per-element skip-flag stack, and
    collapses whitespace. The LLM only reads stdout, and raw HTML's first
    ~4KB is <head> boilerplate on almost any site — extraction is what makes
    fetched pages actually analyzable. On malformed markup the caller falls
    back to the raw body.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.description = ""
        self.chunks: list[str] = []
        self._in_title = False
        self._skip = 0  # >0 while inside skipped content
        self._stack: list[bool] = []  # per-element skip flags, start→end

    @staticmethod
    def _is_skip(tag: str, attrs: dict) -> bool:
        return (tag in ("script", "style", "noscript", "svg", "head")
                or "hidden" in attrs or attrs.get("aria-hidden") == "true")

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        skip = self._is_skip(tag, attrs)
        if tag not in _VOID_TAGS:
            self._stack.append(skip)
        if skip:
            self._skip += 1
        if tag == "title":
            self._in_title = True
        if tag == "meta" and not self.description:
            if (attrs.get("name") or "").lower() == "description":
                self.description = (attrs.get("content") or "").strip()

    def handle_startendtag(self, tag, attrs):
        # XHTML-style self-closed tag: no end tag will follow, so nothing
        # is pushed/popped. Only meta description is worth capturing here.
        if tag == "meta" and not self.description:
            attrs = dict(attrs)
            if (attrs.get("name") or "").lower() == "description":
                self.description = (attrs.get("content") or "").strip()

    def handle_endtag(self, tag):
        if self._stack:
            if self._stack.pop():
                self._skip = max(0, self._skip - 1)
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        elif not self._skip:
            self.chunks.append(data)


def _html_to_text(body: str) -> str:
    parser = _TextExtractor()
    try:
        parser.feed(body)
        parser.close()
    except Exception:
        return body
    text = " ".join(" ".join(parser.chunks).split())
    parts = []
    if parser.title.strip():
        parts.append(f"Title: {parser.title.strip()}")
    if parser.description:
        parts.append(f"Description: {parser.description}")
    if text:
        parts.append(text)
    return "\n\n".join(parts) if parts else body


class WebFetchTool(Tool):
    @property
    def name(self) -> str:
        return "web_fetch"

    @property
    def description(self) -> str:
        return "Fetch a public web page and return its readable text content (HTML converted to plain text, truncated). Only http(s) on ports 80/443; private-network and cloud-metadata targets are blocked."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "HTTP(S) URL to fetch"},
            },
            "required": ["url"],
        }

    async def execute(self, arguments: dict) -> ToolResult:
        start = time.time()
        url = str(arguments.get("url", ""))
        reason = validate_url(url)
        if reason:
            return ToolResult(tool_name="web_fetch", exit_code=1, stdout="", stderr=reason,
                duration_ms=int((time.time() - start) * 1000))

        current = url
        try:
            for _ in range(MAX_REDIRECTS + 1):
                reason = validate_url(current)
                if reason:
                    return ToolResult(tool_name="web_fetch", exit_code=1, stdout="", stderr=reason,
                        duration_ms=int((time.time() - start) * 1000))
                async with httpx.AsyncClient(timeout=15.0, follow_redirects=False) as client:
                    async with client.stream("GET", current, headers={"User-Agent": "GlimmerAgent/1.0"}) as resp:
                        if resp.status_code in (301, 302, 303, 307, 308):
                            loc = resp.headers.get("location")
                            if not loc:
                                return ToolResult(tool_name="web_fetch", exit_code=1, stdout="",
                                    stderr=f"Redirect without location: {current}",
                                    duration_ms=int((time.time() - start) * 1000))
                            current = str(httpx.URL(resp.url).join(loc))
                            continue

                        ct = resp.headers.get("content-type", "")
                        if not any(ct.lower().startswith(a) for a in ALLOWED_CONTENT_TYPES):
                            return ToolResult(tool_name="web_fetch", exit_code=1, stdout="",
                                stderr=f"Content type not allowed: {ct or '(none)'}",
                                duration_ms=int((time.time() - start) * 1000))

                        # Stream the body with a hard cap: abort as soon as
                        # MAX_BYTES is exceeded so an oversized response is
                        # never fully materialized in memory (the transfer
                        # itself is bounded too, not just the stored copy).
                        buf = bytearray()
                        async for chunk in resp.aiter_bytes():
                            buf.extend(chunk)
                            if len(buf) > MAX_BYTES:
                                break
                        body = bytes(buf[:MAX_BYTES]).decode("utf-8", errors="replace")
                        stdout_source = _html_to_text(body) if ct.lower().startswith("text/html") else body
                        stdout_body = stdout_source[:MAX_STDOUT_CHARS]
                        if len(stdout_source) > MAX_STDOUT_CHARS:
                            stdout_body += "\n...[truncated]"
                        return ToolResult(tool_name="web_fetch", exit_code=0,
                            stdout=stdout_body,
                            structured={
                                "final_url": str(resp.url),
                                "status_code": resp.status_code,
                                "content_type": ct,
                                "content": body,
                            },
                            duration_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(tool_name="web_fetch", exit_code=1, stdout="", stderr=str(e),
                duration_ms=int((time.time() - start) * 1000))
        return ToolResult(tool_name="web_fetch", exit_code=1, stdout="", stderr="Too many redirects",
            duration_ms=int((time.time() - start) * 1000))
