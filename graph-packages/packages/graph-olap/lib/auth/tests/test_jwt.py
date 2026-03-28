"""Tests for JWT extraction utilities."""

from __future__ import annotations

import base64
import json

from lib_auth import (
    CLAIMS_NAMESPACE,
    EMAIL_CLAIM,
    ROLES_CLAIM,
    decode_jwt_payload,
    extract_email_from_token,
    extract_role_from_token,
)


def _make_jwt(payload: dict) -> str:
    """Create a fake JWT with the given payload (no signature validation needed)."""
    header_json = json.dumps({"alg": "RS256"}).encode()
    header = base64.urlsafe_b64encode(header_json).decode().rstrip("=")
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    signature = "fake_signature"
    return f"Bearer {header}.{body}.{signature}"


class TestDecodeJwtPayload:
    """Tests for decode_jwt_payload."""

    def test_valid_jwt(self) -> None:
        """Decodes valid JWT payload."""
        payload = {"sub": "user123", "email": "test@example.com"}
        token = _make_jwt(payload)
        result = decode_jwt_payload(token)
        assert result == payload

    def test_none_authorization(self) -> None:
        """Returns None for None input."""
        assert decode_jwt_payload(None) is None

    def test_empty_authorization(self) -> None:
        """Returns None for empty string."""
        assert decode_jwt_payload("") is None

    def test_no_bearer_prefix(self) -> None:
        """Returns None if not Bearer token."""
        assert decode_jwt_payload("Basic abc123") is None

    def test_invalid_jwt_parts(self) -> None:
        """Returns None if JWT doesn't have 3 parts."""
        assert decode_jwt_payload("Bearer header.payload") is None
        assert decode_jwt_payload("Bearer onlyonepart") is None

    def test_invalid_base64(self) -> None:
        """Returns None for invalid base64 payload."""
        assert decode_jwt_payload("Bearer header.!!!invalid!!!.signature") is None


class TestExtractEmailFromToken:
    """Tests for extract_email_from_token."""

    def test_extracts_email_from_custom_claim(self) -> None:
        """Extracts email from custom namespace claim."""
        payload = {EMAIL_CLAIM: "analyst@example.com"}
        token = _make_jwt(payload)
        assert extract_email_from_token(token) == "analyst@example.com"

    def test_returns_none_if_no_custom_claim(self) -> None:
        """Returns None if custom claim missing."""
        payload = {"email": "standard@example.com"}  # Standard claim, not custom
        token = _make_jwt(payload)
        assert extract_email_from_token(token) is None

    def test_returns_none_for_invalid_token(self) -> None:
        """Returns None for invalid token."""
        assert extract_email_from_token(None) is None
        assert extract_email_from_token("invalid") is None


class TestExtractRoleFromToken:
    """Tests for extract_role_from_token."""

    def test_extracts_role_from_list(self) -> None:
        """Extracts first role from list."""
        payload = {ROLES_CLAIM: ["analyst", "viewer"]}
        token = _make_jwt(payload)
        assert extract_role_from_token(token) == "analyst"

    def test_extracts_role_from_string(self) -> None:
        """Extracts role from string value."""
        payload = {ROLES_CLAIM: "admin"}
        token = _make_jwt(payload)
        assert extract_role_from_token(token) == "admin"

    def test_normalizes_to_lowercase(self) -> None:
        """Normalizes role to lowercase."""
        payload = {ROLES_CLAIM: ["ANALYST"]}
        token = _make_jwt(payload)
        assert extract_role_from_token(token) == "analyst"

    def test_returns_none_for_empty_list(self) -> None:
        """Returns None for empty roles list."""
        payload = {ROLES_CLAIM: []}
        token = _make_jwt(payload)
        assert extract_role_from_token(token) is None

    def test_returns_none_if_no_roles_claim(self) -> None:
        """Returns None if roles claim missing."""
        payload = {"sub": "user123"}
        token = _make_jwt(payload)
        assert extract_role_from_token(token) is None

    def test_returns_none_for_invalid_token(self) -> None:
        """Returns None for invalid token."""
        assert extract_role_from_token(None) is None


class TestClaimsNamespace:
    """Tests for claims constants."""

    def test_namespace_constant(self) -> None:
        """Namespace matches Auth0 configuration."""
        assert CLAIMS_NAMESPACE == "https://api.graph-olap.example.com"

    def test_email_claim_uses_namespace(self) -> None:
        """Email claim uses namespace prefix."""
        assert EMAIL_CLAIM == CLAIMS_NAMESPACE + "/email"

    def test_roles_claim_uses_namespace(self) -> None:
        """Roles claim uses namespace prefix."""
        assert ROLES_CLAIM == CLAIMS_NAMESPACE + "/roles"
