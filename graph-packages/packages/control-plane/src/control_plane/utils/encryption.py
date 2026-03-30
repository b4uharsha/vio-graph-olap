"""Fernet-based symmetric encryption for data source credentials.

Key sourced from env var GRAPH_OLAP_ENCRYPTION_KEY (base64-url-safe-encoded 32-byte key).
Falls back to a deterministic key derived from GRAPH_OLAP_INTERNAL_API_KEY if not set.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os

from cryptography.fernet import Fernet


def _get_key() -> bytes:
    """Return the Fernet-compatible encryption key.

    Prefers GRAPH_OLAP_ENCRYPTION_KEY (must be a url-safe-base64-encoded 32-byte key).
    Falls back to a SHA-256 derivation of the internal API key.
    """
    explicit_key = os.environ.get("GRAPH_OLAP_ENCRYPTION_KEY")
    if explicit_key:
        # Caller is expected to supply a valid Fernet key (url-safe base64 of 32 bytes)
        return explicit_key.encode()

    # Fallback: derive from internal API key
    api_key = os.environ.get("GRAPH_OLAP_INTERNAL_API_KEY", "default-dev-key")
    derived = hashlib.sha256(api_key.encode()).digest()
    return base64.urlsafe_b64encode(derived)


def encrypt_credentials(plaintext: dict) -> str:
    """Encrypt a dict of credentials to a Fernet token string."""
    f = Fernet(_get_key())
    return f.encrypt(json.dumps(plaintext).encode()).decode()


def decrypt_credentials(ciphertext: str) -> dict:
    """Decrypt a Fernet token string back to a dict of credentials."""
    f = Fernet(_get_key())
    return json.loads(f.decrypt(ciphertext.encode()).decode())


def mask_credentials(credentials: dict) -> dict:
    """Return a masked copy of credentials suitable for API responses.

    Shows the first two and last two characters of string values longer than 4 chars;
    everything else is replaced with ``****``.
    """
    masked: dict[str, str] = {}
    for key, value in credentials.items():
        if isinstance(value, str) and len(value) > 4:
            masked[key] = value[:2] + "*" * (len(value) - 4) + value[-2:]
        else:
            masked[key] = "****"
    return masked
