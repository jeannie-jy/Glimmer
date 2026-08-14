"""Integration tests for static file serving + SPA fallback in server/main.py.

Regression tests for the path traversal vulnerability introduced in a931365:
the SPA fallback joined ``rest_of_path`` onto ``static_dir`` without a
containment check, allowing ``GET /../../<file>`` (or an absolute Windows
path) to read arbitrary files from the server's filesystem.
"""
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from server.main import create_app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(create_app())


def _asset_js_path() -> str:
    """Path of the built JS bundle under /assets, if present."""
    assets = Path(__file__).parents[2] / "server" / "static" / "assets"
    for p in assets.glob("index-*.js"):
        return f"/assets/{p.name}"
    pytest.skip("no built JS bundle in server/static/assets")


class TestSpaServing:
    """Normal serving paths keep working."""

    def test_root_serves_index_html(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]

    def test_client_route_falls_back_to_index(self, client):
        resp = client.get("/about")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]

    def test_real_file_inside_static_is_served(self, client):
        resp = client.get("/favicon.svg")
        assert resp.status_code == 200

    def test_assets_are_served(self, client):
        resp = client.get(_asset_js_path())
        assert resp.status_code == 200
        assert "javascript" in resp.headers["content-type"]


class TestPathTraversalBlocked:
    """A path escaping static_dir must never be served.

    Note: a plain-text ``/../main.py`` never reaches the app — httpx (and
    browsers) normalize dot-segments client-side (verified: the handler sees
    ``/main.py``). The attacks below use percent-encoding, which clients do
    NOT normalize, so they exercise the handler's containment check. Raw
    unnormalized requests are additionally verified against a live uvicorn
    server (see manual verification).
    """

    def test_encoded_dotdot_traversal(self, client):
        resp = client.get("/%2e%2e/main.py")
        assert resp.status_code == 404
        assert "FastAPI application entry point" not in resp.text

    def test_encoded_dotdot_dotenv_traversal(self, client):
        resp = client.get("/%2e%2e/%2e%2e/.env")
        assert resp.status_code == 404
        assert "GITHUB_CLIENT_ID" not in resp.text

    @pytest.mark.skipif(os.name != "nt", reason="backslash is a path separator only on Windows")
    def test_encoded_backslash_traversal(self, client):
        resp = client.get("/%2e%2e%5cmain.py")
        assert resp.status_code == 404
        assert "FastAPI application entry point" not in resp.text

    @pytest.mark.skipif(os.name != "nt", reason="absolute drive path is only special on Windows")
    def test_windows_absolute_path(self, client):
        # On Windows, an absolute path as the right operand of `/` REPLACES
        # the left operand — the containment check must reject it.
        resp = client.get("/C:/Windows/win.ini")
        assert resp.status_code == 404
        assert "[fonts]" not in resp.text


class TestApiNotFound:
    """Unmatched API paths must 404 as JSON, not fall back to the SPA."""

    def test_unknown_api_route_returns_404_json(self, client):
        resp = client.get("/api/does-not-exist")
        assert resp.status_code == 404
        assert "application/json" in resp.headers["content-type"]
