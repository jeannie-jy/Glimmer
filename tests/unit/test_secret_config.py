"""Security tests: GLIMMER_SECRET_KEY must never fall back to a hardcoded default."""
import pytest

from harness.auth.jwt import create_token, get_user_id_from_token, verify_token
from harness.auth.crypto import encrypt_credential


@pytest.fixture()
def no_secret(monkeypatch):
    monkeypatch.delenv("GLIMMER_SECRET_KEY", raising=False)


def test_create_token_requires_secret(no_secret):
    """Minting JWTs with the insecure dev default must fail loudly."""
    with pytest.raises(RuntimeError):
        create_token("some-user-id")


def test_verify_token_requires_secret(no_secret):
    with pytest.raises(RuntimeError):
        verify_token("not-a-real-token")


def test_get_user_id_returns_none_without_secret(no_secret):
    """Token extraction must degrade gracefully (used by local-mode WS)."""
    assert get_user_id_from_token("whatever") is None


def test_encrypt_credential_requires_secret(no_secret):
    """Encrypting API keys with the insecure dev default must fail loudly."""
    with pytest.raises(RuntimeError):
        encrypt_credential("sk-test-key")


def test_token_roundtrip_with_secret(monkeypatch):
    """With a real secret, tokens mint and verify normally."""
    monkeypatch.setenv("GLIMMER_SECRET_KEY", "x" * 64)
    token = create_token("user-123")
    assert get_user_id_from_token(token) == "user-123"
