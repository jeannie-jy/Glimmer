"""JWT token creation and verification."""
import os
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError

SECRET_KEY = os.environ.get("GLIMMER_SECRET_KEY", "dev-secret-change-me")
ALGORITHM = "HS256"
EXPIRE_DAYS = 7


def create_token(user_id: str) -> str:
    """Create a signed JWT for a user."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(days=EXPIRE_DAYS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    """Verify and decode a JWT. Raises JWTError on failure."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def get_user_id_from_token(token: str) -> str | None:
    """Extract user_id from token, or None if invalid."""
    try:
        payload = verify_token(token)
        return payload.get("sub")
    except JWTError:
        return None
