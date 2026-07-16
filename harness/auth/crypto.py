"""AES-256-GCM encryption for API keys at rest."""
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

_SECRET = os.environ.get("GLIMMER_SECRET_KEY", "dev-secret-change-me")


def _derive_key() -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b"glimmer-creds").derive(_SECRET.encode())


def encrypt_credential(plaintext: str) -> bytes:
    key = _derive_key()
    nonce = os.urandom(12)
    ct = AESGCM(key).encrypt(nonce, plaintext.encode(), None)
    return nonce + ct


def decrypt_credential(data: bytes) -> str | None:
    try:
        key = _derive_key()
        return AESGCM(key).decrypt(data[:12], data[12:], None).decode()
    except Exception:
        return None
