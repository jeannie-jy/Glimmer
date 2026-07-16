"""REST endpoints for harness configuration."""
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from harness.config import ConfigManager
from harness.credentials import CredentialManager

router = APIRouter(tags=["config"])

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

class ConfigUpdate(BaseModel):
    """Partial config update payload."""
    model_provider: str | None = None
    model_id: str | None = None
    base_url: str | None = None
    max_tokens: int | None = None
    max_retries: int | None = None
    sandbox_root: str | None = None
    command_whitelist_extra: list[str] | None = None
    timeout_seconds: int | None = None
    enabled_tools: list[str] | None = None
    max_context_tokens: int | None = None
    learnings_limit: int | None = None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/config")
async def get_config() -> dict:
    """Return the current configuration (credential values masked)."""
    if _config_manager is None:
        raise HTTPException(status_code=503, detail="Server not fully initialised")

    config = _config_manager.load()
    data = config.model_dump()

    # Mask any credential-like fields
    if "api_key" in data:
        data["api_key"] = _mask_key(data["api_key"])
    if "api_key" in data.get("model", {}):
        data["model"]["api_key"] = _mask_key(data["model"]["api_key"])

    return data


@router.put("/config")
async def update_config(update: ConfigUpdate) -> dict:
    """Update the project-level configuration file.

    Only the fields provided in the request body are changed; missing fields
    keep their current value.
    """
    if _config_manager is None:
        raise HTTPException(status_code=503, detail="Server not fully initialised")

    current = _config_manager.load()
    updates = update.model_dump(exclude_none=True)

    # Replace whitelist_extra entirely (not append — prevents unbounded growth)

    # Write merged config to project config file
    project_cfg = _config_manager.project_root / ConfigManager.PROJECT_CONFIG_PATH
    project_cfg.parent.mkdir(parents=True, exist_ok=True)

    merged = current.model_copy(update=updates)

    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:
        raise HTTPException(status_code=500, detail="PyYAML is required for config writes")

    with open(project_cfg, "w", encoding="utf-8") as fh:
        yaml.dump(merged.model_dump(), fh, default_flow_style=False)

    return {"status": "ok", "config": merged.model_dump()}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mask_key(key: str) -> str:
    if not key or len(key) < 8:
        return "****"
    return key[:3] + "..." + key[-4:]
