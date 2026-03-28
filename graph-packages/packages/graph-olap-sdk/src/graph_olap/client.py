"""Main Graph OLAP SDK client."""

from __future__ import annotations

from typing import Any

from graph_olap_schemas import WrapperType

from graph_olap.config import Config
from graph_olap.http import HTTPClient
from graph_olap.resources.admin import AdminResource
from graph_olap.resources.favorites import FavoriteResource
from graph_olap.resources.health import HealthResource
from graph_olap.resources.instances import InstanceResource
from graph_olap.resources.mappings import MappingResource
from graph_olap.resources.ops import OpsResource
from graph_olap.resources.schema import SchemaResource

# =============================================================================
# SNAPSHOT FUNCTIONALITY DISABLED
# Snapshots are now created implicitly when instances are created from mappings.
# =============================================================================
# from graph_olap.resources.snapshots import SnapshotResource


class GraphOLAPClient:
    """Main client for Graph OLAP Platform.

    Provides access to all control plane operations:
    - Mappings: Graph schema definitions
    - Snapshots: Point-in-time data exports
    - Instances: Running graph databases
    - Favorites: Bookmarked resources
    - Schema: Browse Starburst schema metadata (catalogs, schemas, tables, columns)
    - Ops: Configuration and cluster management (Ops role)
    - Admin: Privileged operations (Admin role)
    - Health: Health and readiness checks

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
        >>> client = GraphOLAPClient(
        ...     api_url="https://graph-olap.example.com",
        ...     api_key="sk-xxx",
        ... )

        >>> # Development mode with username
        >>> client = GraphOLAPClient(
        ...     api_url="http://localhost:8000",
        ...     username="test-user",
        ...     role="analyst",
        ... )

        >>> # Or auto-discover from environment
        >>> client = GraphOLAPClient.from_env()

        >>> # List mappings
        >>> mappings = client.mappings.list()

        >>> # Create snapshot and wait
        >>> snapshot = client.snapshots.create_and_wait(
        ...     mapping_id=1,
        ...     name="Analysis Snapshot",
        ... )

        >>> # Create instance and connect
        >>> instance = client.instances.create_and_wait(
        ...     snapshot_id=snapshot.id,
        ...     name="Analysis Instance",
        ... )
        >>> conn = client.instances.connect(instance.id)

        >>> # Query
        >>> result = conn.query("MATCH (n:Customer) RETURN n LIMIT 10")
        >>> df = result.to_polars()

        >>> # Clean up
        >>> client.instances.terminate(instance.id)
        >>> client.close()

    Using context manager:
        >>> with GraphOLAPClient.from_env() as client:
        ...     mappings = client.mappings.list()
    """

    def __init__(
        self,
        api_url: str,
        api_key: str | None = None,
        internal_api_key: str | None = None,
        username: str | None = None,
        role: str | None = None,
        *,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        """Initialize Graph OLAP client.

        Args:
            api_url: Base URL for the control plane API
            api_key: API key for authentication (Bearer token)
            internal_api_key: Internal API key (X-Internal-Api-Key header)
            username: Username for user-scoped routes (X-Username header)
            role: User role for X-User-Role header (e.g., "analyst", "admin", "ops")
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for transient failures
        """
        self._config = Config(
            api_url=api_url,
            api_key=api_key,
            internal_api_key=internal_api_key,
            username=username,
            role=role,
            timeout=timeout,
            max_retries=max_retries,
        )

        self._http = HTTPClient(
            base_url=api_url,
            api_key=api_key,
            internal_api_key=internal_api_key,
            username=username,
            role=role,
            timeout=timeout,
            max_retries=max_retries,
        )

        # Resource managers
        self.mappings = MappingResource(self._http)
        # SNAPSHOT FUNCTIONALITY DISABLED - snapshots created implicitly from mappings
        # self.snapshots = SnapshotResource(self._http)
        self.instances = InstanceResource(self._http, self._config)
        self.favorites = FavoriteResource(self._http)
        self.schema = SchemaResource(self._http)
        self.ops = OpsResource(self._http)
        self.admin = AdminResource(self._http)
        self.health = HealthResource(self._http)

    @classmethod
    def from_env(
        cls,
        api_url: str | None = None,
        api_key: str | None = None,
        internal_api_key: str | None = None,
        username: str | None = None,
        **kwargs: Any,
    ) -> GraphOLAPClient:
        """Create client from environment variables.

        Environment Variables:
            GRAPH_OLAP_API_URL: Base URL for the control plane API
            GRAPH_OLAP_API_KEY: API key for authentication (Bearer token)
            GRAPH_OLAP_INTERNAL_API_KEY: Internal API key (X-Internal-Api-Key header)
            GRAPH_OLAP_USERNAME: Username for development/testing (X-Username header)

        Args:
            api_url: Override GRAPH_OLAP_API_URL
            api_key: Override GRAPH_OLAP_API_KEY
            internal_api_key: Override GRAPH_OLAP_INTERNAL_API_KEY
            username: Override GRAPH_OLAP_USERNAME
            **kwargs: Additional config options (timeout, max_retries)

        Returns:
            Configured GraphOLAPClient

        Raises:
            ValueError: If GRAPH_OLAP_API_URL is not set

        Example:
            >>> # Uses environment variables
            >>> client = GraphOLAPClient.from_env()

            >>> # Override specific values
            >>> client = GraphOLAPClient.from_env(timeout=60.0)
        """
        config = Config.from_env(api_url=api_url, api_key=api_key, internal_api_key=internal_api_key, username=username, **kwargs)
        return cls(
            api_url=config.api_url,
            api_key=config.api_key,
            internal_api_key=config.internal_api_key,
            username=config.username,
            timeout=config.timeout,
            max_retries=config.max_retries,
        )

    def close(self) -> None:
        """Close the client and release resources."""
        self._http.close()

    def __enter__(self) -> GraphOLAPClient:
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()

    def quick_start(
        self,
        mapping_id: int,
        wrapper_type: WrapperType,
        *,
        snapshot_name: str | None = None,
        instance_name: str | None = None,
        wait_timeout: int = 600,
    ) -> Any:
        """Quick start: create snapshot, instance, and connect in one call.

        Convenience method for the common workflow of going from a mapping
        to a connected instance ready for queries.

        Args:
            mapping_id: Mapping ID to use
            wrapper_type: Graph database wrapper type (ryugraph or falkordb)
            snapshot_name: Name for snapshot (defaults to "Quick Snapshot")
            instance_name: Name for instance (defaults to "Quick Instance")
            wait_timeout: Max time to wait for snapshot + instance creation

        Returns:
            InstanceConnection ready for queries

        Example:
            >>> conn = client.quick_start(mapping_id=1, wrapper_type=WrapperType.RYUGRAPH)
            >>> result = conn.query("MATCH (n) RETURN count(n)")
            >>> # Remember to terminate the instance when done!
        """

        # Create snapshot
        snapshot = self.snapshots.create_and_wait(
            mapping_id=mapping_id,
            name=snapshot_name or "Quick Snapshot",
            timeout=wait_timeout // 2,
        )

        # Create instance
        instance = self.instances.create_and_wait(
            snapshot_id=snapshot.id,
            name=instance_name or "Quick Instance",
            wrapper_type=wrapper_type,
            timeout=wait_timeout // 2,
        )

        # Connect
        return self.instances.connect(instance.id)
