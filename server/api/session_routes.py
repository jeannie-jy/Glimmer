"""REST endpoints for session history."""
import os
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from harness.db.database import get_db
from harness.db.models import User, Session
from server.api.auth_routes import get_current_user

router = APIRouter(tags=["session"])


@router.get("/sessions")
async def list_sessions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return current user's past sessions (most recent first, max 50)."""
    if not os.environ.get("DATABASE_URL"):
        return {"sessions": []}

    result = await db.execute(
        select(Session)
        .where(Session.user_id == user.id)
        .order_by(Session.created_at.desc())
        .limit(50)
    )
    sessions = result.scalars().all()
    return {
        "sessions": [
            {
                "id": str(s.id),
                "task": s.task,
                "state": s.status,
                "status": s.status,
                "created_at": s.created_at.isoformat() if s.created_at else "",
            }
            for s in sessions
        ]
    }


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return a single session with all its messages."""
    if not os.environ.get("DATABASE_URL"):
        raise HTTPException(404, "Session not found")

    result = await db.execute(
        select(Session).where(Session.id == session_id, Session.user_id == user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Session not found")

    messages = session.messages or []
    return {
        "id": str(session.id),
        "task": session.task,
        "status": session.status,
        "created_at": session.created_at.isoformat() if session.created_at else "",
        "messages": [
            {"type": m.type, "payload": m.payload, "created_at": m.created_at.isoformat() if m.created_at else ""}
            for m in messages
        ],
    }


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a session (and its messages via cascade)."""
    if not os.environ.get("DATABASE_URL"):
        raise HTTPException(404, "Session not found")

    result = await db.execute(
        select(Session).where(Session.id == session_id, Session.user_id == user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Session not found")

    await db.delete(session)
    await db.flush()
    return {"status": "ok", "deleted": True}
