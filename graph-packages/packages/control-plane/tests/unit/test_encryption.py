"""Unit tests for credential encryption utilities."""

from __future__ import annotations

import os
from unittest import mock

import pytest
from cryptography.fernet import Fernet, InvalidToken

from control_plane.utils.encryption import (
    _get_key,
    decrypt_credentials,
    encrypt_credentials,
    mask_credentials,
)


class TestEncryptDecryptRoundTrip:
    """Encrypt then decrypt should return the original data."""

    def test_simple_dict(self):
        creds = {"username": "admin", "password": "s3cret!"}
        token = encrypt_credentials(creds)
        assert decrypt_credentials(token) == creds

    def test_empty_dict(self):
        creds: dict = {}
        assert decrypt_credentials(encrypt_credentials(creds)) == creds

    def test_nested_values(self):
        creds = {"host": "db.example.com", "port": 5432, "ssl": True}
        assert decrypt_credentials(encrypt_credentials(creds)) == creds

    def test_unicode_values(self):
        creds = {"password": "p@$$w0rd-\u00e9\u00e8\u00ea"}
        assert decrypt_credentials(encrypt_credentials(creds)) == creds


class TestDecryptWithWrongKey:
    """Decryption with a different key should fail."""

    def test_wrong_key_raises(self):
        creds = {"password": "secret"}
        token = encrypt_credentials(creds)

        different_key = Fernet.generate_key().decode()
        with mock.patch.dict(os.environ, {"GRAPH_OLAP_ENCRYPTION_KEY": different_key}):
            with pytest.raises(InvalidToken):
                decrypt_credentials(token)


class TestKeyDerivationFallback:
    """When GRAPH_OLAP_ENCRYPTION_KEY is not set, derive from internal API key."""

    def test_fallback_uses_internal_api_key(self):
        env = {
            "GRAPH_OLAP_INTERNAL_API_KEY": "my-secret-api-key",
        }
        with mock.patch.dict(os.environ, env, clear=False):
            # Remove encryption key if present
            os.environ.pop("GRAPH_OLAP_ENCRYPTION_KEY", None)
            key = _get_key()
            # Key should be deterministic
            assert _get_key() == key

    def test_fallback_default_dev_key(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("GRAPH_OLAP_ENCRYPTION_KEY", None)
            os.environ.pop("GRAPH_OLAP_INTERNAL_API_KEY", None)
            key = _get_key()
            # Should still return a valid Fernet key
            Fernet(key)

    def test_explicit_key_takes_precedence(self):
        explicit = Fernet.generate_key().decode()
        env = {
            "GRAPH_OLAP_ENCRYPTION_KEY": explicit,
            "GRAPH_OLAP_INTERNAL_API_KEY": "ignored",
        }
        with mock.patch.dict(os.environ, env, clear=False):
            assert _get_key() == explicit.encode()


class TestMaskCredentials:
    """mask_credentials should hide sensitive values while showing hints."""

    def test_long_string_masked(self):
        result = mask_credentials({"password": "mysecretpassword"})
        assert result["password"] == "my************rd"

    def test_short_string_fully_masked(self):
        result = mask_credentials({"pin": "1234"})
        assert result["pin"] == "****"

    def test_empty_string_fully_masked(self):
        result = mask_credentials({"token": ""})
        assert result["token"] == "****"

    def test_non_string_fully_masked(self):
        result = mask_credentials({"port": 5432})
        assert result["port"] == "****"

    def test_five_char_string(self):
        result = mask_credentials({"code": "abcde"})
        assert result["code"] == "ab*de"

    def test_preserves_all_keys(self):
        creds = {"a": "value1", "b": "value2", "c": "x"}
        result = mask_credentials(creds)
        assert set(result.keys()) == {"a", "b", "c"}
