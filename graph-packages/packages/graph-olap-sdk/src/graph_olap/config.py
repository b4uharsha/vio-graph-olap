"""Configuration management for Graph OLAP SDK."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Config:
    """SDK configuration.

    Configuration can be provided explicitly or auto-discovered from
    environment variables.

    Environment Variables:
        GRAPH_OLAP_API_URL: Base URL for the control plane API
        GRAPH_OLAP_API_KEY: API key for authentication (Bearer token)
        GRAPH_OLAP_INTERNAL_API_KEY: Internal API key (X-Internal-Api-Key header)
        GRAPH_OLAP_USERNAME: Username for development/testing (X-Username header)

    Authentication:
        The SDK supports multiple authentication modes:
        - api_key: Uses 'Authorization: Bearer {key}' header (production)
        - internal_api_key: Uses 'X-Internal-Api-Key: {key}' header (internal)
        - username: Uses 'X-Username: {username}' header (development/testing)
        - role: Uses 'X-User-Role: {role}' header (development/testing)

        Priority: internal_api_key > api_key, username is always sent if provided.

    Warning - Production Environments:
        In production/staging environments with authentication gateways (e.g., production GKE):
        - The `username` and `role` parameters are IGNORED by the platform
        - Authentication happens via the gateway's IAP/OIDC layer
        - The gateway strips user-supplied X-Username/X-User-Role headers
        - The gateway injects validated headers based on authenticated identity
        - These parameters are ONLY effective in local development and E2E testing

        The SDK will still send these headers if you set them, but the authentication
        gateway will strip and replace them with validated identity information.

    Example:
        >>> # Explicit configuration with Bearer auth
        >>> config = Config(
        ...     api_url="https://api.example.com",
        ...     api_key="sk-xxx",
        ... )

        >>> # Development mode with username
        >>> config = Config(
        ...     api_url="http://localhost:8000",
        ...     username="test-user",
        ... )

        >>> # Auto-discover from environment
        >>> config = Config.from_env()
    """

    api_url: str
    api_key: str | None = None
    internal_api_key: str | None = None
    username: str | None = None
    role: str | None = None
    timeout: float = 30.0
    max_retries: int = 3

    @classmethod
    def from_env(
        cls,
        api_url: str | None = None,
        api_key: str | None = None,
        internal_api_key: str | None = None,
        username: str | None = None,
        **kwargs,
    ) -> Config:
        """Create configuration from environment variables.

        Args:
            api_url: Override GRAPH_OLAP_API_URL
            api_key: Override GRAPH_OLAP_API_KEY
            internal_api_key: Override GRAPH_OLAP_INTERNAL_API_KEY
            username: Override GRAPH_OLAP_USERNAME
            **kwargs: Additional config options

        Returns:
            Config instance

        Raises:
            ValueError: If GRAPH_OLAP_API_URL is not set
        """
        url = api_url or os.environ.get("GRAPH_OLAP_API_URL")
        if not url:
            raise ValueError(
                "GRAPH_OLAP_API_URL not set. Either pass api_url parameter "
                "or set the GRAPH_OLAP_API_URL environment variable."
            )

        key = api_key or os.environ.get("GRAPH_OLAP_API_KEY")
        internal_key = internal_api_key or os.environ.get("GRAPH_OLAP_INTERNAL_API_KEY")
        user = username or os.environ.get("GRAPH_OLAP_USERNAME")

        return cls(api_url=url, api_key=key, internal_api_key=internal_key, username=user, **kwargs)
