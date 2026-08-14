"""DELETE /api/sessions/{session_id} endpoint tests (history deletion).

The route is DB-backed and the suite has no real-database fixtures, so the
AsyncSession dependency is overridden with a stub that records what the route
deletes. This pins the contract the sidebar delete relies on: deletion is
scoped to the current user, unknown sessions 404, and success reports ok.
"""
import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from harness.db.database import get_db_optional
from harness.db.models import Session as DBSession, User
from server.api.auth_routes import get_current_user
from server.api.session_routes import router as session_router


class _FakeDb:
    """AsyncSession stub for the route's execute/delete/flush calls."""

    def __init__(self, found: DBSession | None):
        self._found = found
        self.deleted: list[DBSession] = []

    async def execute(self, stmt):
        return self

    def scalar_one_or_none(self):
        return self._found

    async def delete(self, obj):
        self.deleted.append(obj)

    async def flush(self):
        pass


def _make_app(db: _FakeDb | None, monkeypatch) -> FastAPI:
    if db is not None:
        # The route only talks to the DB when DATABASE_URL is configured.
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
    else:
        monkeypatch.delenv("DATABASE_URL", raising=False)
    app = FastAPI()
    app.include_router(session_router, prefix="/api")
    app.dependency_overrides[get_current_user] = lambda: User(
        id=uuid.uuid4(), github_id=1, login="test"
    )
    app.dependency_overrides[get_db_optional] = lambda: db
    return app


def _db_session() -> DBSession:
    return DBSession(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        task="fix the bug",
        status="completed",
    )


class TestDeleteSession:
    def test_delete_existing_session_reports_ok(self, monkeypatch):
        session = _db_session()
        db = _FakeDb(session)
        app = _make_app(db, monkeypatch)

        resp = TestClient(app).delete(f"/api/sessions/{session.id}")

        assert resp.status_code == 200
        assert resp.json() == {"status": "ok", "deleted": True}
        # The route deletes exactly the session it looked up (scoped by user).
        assert db.deleted == [session]

    def test_delete_unknown_session_returns_404(self, monkeypatch):
        db = _FakeDb(None)
        app = _make_app(db, monkeypatch)

        resp = TestClient(app).delete(f"/api/sessions/{uuid.uuid4()}")

        assert resp.status_code == 404
        assert db.deleted == []

    def test_delete_in_local_mode_returns_404(self, monkeypatch):
        app = _make_app(None, monkeypatch)

        resp = TestClient(app).delete(f"/api/sessions/{uuid.uuid4()}")

        assert resp.status_code == 404
