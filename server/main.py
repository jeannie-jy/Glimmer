"""FastAPI application entry point for Glimmer."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from server.ws_handler import router as ws_router, configure as configure_ws
from server.api.config_routes import router as config_router, configure as configure_config
from server.api.credential_routes import router as credential_router, configure as configure_credential
from server.api.session_routes import router as session_router
from server.api.auth_routes import router as auth_router

from harness.config import ConfigManager
from harness.credentials import CredentialManager


def create_app(project_root: Path | None = None) -> FastAPI:
    """Build and return a configured FastAPI application.

    Args:
        project_root: Root directory for config / credential resolution.
                      Defaults to ``Path.cwd()``.
    """
    root = project_root or Path.cwd()

    app = FastAPI(title="Glimmer", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Shared services ---
    config_manager = ConfigManager(root)
    credential_manager = CredentialManager(root)

    # --- Wire up sub-routers ---
    configure_config(config_manager, credential_manager)
    configure_credential(config_manager, credential_manager)
    configure_ws(app, config_manager=config_manager, credential_manager=credential_manager)

    app.include_router(ws_router)
    app.include_router(config_router, prefix="/api")
    app.include_router(credential_router, prefix="/api")
    app.include_router(session_router, prefix="/api")
    app.include_router(auth_router, prefix="/api")

    # --- Serve frontend static files in production ---
    static_dir = Path(__file__).parent / "static"
    if static_dir.is_dir():
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

    return app


app = create_app()
