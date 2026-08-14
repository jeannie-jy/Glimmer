"""Tests for local mode (no DATABASE_URL) REST accessibility.

Regression tests for the integration break where /api/config, /api/sessions
and /api/auth/* resolved their DB/auth dependencies BEFORE their local-mode
branches ran, so every REST call 500'd/401'd in local mode — making the
Settings panel, History sidebar and the Agent page (via ProtectedRoute)
unreachable under `make dev`.
"""
import pytest
from fastapi.testclient import TestClient

from server.main import create_app


@pytest.fixture()
def client(monkeypatch, tmp_path) -> TestClient:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    # project_root=tmp_path keeps local-mode config/credential writes
    # (.harness/config.yaml etc.) out of the repository.
    return TestClient(create_app(project_root=tmp_path))


def test_auth_mode_reports_local(client):
    resp = client.get("/api/auth/mode")
    assert resp.status_code == 200
    assert resp.json() == {"local": True}


def test_config_accessible_without_token(client):
    resp = client.get("/api/config")
    assert resp.status_code == 200, resp.text
    assert "model_provider" in resp.json()


def test_config_update_accessible_without_token(client):
    resp = client.put("/api/config", json={"model_id": "test-model"})
    assert resp.status_code == 200, resp.text


def test_credentials_roundtrip_without_token(client):
    resp = client.post("/api/credentials", json={"provider": "local", "api_key": "sk-test-123"})
    assert resp.status_code == 200, resp.text

    resp = client.get("/api/credentials/status")
    assert resp.status_code == 200
    assert resp.json()["providers"].get("local") == "set"


def test_sessions_list_empty_without_token(client):
    resp = client.get("/api/sessions")
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"sessions": []}


def test_auth_me_returns_local_user_without_token(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["login"] == "local-user"
