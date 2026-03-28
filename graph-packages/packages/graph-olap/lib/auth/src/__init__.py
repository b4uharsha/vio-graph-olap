"""Shared JWT authentication utilities for graph-olap services.

Provides functions to extract claims from JWT tokens that have already
been validated by oauth2-proxy at the edge. No signature verification
is performed - these utilities only decode and extract claims.

Usage:
    from lib_auth import extract_email_from_token, extract_role_from_token

    email = extract_email_from_token(authorization_header)
    role = extract_role_from_token(authorization_header)
"""

from __future__ import annotations

import base64
import json

__all__ = [
    "CLAIMS_NAMESPACE",
    "EMAIL_CLAIM",
    "ROLES_CLAIM",
    "decode_jwt_payload",
    "extract_email_from_token",
    "extract_role_from_token",
]

# Auth0 custom claims namespace
CLAIMS_NAMESPACE = "https://api.graph-olap.example.com"
EMAIL_CLAIM = f"{CLAIMS_NAMESPACE}/email"
ROLES_CLAIM = f"{CLAIMS_NAMESPACE}/roles"


def decode_jwt_payload(authorization: str | None) -> dict | None:
    """Decode JWT Bearer token payload without signature validation.

    The token has already been validated by oauth2-proxy at the edge.
    This function only decodes the payload to extract claims.

    Args:
        authorization: Authorization header value (Bearer <token>)

    Returns:
        Decoded payload dict, or None if not a valid JWT Bearer token
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None

    try:
        token = authorization[7:]  # Remove "Bearer " prefix

        # JWT has 3 parts: header.payload.signature
        parts = token.split(".")
        if len(parts) != 3:
            return None

        # Decode payload (base64url)
        payload_b64 = parts[1]

        # Add padding if needed (base64url may omit padding)
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding

        return json.loads(base64.urlsafe_b64decode(payload_b64))
    except Exception:
        return None


def extract_email_from_token(authorization: str | None) -> str | None:
    """Extract email from JWT custom claim.

    Looks for email in the custom namespace claim used by Auth0 Actions
    for both user tokens and M2M tokens.

    Args:
        authorization: Authorization header value (Bearer <token>)

    Returns:
        Email string, or None if not found
    """
    payload = decode_jwt_payload(authorization)
    if not payload:
        return None

    return payload.get(EMAIL_CLAIM)


def extract_role_from_token(authorization: str | None) -> str | None:
    """Extract role from JWT custom claim.

    Looks for roles in the custom namespace claim. If roles is a list,
    returns the first role. Role is normalized to lowercase.

    Args:
        authorization: Authorization header value (Bearer <token>)

    Returns:
        Role string (lowercase), or None if not found
    """
    payload = decode_jwt_payload(authorization)
    if not payload:
        return None

    roles = payload.get(ROLES_CLAIM)

    if roles is None:
        return None
    if isinstance(roles, list) and roles:
        return roles[0].lower()
    if isinstance(roles, str):
        return roles.lower()

    return None
