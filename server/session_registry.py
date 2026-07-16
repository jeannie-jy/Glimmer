"""In-memory registry mapping session_id → container info for cross-route access.

The WebSocket handler registers sessions, and REST routes (files download, etc.)
look up container references to execute commands inside sandboxes.
"""
import time

# {session_id: {"docker_mgr": ..., "container_id": ..., "user_id": ..., "expires": ...}}
_registry: dict[str, dict] = {}

TTL_SECONDS = 3600  # entries expire after 1 hour


def register(session_id: str, docker_mgr, container_id: str, user_id: str) -> None:
    _registry[session_id] = {
        "docker_mgr": docker_mgr,
        "container_id": container_id,
        "user_id": user_id,
        "expires": time.time() + TTL_SECONDS,
    }


def unregister(session_id: str) -> None:
    _registry.pop(session_id, None)


def lookup(session_id: str) -> dict | None:
    """Return container info or None if expired / not found."""
    entry = _registry.get(session_id)
    if entry is None:
        return None
    if time.time() > entry["expires"]:
        _registry.pop(session_id, None)
        return None
    return entry
