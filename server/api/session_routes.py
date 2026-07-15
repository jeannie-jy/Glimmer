"""REST endpoints for session history."""
from fastapi import APIRouter

router = APIRouter(tags=["session"])


@router.get("/session/history")
async def session_history() -> dict:
    """Return a list of past sessions.

    .. note::
       Persistent session storage is not yet implemented.
       Returns an empty list as a stub.
    """
    return {"sessions": []}
