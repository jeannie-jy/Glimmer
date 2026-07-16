"""Tests for CredentialManager mask/status/store/delete."""

import os
from pathlib import Path

import pytest

from harness.credentials.manager import (
    CredentialManager,
    _encrypt,
    _decrypt,
)


@pytest.fixture
def cred_dir(tmp_path: Path) -> Path:
    """Create a temporary project root with .harness/credentials directory."""
    proj = tmp_path / "project"
    (proj / ".harness" / "credentials").mkdir(parents=True)
    return proj


@pytest.fixture
def manager(cred_dir: Path) -> CredentialManager:
    return CredentialManager(cred_dir)


# ------------------------------------------------------------------
# mask()
# ------------------------------------------------------------------


def test_mask_hides_middle_characters(manager: CredentialManager):
    """mask() returns first 3 and last 4 chars separated by '...'."""
    api_key = "sk-ant-api03-abcdefghijklmnopqrstuvwxyz"
    manager.store("anthropic", api_key)
    masked = manager.mask("anthropic")
    assert masked == "sk-" + "..." + "wxyz"
    assert "abcdefghi" not in masked


def test_mask_short_key(manager: CredentialManager):
    """API keys shorter than 8 characters return '****'."""
    manager.store("shorty", "abc123")
    assert manager.mask("shorty") == "****"


def test_mask_missing_key(manager: CredentialManager):
    """mask() returns empty string when no key is stored."""
    assert manager.mask("nonexistent") == ""


# ------------------------------------------------------------------
# status()
# ------------------------------------------------------------------


def test_status_never_returns_plaintext(manager: CredentialManager):
    """status() returns a masked string, never the full plaintext."""
    api_key = "sk-live-abcdefghijklmnopqrstuvwxyz1234"
    manager.store("openai", api_key)
    status = manager.status("openai")
    # Should contain the masked form
    assert "configured" in status
    assert "..." in status
    assert "sk-" in status
    # Should NOT contain the full plaintext
    assert api_key not in status
    assert "abcdefghijklmnopqrstuvwxyz1234" not in status


def test_status_not_configured(manager: CredentialManager):
    """status() returns 'not configured' when no key is stored."""
    assert manager.status("unknown-provider") == "not configured"


# ------------------------------------------------------------------
# store / delete cycle
# ------------------------------------------------------------------


def test_store_and_retrieve(manager: CredentialManager):
    """store() followed by load() returns the original key."""
    api_key = "sk-test-"
    manager.store("test-provider", api_key)
    loaded = manager.load("test-provider")
    assert loaded == api_key


def test_store_and_delete_cycle(manager: CredentialManager):
    """After delete(), status() returns 'not configured'."""
    api_key = "sk-test-delete-key-12345678"
    manager.store("delete-me", api_key)
    assert manager.status("delete-me") != "not configured"  # nosec  # actually it IS configured

    manager.delete("delete-me")
    assert manager.status("delete-me") == "not configured"


def test_delete_twice_is_safe(manager: CredentialManager):
    """Deleting a non-existent credential does not raise."""
    manager.delete("never-existed")  # should not raise


def test_load_missing_returns_none(manager: CredentialManager):
    """load() returns None for a provider with no stored key."""
    assert manager.load("nothing-here") is None


# ------------------------------------------------------------------
# Encrypted file fallback (when keyring is unavailable)
# ------------------------------------------------------------------


def test_encrypt_decrypt_roundtrip(monkeypatch):
    """AES-GCM encrypt/decrypt round-trips correctly."""
    password = "test-password-123"
    plaintext = "sk-test-key-value"
    encrypted = _encrypt(plaintext, password)
    decrypted = _decrypt(encrypted, password)
    assert decrypted == plaintext


def test_encrypt_produces_different_ciphers():
    """Same plaintext and password produce different ciphertexts due to random nonce."""
    password = "test-pw"
    plaintext = "same-key"
    c1 = _encrypt(plaintext, password)
    c2 = _encrypt(plaintext, password)
    assert c1 != c2  # different nonces


def test_file_store_and_load_plain(tmp_path: Path):
    """File-based store/load works without HARNESS_KEY_PASSWORD (plain-text .key files)."""
    proj = tmp_path / "project"
    (proj / ".harness" / "credentials").mkdir(parents=True)

    mgr = CredentialManager(proj)
    mgr.store("test-provider", "test-key-12345")
    loaded = mgr.load("test-provider")
    assert loaded == "test-key-12345"
    assert mgr.mask("test-provider") == "tes...2345"
    mgr.delete("test-provider")
    assert mgr.load("test-provider") is None


def test_file_store_and_load(tmp_path: Path, monkeypatch):
    """File-based store/load round-trips correctly."""
    proj = tmp_path / "project"
    (proj / ".harness" / "credentials").mkdir(parents=True)
    monkeypatch.setenv("HARNESS_KEY_PASSWORD", "strong-password")

    mgr = CredentialManager(proj)
    mgr.store("file-provider", "file-stored-key")
    loaded = mgr.load("file-provider")
    assert loaded == "file-stored-key"


def test_missing_file_returns_none(tmp_path: Path, monkeypatch):
    """load() returns None when no encrypted file exists."""
    proj = tmp_path / "project"
    (proj / ".harness" / "credentials").mkdir(parents=True)
    mgr = CredentialManager(proj)
    assert mgr.load("ghost") is None
