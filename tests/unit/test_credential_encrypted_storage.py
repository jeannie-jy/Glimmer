"""Security tests: local credential files are encrypted when a password is set."""
import os

from harness.credentials.manager import CredentialManager


def test_store_with_password_uses_encrypted_file(tmp_path, monkeypatch):
    monkeypatch.setenv("HARNESS_KEY_PASSWORD", "strong-password")
    mgr = CredentialManager(tmp_path)

    mgr.store("anthropic", "sk-secret-value-123")

    enc_file = tmp_path / ".harness" / "credentials" / "anthropic.enc"
    key_file = tmp_path / ".harness" / "credentials" / "anthropic.key"
    assert enc_file.is_file()
    assert not key_file.exists(), "plaintext .key file must not be written when a password is set"
    raw = enc_file.read_bytes()
    assert b"sk-secret-value-123" not in raw, "key must not appear in plaintext in the .enc file"
    assert mgr.load("anthropic") == "sk-secret-value-123"


def test_load_with_wrong_password_returns_none(tmp_path, monkeypatch):
    monkeypatch.setenv("HARNESS_KEY_PASSWORD", "correct-password")
    mgr = CredentialManager(tmp_path)
    mgr.store("anthropic", "sk-secret-value-123")

    monkeypatch.setenv("HARNESS_KEY_PASSWORD", "wrong-password")
    assert mgr.load("anthropic") is None


def test_store_without_password_writes_private_keyfile(tmp_path, monkeypatch):
    monkeypatch.delenv("HARNESS_KEY_PASSWORD", raising=False)
    mgr = CredentialManager(tmp_path)
    mgr.store("anthropic", "sk-plain-123")

    key_file = tmp_path / ".harness" / "credentials" / "anthropic.key"
    assert key_file.read_text() == "sk-plain-123"
    if os.name != "nt":  # Windows permission bits are not comparable
        assert key_file.stat().st_mode & 0o777 == 0o600


def test_delete_removes_encrypted_file(tmp_path, monkeypatch):
    monkeypatch.setenv("HARNESS_KEY_PASSWORD", "strong-password")
    mgr = CredentialManager(tmp_path)
    mgr.store("anthropic", "sk-secret-value-123")
    assert mgr.load("anthropic") == "sk-secret-value-123"

    mgr.delete("anthropic")
    assert mgr.load("anthropic") is None
    assert not (tmp_path / ".harness" / "credentials" / "anthropic.enc").exists()
