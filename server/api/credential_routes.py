"""REST endpoints for credential management."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from harness.config import ConfigManager
from harness.credentials import CredentialManager

router = APIRouter(tags=["credentials"])

# Shared references — set from main.py via configure()
_config_manager: ConfigManager | None = None
_credential_manager: CredentialManager | None = None


def configure(config_manager: ConfigManager, credential_manager: CredentialManager) -> None:
    """Inject shared service instances (called at startup)."""
    global _config_manager, _credential_manager
    _config_manager = config_manager
    _credential_manager = credential_manager


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class CredentialStore(BaseModel):
    """Payload for storing an API key."""
    provider: str
    api_key: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/credentials/status")
async def credentials_status() -> dict:
    """Return the status of all known credential providers (masked)."""
    if _credential_manager is None:
        raise HTTPException(status_code=503, detail="Server not fully initialised")

    providers = ["anthropic", "openai"]
    statuses = {}
    for prov in providers:
        masked = _credential_manager.mask(prov)
        if masked:
            statuses[prov] = f"configured ({masked})"
        else:
            statuses[prov] = "not configured"

    return {"providers": statuses}


@router.post("/credentials")
async def store_credential(body: CredentialStore) -> dict:
    """Store an API key for the given provider."""
    if _credential_manager is None:
        raise HTTPException(status_code=503, detail="Server not fully initialised")

    _credential_manager.store(body.provider, body.api_key)
    return {"status": "ok", "provider": body.provider}


@router.delete("/credentials/{provider}")
async def delete_credential(provider: str) -> dict:
    """Delete the stored API key for a provider."""
    if _credential_manager is None:
        raise HTTPException(status_code=503, detail="Server not fully initialised")

    _credential_manager.delete(provider)
    return {"status": "ok", "provider": provider, "deleted": True}
