"""Rate-limiting tests: mutation endpoints are throttled per client.

Before the fix, create_app() created a Limiter and stored it on app.state but
NO route was decorated with it — the limits never applied to anything.
"""
from fastapi.testclient import TestClient

from server.main import create_app


def _client(monkeypatch, tmp_path) -> TestClient:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    return TestClient(create_app(project_root=tmp_path))


def test_credentials_post_throttled_after_10(monkeypatch, tmp_path):
    """POST /api/credentials allows 10 writes per minute, then 429s."""
    client = _client(monkeypatch, tmp_path)
    for i in range(10):
        resp = client.post(
            "/api/credentials",
            json={"provider": "anthropic", "api_key": "sk-test"},
        )
        assert resp.status_code == 200, f"request {i + 1}: {resp.status_code} {resp.text}"

    resp = client.post(
        "/api/credentials",
        json={"provider": "anthropic", "api_key": "sk-test"},
    )
    assert resp.status_code == 429, f"expected 429, got {resp.status_code} {resp.text}"


def test_config_put_throttled_after_30(monkeypatch, tmp_path):
    """PUT /api/config allows 30 writes per minute, then 429s."""
    client = _client(monkeypatch, tmp_path)
    for i in range(30):
        resp = client.put("/api/config", json={"model_provider": "anthropic"})
        assert resp.status_code == 200, f"request {i + 1}: {resp.status_code} {resp.text}"

    resp = client.put("/api/config", json={"model_provider": "anthropic"})
    assert resp.status_code == 429, f"expected 429, got {resp.status_code} {resp.text}"
