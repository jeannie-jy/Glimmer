"""Unit tests for local-mode API key resolution in the WebSocket bootstrap.

The Settings page stores the key under provider "local", while the chat
bootstrap historically loaded the key named after config.model_provider
(e.g. "openai") — so the chat silently ignored newly saved keys. These tests
pin the resolution order: "local" first, provider name as legacy fallback.
"""

import harness.credentials.manager as cred_module
from harness.credentials import CredentialManager
from harness.models import ConfigData
from server.ws_handler import _resolve_local_api_key


def _isolated_manager(tmp_path, monkeypatch):
    # The OS keyring may hold real credentials on dev machines; file storage
    # is the unit under test here.
    monkeypatch.setattr(cred_module, "keyring", None)
    monkeypatch.delenv("HARNESS_KEY_PASSWORD", raising=False)
    return CredentialManager(tmp_path)


def test_prefers_local_credential_over_provider_file(tmp_path, monkeypatch):
    cm = _isolated_manager(tmp_path, monkeypatch)
    cm.store("local", "sk-local-valid")
    cm.store("openai", "sk-openai-stale")
    assert _resolve_local_api_key(cm, ConfigData(model_provider="openai")) == "sk-local-valid"


def test_falls_back_to_provider_file_when_local_missing(tmp_path, monkeypatch):
    cm = _isolated_manager(tmp_path, monkeypatch)
    cm.store("openai", "sk-openai-stale")
    assert _resolve_local_api_key(cm, ConfigData(model_provider="openai")) == "sk-openai-stale"


def test_returns_none_when_nothing_stored(tmp_path, monkeypatch):
    cm = _isolated_manager(tmp_path, monkeypatch)
    assert _resolve_local_api_key(cm, ConfigData(model_provider="openai")) is None
