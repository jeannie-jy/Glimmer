"""Outbound-request guard: block private/loopback/link-local/metadata targets.

Shared by the web_fetch tool (always host-side — sandbox containers have no
network) and by the guardrail engine's egress check for execute_shell URLs.
Synchronous on purpose: the guardrail engine's check() is sync, and the
resolution below is a pure local getaddrinfo (no network round-trip).
"""
import ipaddress
import os
import socket
from urllib.parse import urlparse

BLOCKED_NETS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def _env_deny() -> set[str]:
    return {d.strip().lower() for d in os.environ.get("WEB_FETCH_DENY", "").split(",") if d.strip()}


def validate_url(url: str) -> str | None:
    """Return None when the URL is safe to fetch, else a reason string."""
    if not url or not isinstance(url, str):
        return "Empty URL"
    try:
        parsed = urlparse(url)
    except ValueError:
        return f"Malformed URL: {url[:100]}"
    if parsed.scheme not in ("http", "https"):
        return f"Only http/https URLs are allowed (got: {parsed.scheme or 'no scheme'})"
    try:
        port = parsed.port
    except ValueError:
        return f"Invalid port in URL: {url[:100]}"
    if port not in (None, 80, 443):
        return f"Only ports 80/443 are allowed (got: {port})"
    host = (parsed.hostname or "").lower()
    if not host:
        return f"URL has no host: {url[:100]}"
    if host in _env_deny():
        return f"Domain is blocked: {host}"
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return f"Cannot resolve host: {host}"
    for info in infos:
        try:
            ip = ipaddress.ip_address(info[4][0])
        except ValueError:
            continue
        for net in BLOCKED_NETS:
            if ip in net:
                return f"Target resolves to a blocked address ({ip} in {net}): {host}"
    return None
