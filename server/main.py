"""FastAPI application entry point for Glimmer."""
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from server.rate_limit import limiter
from server.ws_handler import router as ws_router, configure as configure_ws
from server.api.config_routes import router as config_router, configure_fallback
from server.api.session_routes import router as session_router
from server.api.auth_routes import router as auth_router
from server.api.files_routes import router as files_router

from harness.config import ConfigManager
from harness.credentials import CredentialManager


def create_app(project_root: Path | None = None) -> FastAPI:
    """Build and return a configured FastAPI application.

    Args:
        project_root: Root directory for config / credential resolution.
                      Defaults to ``Path.cwd()``.
    """
    root = project_root or Path.cwd()

    # Local mode detection: when DATABASE_URL is not set, skip DB init and auth.
    # Evaluated per call (not at import time) so tests can toggle the env var.
    LOCAL_MODE = not os.environ.get("DATABASE_URL")

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
    # Shared limiter instance (server/rate_limit.py) — routes decorate their
    # endpoints with @limiter.limit(...). slowapi enforces through this
    # instance's in-memory storage, which we reset so every app (including
    # test apps) starts with a clean slate.
    limiter.reset()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # --- Serve frontend static files in production ---
    static_dir = Path(__file__).parent / "static"
    if static_dir.is_dir():
        # Serve static assets (JS, CSS, favicon, etc.) at their exact paths
        app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")

        static_root = static_dir.resolve()

        # SPA fallback: serve index.html for all unmatched non-API paths
        @app.get("/{rest_of_path:path}")
        async def spa_fallback(rest_of_path: str):
            # Unmatched API/WS paths must 404, not fall back to the SPA
            if rest_of_path in ("api", "ws") or rest_of_path.startswith(("api/", "ws/")):
                return JSONResponse({"detail": "Not Found"}, status_code=404)

            # Serve real files inside static_dir (e.g. favicon.svg). The
            # resolve() + is_relative_to() check blocks ../ traversal and
            # absolute-path escapes (which would replace the base path).
            candidate = (static_root / rest_of_path).resolve()
            if not candidate.is_relative_to(static_root):
                return JSONResponse({"detail": "Not Found"}, status_code=404)
            if candidate.is_file():
                return FileResponse(candidate)

            # SPA fallback — let React Router handle client-side routes
            index_path = static_root / "index.html"
            if index_path.is_file():
                return FileResponse(index_path)
            return JSONResponse({"detail": "Not Found"}, status_code=404)

    # --- Database init (skipped in local mode) ---
    if not LOCAL_MODE:
        @app.on_event("startup")
        async def startup_db():
            from harness.db.database import init_db
            await init_db()

    return app


app = create_app()
