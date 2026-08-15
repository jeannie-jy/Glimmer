"""Fetch a public web page over HTTP(S) — always host-side.

Sandbox containers run with network_mode=none, so this tool executes in the
server process in every deployment mode. SSRF is the primary threat: every
hop (including each redirect) passes netguard validation, which blocks
private/loopback/link-local/cloud-metadata targets and non-80/443 ports.
"""
import time

import httpx

from harness.tools.registry import Tool
from harness.models import ToolResult
from harness.netguard import validate_url

MAX_BYTES = 512 * 1024
MAX_REDIRECTS = 5
MAX_STDOUT_CHARS = 4096  # LLM context contains only stdout
ALLOWED_CONTENT_TYPES = ("text/", "application/json", "application/xml")


class WebFetchTool(Tool):
    @property
    def name(self) -> str:
        return "web_fetch"

    @property
    def description(self) -> str:
        return "Fetch a public web page and return its text content (truncated). Only http(s) on ports 80/443; private-network and cloud-metadata targets are blocked."

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
                    resp = await client.get(current, headers={"User-Agent": "GlimmerAgent/1.0"})
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
                body = resp.text
                if len(body) > MAX_BYTES:
                    body = body[:MAX_BYTES]
                stdout_body = body[:MAX_STDOUT_CHARS]
                if len(body) > MAX_STDOUT_CHARS:
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
