"""FastAPI application entry point for Glimmer."""
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from server.ws_handler import router as ws_router, configure as configure_ws
from server.api.config_routes import router as config_router, configure_fallback
from server.api.session_routes import router as session_router
from server.api.auth_routes import router as auth_router
from server.api.files_routes import router as files_router

from harness.config import ConfigManager
from harness.credentials import CredentialManager

# Local mode detection: when DATABASE_URL is not set, skip DB init and auth
LOCAL_MODE = not os.environ.get("DATABASE_URL")


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
    configure_fallback(config_manager, credential_manager)
    configure_ws(app, config_manager=config_manager, credential_manager=credential_manager)

    app.include_router(ws_router)
    app.include_router(config_router, prefix="/api")
    app.include_router(session_router, prefix="/api")
    app.include_router(auth_router, prefix="/api")
    app.include_router(files_router, prefix="/api")

    # --- Rate limiting ---
    limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # --- Serve frontend static files in production ---
    static_dir = Path(__file__).parent / "static"
    if static_dir.is_dir():
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

    # --- Database init (skipped in local mode) ---
    if not LOCAL_MODE:
        @app.on_event("startup")
        async def startup_db():
            from harness.db.database import init_db
            await init_db()

    return app


app = create_app()
