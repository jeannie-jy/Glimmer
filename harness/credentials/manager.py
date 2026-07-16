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

        Always writes to file; also tries OS keyring for desktop convenience.
        """
        # Always write to file as primary storage
        self._store_file(provider, api_key)

        # Also try keyring (best-effort, may fail silently)
        if keyring is not None:
            try:
                keyring.set_password(SERVICE_NAME, provider, api_key)
            except KeyringError:
                pass

    def load(self, provider: str) -> Optional[str]:
        """Load the API key for *provider*.

        Returns ``None`` if no key is stored. File is the primary source;
        keyring is a best-effort fallback.
        """
        # File is always reliable
        key = self._load_file(provider)
        if key is not None:
            return key

        # Try keyring as fallback
        if keyring is not None:
            try:
                return keyring.get_password(SERVICE_NAME, provider)
            except KeyringError:
                pass

        return None

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

        cred_file = self._cred_dir / f"{provider}.key"
        if cred_file.is_file():
            cred_file.unlink()

    # ------------------------------------------------------------------
    # File-based fallback (simple file, localhost-only tool)
    # ------------------------------------------------------------------

    def _store_file(self, provider: str, api_key: str) -> None:
        cred_file = self._cred_dir / f"{provider}.key"
        cred_file.write_text(api_key, encoding="utf-8")

    def _load_file(self, provider: str) -> Optional[str]:
        cred_file = self._cred_dir / f"{provider}.key"
        if not cred_file.is_file():
            return None
        try:
            return cred_file.read_text(encoding="utf-8").strip()
        except Exception:
            return None
