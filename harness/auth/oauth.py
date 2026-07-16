"""GitHub OAuth integration."""
import os
import httpx

GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", "")
REDIRECT_URI = os.environ.get("OAUTH_REDIRECT_URI", "http://localhost:8000/api/auth/callback")

AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
TOKEN_URL = "https://github.com/login/oauth/access_token"
USER_URL = "https://api.github.com/user"


def get_login_url() -> str:
    return f"{AUTHORIZE_URL}?client_id={GITHUB_CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=user:email"


async def exchange_code(code: str) -> dict | None:
    """Exchange OAuth code for access token, then fetch user info."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            TOKEN_URL,
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": REDIRECT_URI,
            },
            headers={"Accept": "application/json"},
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        access_token = data.get("access_token")
        if not access_token:
            return None

        resp2 = await client.get(
            USER_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if resp2.status_code != 200:
            return None
        user = resp2.json()

        return {
            "id": user["id"],
            "login": user["login"],
            "name": user.get("name") or user["login"],
            "email": user.get("email"),
            "avatar_url": user.get("avatar_url", ""),
        }
