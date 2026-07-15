"""CredentialManager: stores and loads API keys via keyring or AES-GCM encrypted files."""

import os
from pathlib import Path
from typing import Optional

try:
    import keyring  # type: ignore[import-untyped]
    from keyring.errors import KeyringError
except Exception:
    keyring = None  # type: ignore[assignment]
    KeyringError = Exception  # type: ignore[misc]

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    from cryptography.hazmat.primitives import hashes
except ImportError:
    AESGCM = None  # type: ignore[assignment]
    HKDF = None  # type: ignore[assignment]
    hashes = None  # type: ignore[assignment]


SERVICE_NAME = "lite-agent-harness"
CREDENTIALS_DIR = ".harness/credentials"
ENV_PASSWORD_KEY = "HARNESS_KEY_PASSWORD"


def _derive_key(password: str) -> bytes:
    """Derive a 256-bit AES key from *password* using HKDF."""
    if HKDF is None or hashes is None:
        raise RuntimeError("cryptography library is required for encrypted credential storage")
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"lite-agent-harness-credential",
    )
    return hkdf.derive(password.encode("utf-8"))


def _encrypt(plaintext: str, password: str) -> bytes:
    """Encrypt *plaintext* with AES-GCM using a key derived from *password*.

    Returns nonce + ciphertext (concatenated).
    """
    if AESGCM is None:
        raise RuntimeError("cryptography library is required for encrypted credential storage")
    key = _derive_key(password)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return nonce + ct


def _decrypt(data: bytes, password: str) -> str:
    """Decrypt *data* (nonce + ciphertext) with AES-GCM."""
    if AESGCM is None:
        raise RuntimeError("cryptography library is required for encrypted credential storage")
    key = _derive_key(password)
    aesgcm = AESGCM(key)
    nonce = data[:12]
    ct = data[12:]
    plaintext = aesgcm.decrypt(nonce, ct, None)
    return plaintext.decode("utf-8")


class CredentialManager:
    """Manages API key credentials.

    Tries the OS keyring first; falls back to an AES-GCM-encrypted file at
    ``.harness/credentials/{provider}.enc`` (password from ``HARNESS_KEY_PASSWORD``).
    """

    def __init__(self, project_root: Path) -> None:
        self.project_root = Path(project_root).resolve()
        self._cred_dir = self.project_root / CREDENTIALS_DIR
        self._cred_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def store(self, provider: str, api_key: str) -> None:
        """Store an API key for *provider*.

        Uses the OS keyring when available; falls back to an encrypted file.
        """
        if keyring is not None:
            try:
                keyring.set_password(SERVICE_NAME, provider, api_key)
                return
            except KeyringError:
                pass

        self._store_file(provider, api_key)

    def load(self, provider: str) -> Optional[str]:
        """Load the API key for *provider*.

        Returns ``None`` if no key is stored.
        """
        if keyring is not None:
            try:
                val = keyring.get_password(SERVICE_NAME, provider)
                if val is not None:
                    return val
            except KeyringError:
                pass

        return self._load_file(provider)

    def mask(self, provider: str) -> str:
        """Return a masked representation: ``sk-...ab12`` (first 3 + last 4 chars).

        If the API key is fewer than 8 characters it is fully masked as ``****``.
        """
        key = self.load(provider)
        if key is None:
            return ""
        if len(key) < 8:
            return "****"
        return key[:3] + "..." + key[-4:]

    def status(self, provider: str) -> str:
        """Return a human-readable status string.

        Returns ``"configured (sk-...ab12)"`` if a key is stored,
        or ``"not configured"`` otherwise.
        """
        key = self.load(provider)
        if key is None:
            return "not configured"
        return f"configured ({self.mask(provider)})"

    def delete(self, provider: str) -> None:
        """Delete the stored API key for *provider*."""
        if keyring is not None:
            try:
                keyring.delete_password(SERVICE_NAME, provider)
            except KeyringError:
                pass

        # Remove the encrypted file regardless (no-op if missing)
        cred_file = self._cred_dir / f"{provider}.enc"
        if cred_file.is_file():
            cred_file.unlink()

    # ------------------------------------------------------------------
    # File-based fallback
    # ------------------------------------------------------------------

    def _get_password(self) -> str:
        pw = os.environ.get(ENV_PASSWORD_KEY)
        if not pw:
            raise RuntimeError(
                f"{ENV_PASSWORD_KEY} environment variable is not set; "
                f"cannot encrypt/decrypt credential file"
            )
        return pw

    def _store_file(self, provider: str, api_key: str) -> None:
        password = self._get_password()
        encrypted = _encrypt(api_key, password)
        cred_file = self._cred_dir / f"{provider}.enc"
        cred_file.write_bytes(encrypted)

    def _load_file(self, provider: str) -> Optional[str]:
        cred_file = self._cred_dir / f"{provider}.enc"
        if not cred_file.is_file():
            return None
        try:
            password = self._get_password()
            return _decrypt(cred_file.read_bytes(), password)
        except Exception:
            return None
