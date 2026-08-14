"""JWT token creation and verification."""
import os
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError

ALGORITHM = "HS256"
EXPIRE_DAYS = 7


def _secret() -> str:
    """Return the JWT signing secret.

    Raises RuntimeError when GLIMMER_SECRET_KEY is not set — signing tokens
    with a hardcoded dev default would let anyone forge tokens.
    """
    secret = os.environ.get("GLIMMER_SECRET_KEY")
    if not secret:
        raise RuntimeError("GLIMMER_SECRET_KEY is not set")
    return secret


def create_token(user_id: str) -> str:
    """Create a signed JWT for a user."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(days=EXPIRE_DAYS),
    }
    return jwt.encode(payload, _secret(), algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    """Verify and decode a JWT. Raises JWTError on failure, RuntimeError when
    no secret is configured."""
    return jwt.decode(token, _secret(), algorithms=[ALGORITHM])


def get_user_id_from_token(token: str) -> str | None:
    """Extract user_id from token, or None if invalid or unverifiable."""
    try:
        payload = verify_token(token)
        return payload.get("sub")
    except (JWTError, RuntimeError):
        return None
