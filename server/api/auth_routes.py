"""Authentication routes — GitHub OAuth login."""
import os
import uuid
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from harness.db.database import get_db, get_db_optional
from harness.db.models import User
from harness.auth.oauth import get_login_url, exchange_code
from harness.auth.jwt import create_token, get_user_id_from_token

router = APIRouter(tags=["auth"])
_security = HTTPBearer(auto_error=False)


# Canonical user id of the synthetic local-mode user. Sessions registered by
# the WS handler in local mode use this id so ownership checks stay uniform.
LOCAL_USER_ID = str(uuid.UUID(int=0))


def _local_user() -> User:
    """Synthetic detached user for local mode (no DATABASE_URL)."""
    return User(
        id=uuid.UUID(int=0),
        github_id=0,
        login="local-user",
        name="Local Mode",
        avatar_url=None,
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_security),
    db: AsyncSession | None = Depends(get_db_optional),
) -> User:
    """Dependency: extract JWT, return User or raise 401.

    In local mode the DB dependency yields None and a synthetic user is
    returned without any token requirement — the db-None check must come
    BEFORE token validation so local mode never demands a token.
    """
    if db is None:
        return _local_user()

    if credentials is None:
        raise HTTPException(401, "Authorization header required")
    user_id = get_user_id_from_token(credentials.credentials)
    if not user_id:
        raise HTTPException(401, "Invalid or expired token")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(401, "User not found")
    return user


@router.get("/auth/mode")
async def auth_mode():
    """Report whether the server runs in local (single-user, no DB) mode."""
    return {"local": not os.environ.get("DATABASE_URL")}


@router.get("/auth/login")
async def login():
    """Redirect user to GitHub for authentication."""
    url = get_login_url()
    if not url:
        raise HTTPException(500, "GitHub OAuth not configured (GITHUB_CLIENT_ID missing)")
    return RedirectResponse(url)


@router.get("/auth/callback")
async def callback(code: str, db: AsyncSession = Depends(get_db)):
    """Handle GitHub OAuth callback. Returns JWT token."""
    user_info = await exchange_code(code)
    if user_info is None:
        raise HTTPException(400, "GitHub authentication failed")

    result = await db.execute(select(User).where(User.github_id == user_info["id"]))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            github_id=user_info["id"],
            login=user_info["login"],
            name=user_info["name"],
            email=user_info["email"],
            avatar_url=user_info["avatar_url"],
        )
        db.add(user)
        await db.flush()
    else:
        user.login = user_info["login"]
        user.name = user_info["name"]
        user.email = user_info["email"]
        user.avatar_url = user_info["avatar_url"]

    token = create_token(str(user.id))
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost")
    params = urlencode({"token": token})
    return RedirectResponse(f"{frontend_url}/?{params}")


@router.get("/auth/me")
async def me(user: User = Depends(get_current_user)):
    """Return current authenticated user info."""
    return {
        "id": str(user.id),
        "login": user.login,
        "name": user.name,
        "email": user.email,
        "avatar_url": user.avatar_url,
    }
