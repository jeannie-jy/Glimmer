"""Per-user configuration REST endpoints."""
import os
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from harness.db.database import get_db
from harness.db.models import User, UserConfig
from server.api.auth_routes import get_current_user
from harness.auth.crypto import encrypt_credential, decrypt_credential
from harness.models import ConfigData

router = APIRouter(tags=["config"])

# Fallback for local mode (no DATABASE_URL) -- set from main.py
_fallback_config_manager = None
_fallback_credential_manager = None


def configure_fallback(config_mgr, cred_mgr):
    global _fallback_config_manager, _fallback_credential_manager
    _fallback_config_manager = config_mgr
    _fallback_credential_manager = cred_mgr


class ConfigUpdate(BaseModel):
    provider: str | None = None
    model_provider: str | None = None
    base_url: str | None = None
    model_id: str | None = None
    max_tokens: int | None = None
    max_retries: int | None = None
    timeout_seconds: int | None = None

class CredentialStore(BaseModel):
    provider: str | None = None
    api_key: str


# ---- Local mode helpers ----
def _is_local() -> bool:
    return not os.environ.get("DATABASE_URL")


@router.get("/config")
async def get_config(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if _is_local() and _fallback_config_manager:
        cfg = _fallback_config_manager.load()
        return cfg.model_dump()

    result = await db.execute(select(UserConfig).where(UserConfig.user_id == user.id))
    cfg = result.scalar_one_or_none()
    if cfg is None:
        cfg = UserConfig(user_id=user.id)
        db.add(cfg)
        await db.flush()

    return {
        "provider": cfg.provider,
        "model_provider": cfg.provider or "anthropic",
        "base_url": cfg.base_url or "",
        "model_id": cfg.model_id,
        "max_tokens": cfg.max_tokens,
        "max_retries": cfg.max_retries,
        "timeout_seconds": cfg.timeout_seconds,
        "model_provider": cfg.provider,
        "has_api_key": bool(cfg.api_key_enc),
        "command_whitelist_extra": [],
        "sandbox_root": ".",
        "enabled_tools": ["read_file", "write_file", "execute_shell", "run_tests", "search_code"],
        "max_context_tokens": 8000,
        "learnings_limit": 20,
    }


@router.put("/config")
async def update_config(
    update: ConfigUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if _is_local() and _fallback_config_manager:
        # Local mode: write to yaml file
        from harness.models import ConfigData
        current = _fallback_config_manager.load()
        for k, v in update.model_dump(exclude_none=True).items():
            if hasattr(current, k) and v is not None:
                setattr(current, k, v)
        import yaml
        project_cfg = _fallback_config_manager.project_root / ".harness" / "config.yaml"
        project_cfg.parent.mkdir(parents=True, exist_ok=True)
        with open(project_cfg, "w") as fh:
            yaml.dump(current.model_dump(), fh, default_flow_style=False)
        return {"status": "ok", "config": current.model_dump()}

    result = await db.execute(select(UserConfig).where(UserConfig.user_id == user.id))
    cfg = result.scalar_one_or_none()
    if cfg is None:
        cfg = UserConfig(user_id=user.id)
        db.add(cfg)

    update_data = update.model_dump(exclude_none=True)
    # Accept both "provider" and "model_provider" (frontend uses model_provider)
    provider_val = update_data.get("model_provider") or update_data.get("provider")
    if provider_val:
        cfg.provider = provider_val
    if "base_url" in update_data:
        cfg.base_url = update_data["base_url"]
    if "model_id" in update_data:
        cfg.model_id = update_data["model_id"]
    if "max_tokens" in update_data:
        cfg.max_tokens = update_data["max_tokens"]
    if "max_retries" in update_data:
        cfg.max_retries = update_data["max_retries"]
    if "timeout_seconds" in update_data:
        cfg.timeout_seconds = update_data["timeout_seconds"]

    await db.flush()
    return {"status": "ok"}


@router.post("/config/credentials")
async def store_credential(
    body: CredentialStore,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Store encrypted API key for current user."""
    if _is_local() and _fallback_credential_manager:
        _fallback_credential_manager.store("local", body.api_key)
        return {"status": "ok"}

    result = await db.execute(select(UserConfig).where(UserConfig.user_id == user.id))
    cfg = result.scalar_one_or_none()
    if cfg is None:
        cfg = UserConfig(user_id=user.id)
        db.add(cfg)

    encrypted = encrypt_credential(body.api_key)
    cfg.api_key_enc = encrypted.hex()
    await db.flush()
    return {"status": "ok"}


@router.delete("/config/credentials")
async def delete_credential(
    provider: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete stored API key for current user."""
    del provider  # single-provider for now
    if _is_local() and _fallback_credential_manager:
        _fallback_credential_manager.delete("local")
        return {"status": "ok"}

    result = await db.execute(select(UserConfig).where(UserConfig.user_id == user.id))
    cfg = result.scalar_one_or_none()
    if cfg:
        cfg.api_key_enc = None
        await db.flush()
    return {"status": "ok"}


# ---- Frontend-compatible credential routes (matching api.ts) ----

@router.get("/credentials/status")
async def credentials_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return credential status per provider (frontend-compatible)."""
    if _is_local() and _fallback_credential_manager:
        local_key = _fallback_credential_manager.load("local")
        return {"providers": {"local": "set" if local_key else "unset"}}

    result = await db.execute(select(UserConfig).where(UserConfig.user_id == user.id))
    cfg = result.scalar_one_or_none()
    providers = {}
    # Detect providers based on user config
    if cfg and cfg.api_key_enc:
        provider_name = cfg.provider or "anthropic"
        providers[provider_name] = "set"
    return {"providers": providers}


@router.post("/credentials")
async def store_credential_frontend(
    body: CredentialStore,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Store encrypted API key (frontend-compatible)."""
    if _is_local() and _fallback_credential_manager:
        _fallback_credential_manager.store("local", body.api_key)
        return {"status": "ok"}

    result = await db.execute(select(UserConfig).where(UserConfig.user_id == user.id))
    cfg = result.scalar_one_or_none()
    if cfg is None:
        cfg = UserConfig(user_id=user.id)
        db.add(cfg)

    encrypted = encrypt_credential(body.api_key)
    cfg.api_key_enc = encrypted.hex()
    await db.flush()
    return {"status": "ok"}


@router.delete("/credentials/{provider}")
async def delete_credential_frontend(
    provider: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete stored API key (frontend-compatible)."""
    del provider
    if _is_local() and _fallback_credential_manager:
        _fallback_credential_manager.delete("local")
        return {"status": "ok"}

    result = await db.execute(select(UserConfig).where(UserConfig.user_id == user.id))
    cfg = result.scalar_one_or_none()
    if cfg:
        cfg.api_key_enc = None
        await db.flush()
    return {"status": "ok"}


async def get_user_config(user: User, db: AsyncSession) -> ConfigData | None:
    """Helper: fetch user's config as ConfigData model (used by WebSocket handler)."""
    if _is_local() and _fallback_config_manager:
        cfg = _fallback_config_manager.load()
        return cfg

    result = await db.execute(select(UserConfig).where(UserConfig.user_id == user.id))
    cfg = result.scalar_one_or_none()
    if cfg is None:
        return None
    return ConfigData(
        model_provider=cfg.provider,
        model_id=cfg.model_id,
        base_url=cfg.base_url or "",
        max_tokens=cfg.max_tokens,
        max_retries=cfg.max_retries,
        timeout_seconds=cfg.timeout_seconds,
    )


async def get_user_api_key(user: User, db: AsyncSession) -> str | None:
    """Helper: fetch and decrypt user's API key (used by WebSocket handler)."""
    if _is_local() and _fallback_credential_manager:
        return _fallback_credential_manager.load("local")

    result = await db.execute(select(UserConfig).where(UserConfig.user_id == user.id))
    cfg = result.scalar_one_or_none()
    if cfg is None or not cfg.api_key_enc:
        return None
    return decrypt_credential(bytes.fromhex(cfg.api_key_enc))
