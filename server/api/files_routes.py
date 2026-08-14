"""REST endpoints for browsing and downloading session workspace files."""
import os
import shlex
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from harness.db.models import User
from server.api.auth_routes import get_current_user
from server.paths import container_path
from server.session_registry import lookup

router = APIRouter(tags=["files"])


def _check_owner(entry: dict, user: User) -> None:
    """403 when the session belongs to a different user (IDOR guard)."""
    if entry.get("user_id") != str(user.id):
        raise HTTPException(403, "Session belongs to another user")


@router.get("/files")
async def list_files(
    session_id: str = Query(..., description="Session ID"),
    user: User = Depends(get_current_user),
):
    """List files in the session's workspace container."""
    entry = lookup(session_id)
    if entry is None:
        raise HTTPException(404, "Session not found or expired")
    _check_owner(entry, user)

    docker_mgr = entry["docker_mgr"]
    container_id = entry["container_id"]

    if docker_mgr is None or container_id is None:
        return {"session_id": session_id, "files": [], "mode": "local"}

    try:
        # Use find to list files with sizes and modification times
        result = await docker_mgr.exec(
            container_id,
            "find /workspace -type f -printf '%p\t%s\t%TY-%Tm-%TdT%TH:%TM\n' 2>/dev/null",
            timeout=10,
        )
        files = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) >= 3:
                path = parts[0].replace("/workspace/", "", 1)
                if path == "/workspace" or not path:
                    continue
                files.append({
                    "name": path,
                    "size": int(parts[1]),
                    "modified": parts[2],
                })

        # Sort: directories first (grouped by path), then by name
        files.sort(key=lambda f: (os.path.dirname(f["name"]), f["name"]))
        return {"session_id": session_id, "files": files}
    except Exception as e:
        return {"session_id": session_id, "files": [], "error": str(e)}


@router.get("/files/download")
async def download_file(
    session_id: str = Query(...),
    path: str = Query(...),
    user: User = Depends(get_current_user),
):
    """Download a file from the session's workspace."""
    entry = lookup(session_id)
    if entry is None:
        raise HTTPException(404, "Session not found or expired")
    _check_owner(entry, user)

    docker_mgr = entry["docker_mgr"]
    container_id = entry["container_id"]

    if docker_mgr is None or container_id is None:
        raise HTTPException(404, "No sandbox container for this session")

    # Resolve against the CONTAINER filesystem (posix) — host os.path would
    # mis-resolve on Windows and normpath alone cannot stop traversal.
    safe_path = container_path(path)
    if safe_path is None:
        raise HTTPException(400, "Invalid file path")

    try:
        # The path is passed as a single quoted argument so shell
        # metacharacters in it are inert.
        result = await docker_mgr.exec(
            container_id,
            f"cat {shlex.quote(safe_path)}",
            timeout=10,
        )
        if result.exit_code != 0:
            raise HTTPException(404, f"File not found: {path}")

        filename = os.path.basename(path)
        return StreamingResponse(
            iter([result.stdout]),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))
