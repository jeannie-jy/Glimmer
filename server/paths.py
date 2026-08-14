"""Sandbox path resolution shared by the WS and REST file handlers.

posixpath is used throughout because these paths are resolved against the
Linux container filesystem regardless of the host platform.
"""
import posixpath


def container_path(rel: str) -> str | None:
    """Resolve a client-supplied path inside the container /workspace.

    Returns None when the path escapes the workspace (traversal or absolute).
    """
    clean = rel.lstrip("/")
    if clean.startswith("workspace/"):
        clean = clean[len("workspace/"):]
    safe = posixpath.normpath(posixpath.join("/workspace", clean))
    if not safe.startswith("/workspace/"):
        return None
    return safe
