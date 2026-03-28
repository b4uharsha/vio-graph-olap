"""Testing utilities for E2E notebook tests.

This module provides Google-style test contexts with automatic cleanup for
Jupyter notebooks. The key features are:

1. **Explicit identity**: Every test must specify which user is acting
2. **Auto-naming**: Resources get unique names automatically
3. **Auto-tracking**: Resources created via ctx.* are tracked automatically
4. **Guaranteed cleanup**: atexit + signal handlers ensure cleanup even on failure

Quick Start:
    >>> from graph_olap import notebook
    >>> from graph_olap.testing import TestPersona
    >>>
    >>> ctx = notebook.test("CrudTest", persona=TestPersona.ANALYST_ALICE)
    >>> mapping = ctx.mapping(node_definitions=[...])
    >>> instance = ctx.instance(mapping)
    >>> conn = ctx.connect(instance)
    >>>
    >>> # Cleanup happens automatically on exit!

Environment Variables (all required for testing):
    GRAPH_OLAP_API_URL: Control plane URL
    GRAPH_OLAP_API_KEY_ANALYST_ALICE: API key for Alice (analyst role)
    GRAPH_OLAP_API_KEY_ANALYST_BOB: API key for Bob (analyst role)
    GRAPH_OLAP_API_KEY_ADMIN_CAROL: API key for Carol (admin role)
    GRAPH_OLAP_API_KEY_OPS_DAVE: API key for Dave (ops role)
"""

from __future__ import annotations

import atexit
import logging
import os
import signal
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from graph_olap.client import GraphOLAPClient
    from graph_olap.instance.connection import InstanceConnection
    from graph_olap.models import Instance, Mapping, Snapshot

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PersonaConfig:
    """Configuration for a test persona.

    Each persona represents a bearer token that contains both identity and roles.
    The env_var points to the API key for that persona.

    Attributes:
        name: Human-readable name for logging
        env_var: Environment variable containing the API key
        description: Description of this persona's role
        expected_role: Expected role in the token (for documentation/validation)
    """

    name: str
    env_var: str
    description: str
    expected_role: str


class TestPersona(Enum):
    """Pre-defined test personas for E2E tests.

    Each persona maps to a specific API key environment variable.
    The token in that variable should be pre-configured with the
    appropriate identity (username/email) and roles.

    Naming pattern: <ROLE>_<NAME> for consistency.

    IMPORTANT: There is NO default persona. Every test must explicitly
    specify which user is acting. This prevents confusion and ensures
    tests are self-documenting about who is performing each action.

    This is the SINGLE SOURCE OF TRUTH for test personas.

    Example:
        >>> from graph_olap.testing import TestPersona
        >>> ctx = notebook.test("CrudTest", persona=TestPersona.ANALYST_ALICE)
    """

    ANALYST_ALICE = PersonaConfig(
        name="analyst_alice",
        env_var="GRAPH_OLAP_API_KEY_ANALYST_ALICE",
        description="Analyst user Alice - standard analyst permissions",
        expected_role="analyst",
    )
    ANALYST_BOB = PersonaConfig(
        name="analyst_bob",
        env_var="GRAPH_OLAP_API_KEY_ANALYST_BOB",
        description="Analyst user Bob - standard analyst permissions",
        expected_role="analyst",
    )
    ADMIN_CAROL = PersonaConfig(
        name="admin_carol",
        env_var="GRAPH_OLAP_API_KEY_ADMIN_CAROL",
        description="Admin user Carol - elevated admin permissions",
        expected_role="admin",
    )
    OPS_DAVE = PersonaConfig(
        name="ops_dave",
        env_var="GRAPH_OLAP_API_KEY_OPS_DAVE",
        description="Ops user Dave - operations and monitoring permissions",
        expected_role="ops",
    )


# Global registry of active test contexts (for cleanup on unexpected exit)
_active_contexts: dict[str, NotebookTest] = {}


class NotebookTest:
    """Google-style test context with automatic cleanup and typed personas.

    Every test must specify which user is acting - there is no default.
    This ensures tests are self-documenting and explicit about identity.

    Features:
    - Auto-naming: Resources get unique names like "CrudTest-Mapping-a1b2c3d4"
    - Auto-tracking: Resources created via ctx.* are tracked automatically
    - Guaranteed cleanup: atexit + signal handlers ensure cleanup
    - Type-safe personas: IDE autocomplete for all available test users

    Example:
        >>> from graph_olap import notebook
        >>> from graph_olap.testing import TestPersona
        >>>
        >>> ctx = notebook.test("CrudTest", persona=TestPersona.ANALYST_ALICE)
        >>>
        >>> # Create resources (auto-named, auto-tracked)
        >>> mapping = ctx.mapping(node_definitions=[...])
        >>> instance = ctx.instance(mapping)
        >>> conn = ctx.connect(instance)
        >>>
        >>> # Query
        >>> result = conn.query("MATCH (n) RETURN count(n)")
        >>>
        >>> # Cleanup happens automatically!
        >>> # Or call ctx.cleanup() for immediate cleanup
    """

    def __init__(self, prefix: str, *, persona: TestPersona):
        """Create a test context.

        Args:
            prefix: Test name prefix for auto-naming resources (e.g., "CrudTest")
            persona: The persona running this test (REQUIRED - no default!)

        Raises:
            TypeError: If persona is not provided
            ValueError: If required environment variables are missing
        """
        self.prefix = prefix
        self.run_id = uuid.uuid4().hex[:8]
        self._persona = persona
        self._persona_clients: dict[TestPersona, GraphOLAPClient] = {}
        self._resources: list[tuple[str, int, str]] = []  # (type, id, name)
        self._cleaned_up = False

        # Validate required env vars
        api_url = os.environ.get("GRAPH_OLAP_API_URL")
        if not api_url:
            raise ValueError(
                "GRAPH_OLAP_API_URL is required. "
                "Set this environment variable to the control plane URL."
            )

        # Create primary client for the specified persona
        self.client = self._create_client(persona)

        # Register cleanup handlers
        self._context_id = f"{prefix}-{self.run_id}"
        _active_contexts[self._context_id] = self
        atexit.register(self._cleanup)

        # Register signal handlers for SIGTERM/SIGINT
        self._setup_signal_handlers()

        logger.info(
            f"NotebookTest initialized: prefix={prefix}, run_id={self.run_id}, "
            f"persona={persona.value.name}"
        )

    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful cleanup on SIGTERM/SIGINT."""
        def signal_handler(signum: int, frame: Any) -> None:
            logger.warning(f"Received signal {signum}, cleaning up...")
            self._cleanup()
            # Re-raise the signal after cleanup
            signal.signal(signum, signal.SIG_DFL)
            os.kill(os.getpid(), signum)

        try:
            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGINT, signal_handler)
        except (ValueError, OSError):
            # Signal handling not available (e.g., not main thread)
            pass

    def _create_client(self, persona: TestPersona) -> GraphOLAPClient:
        """Create a client for a specific persona.

        Supports two authentication modes:
          - In-cluster mode: Uses X-Username/X-User-Role headers (bypasses SAML/oauth2-proxy).
            Enable by setting GRAPH_OLAP_IN_CLUSTER_MODE=true. Useful for kubectl exec
            based testing inside the cluster where tokens aren't available.
          - External mode: Uses Bearer token from environment variable. Default mode
            for testing from outside the cluster.

        Args:
            persona: The test persona to create a client for

        Returns:
            GraphOLAPClient authenticated as that persona

        Raises:
            ValueError: If the API key environment variable is not set (external mode)
        """
        from graph_olap.client import GraphOLAPClient

        api_url = os.environ["GRAPH_OLAP_API_URL"]
        in_cluster = os.environ.get(
            "GRAPH_OLAP_IN_CLUSTER_MODE", ""
        ).lower() in ("true", "1", "yes")

        if in_cluster:
            # In-cluster mode: use header-based auth (bypasses SAML/oauth2-proxy)
            # Replace example.com with your organization's domain when deploying
            persona_identities = {
                TestPersona.ANALYST_ALICE: ("alice@example.com", "analyst"),
                TestPersona.ANALYST_BOB: ("bob@example.com", "analyst"),
                TestPersona.ADMIN_CAROL: ("carol@example.com", "admin"),
                TestPersona.OPS_DAVE: ("dave@example.com", "ops"),
            }
            username, role = persona_identities[persona]
            return GraphOLAPClient(
                api_url=api_url,
                username=username,
                role=role,
            )

        config = persona.value
        api_key = os.environ.get(config.env_var)

        if not api_key:
            raise ValueError(
                f"Missing API key for persona '{config.name}'. "
                f"Set {config.env_var} environment variable.\n"
                f"Description: {config.description}"
            )

        return GraphOLAPClient(
            api_url=api_url,
            api_key=api_key,
        )

    def with_persona(self, persona: TestPersona) -> GraphOLAPClient:
        """Get a client authenticated as a different persona.

        Use this for authorization tests that need multiple users.

        Args:
            persona: The test persona to use (from TestPersona enum)

        Returns:
            GraphOLAPClient authenticated as that persona

        Example:
            >>> ctx = notebook.test("AuthTest", persona=TestPersona.ANALYST_ALICE)
            >>> bob = ctx.with_persona(TestPersona.ANALYST_BOB)
            >>>
            >>> # Alice creates a mapping
            >>> mapping = ctx.mapping(...)
            >>>
            >>> # Bob can't see it (user isolation)
            >>> bob_mappings = bob.mappings.list()
            >>> assert mapping.id not in [m.id for m in bob_mappings]
        """
        if persona not in self._persona_clients:
            self._persona_clients[persona] = self._create_client(persona)
        return self._persona_clients[persona]

    # =========================================================================
    # Resource Creation (auto-named, auto-tracked)
    # =========================================================================

    def mapping(
        self,
        *,
        name: str | None = None,
        node_definitions: list[dict[str, Any]] | None = None,
        edge_definitions: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> Mapping:
        """Create a test mapping (auto-named, auto-tracked).

        Args:
            name: Optional custom name (defaults to "{prefix}-Mapping-{run_id}")
            node_definitions: List of node definition dicts
            edge_definitions: List of edge definition dicts
            **kwargs: Additional arguments passed to mappings.create()

        Returns:
            Created Mapping object

        Example:
            >>> mapping = ctx.mapping(
            ...     node_definitions=[{"name": "Person", "table": "people"}],
            ...     edge_definitions=[{"name": "KNOWS", ...}],
            ... )
        """
        name = name or f"{self.prefix}-Mapping-{self.run_id}"
        mapping = self.client.mappings.create(
            name=name,
            node_definitions=node_definitions or [],
            edge_definitions=edge_definitions or [],
            **kwargs,
        )
        self._track("mapping", mapping.id, name)
        return mapping

    def snapshot(
        self,
        mapping: Mapping | int,
        *,
        name: str | None = None,
        timeout: int = 300,
        **kwargs: Any,
    ) -> Snapshot:
        """Create a test snapshot and wait for ready (auto-named, auto-tracked).

        Note: Snapshot creation API is currently disabled. Use instance() with a mapping instead,
        which auto-creates snapshots.

        Args:
            mapping: Mapping object or mapping ID
            name: Optional custom name (defaults to "{prefix}-Snapshot-{run_id}")
            timeout: Max seconds to wait for snapshot to be ready
            **kwargs: Additional arguments passed to snapshots.create_and_wait()

        Returns:
            Created Snapshot object (in READY state)

        Example:
            >>> snapshot = ctx.snapshot(mapping, timeout=180)
        """
        mapping_id = mapping.id if hasattr(mapping, "id") else mapping
        name = name or f"{self.prefix}-Snapshot-{self.run_id}"
        snapshot = self.client.snapshots.create_and_wait(
            mapping_id=mapping_id,
            name=name,
            timeout=timeout,
            **kwargs,
        )
        self._track("snapshot", snapshot.id, name)
        return snapshot

    def instance(
        self,
        mapping: Mapping | int,
        *,
        name: str | None = None,
        wrapper_type: str = "ryugraph",
        timeout: int = 300,
        **kwargs: Any,
    ) -> Instance:
        """Create a test instance from mapping and wait for running (auto-named, auto-tracked).

        Args:
            mapping: Mapping object or mapping ID
            name: Optional custom name (defaults to "{prefix}-Instance-{run_id}")
            wrapper_type: Graph database wrapper ("ryugraph" or "falkordb")
            timeout: Max seconds to wait for instance to be running
            **kwargs: Additional arguments passed to instances.create_and_wait()

        Returns:
            Created Instance object (in RUNNING state)

        Example:
            >>> instance = ctx.instance(mapping, wrapper_type="falkordb")
        """
        mapping_id = mapping.id if hasattr(mapping, "id") else mapping
        name = name or f"{self.prefix}-Instance-{self.run_id}"
        instance = self.client.instances.create_and_wait(
            mapping_id=mapping_id,
            name=name,
            wrapper_type=wrapper_type,
            timeout=timeout,
            **kwargs,
        )
        self._track("instance", instance.id, name)
        return instance

    def connect(self, instance: Instance | int) -> InstanceConnection:
        """Connect to an instance.

        Args:
            instance: Instance object or instance ID

        Returns:
            InstanceConnection ready for queries

        Example:
            >>> conn = ctx.connect(instance)
            >>> result = conn.query("MATCH (n) RETURN count(n)")
        """
        instance_id = instance.id if hasattr(instance, "id") else instance
        return self.client.instances.connect(instance_id)

    # =========================================================================
    # Tracking and Cleanup
    # =========================================================================

    def _track(self, resource_type: str, resource_id: int, name: str) -> None:
        """Track a resource for cleanup.

        Args:
            resource_type: Type of resource ("mapping", "snapshot", "instance")
            resource_id: ID of the resource
            name: Name of the resource (for logging)
        """
        self._resources.append((resource_type, resource_id, name))
        logger.info(f"Tracking {resource_type} {resource_id} ({name})")

    def cleanup(self) -> dict[str, int]:
        """Manually trigger cleanup of all tracked resources.

        Call this for immediate cleanup instead of waiting for exit.
        Safe to call multiple times (idempotent).

        Returns:
            Dict with counts: {"instances": n, "snapshots": n, "mappings": n}

        Example:
            >>> results = ctx.cleanup()
            >>> print(f"Cleaned up {results['instances']} instances")
        """
        return self._do_cleanup()

    def _cleanup(self) -> None:
        """Internal cleanup handler for atexit/signals."""
        self._do_cleanup()

    def _do_cleanup(self) -> dict[str, int]:
        """Perform cleanup of all tracked resources.

        Cleans up in dependency order: instances -> snapshots -> mappings.

        Returns:
            Dict with counts of cleaned up resources
        """
        if self._cleaned_up:
            logger.debug("Cleanup already performed, skipping")
            return {"instances": 0, "snapshots": 0, "mappings": 0}

        self._cleaned_up = True
        results = {"instances": 0, "snapshots": 0, "mappings": 0}

        if not self._resources:
            logger.info("No resources to clean up")
            return results

        logger.info(f"Cleaning up {len(self._resources)} tracked resource(s)...")

        # Import here to avoid circular imports
        from graph_olap.exceptions import NotFoundError

        # Group by type for ordered cleanup
        instances = [(id_, name) for t, id_, name in self._resources if t == "instance"]
        snapshots = [(id_, name) for t, id_, name in self._resources if t == "snapshot"]
        mappings = [(id_, name) for t, id_, name in self._resources if t == "mapping"]

        # Clean up instances first (reverse creation order within type)
        for instance_id, name in reversed(instances):
            try:
                logger.info(f"Terminating instance {instance_id} ({name})")
                self.client.instances.terminate(instance_id)
                results["instances"] += 1
            except NotFoundError:
                logger.warning(f"Instance {instance_id} already deleted")
            except Exception as e:
                logger.error(f"Failed to terminate instance {instance_id}: {e}")

        # Clean up snapshots
        for snapshot_id, name in reversed(snapshots):
            try:
                logger.info(f"Deleting snapshot {snapshot_id} ({name})")
                self.client.snapshots.delete(snapshot_id)
                results["snapshots"] += 1
            except NotFoundError:
                logger.warning(f"Snapshot {snapshot_id} already deleted")
            except Exception as e:
                logger.error(f"Failed to delete snapshot {snapshot_id}: {e}")

        # Clean up mappings
        for mapping_id, name in reversed(mappings):
            try:
                logger.info(f"Deleting mapping {mapping_id} ({name})")
                self.client.mappings.delete(mapping_id)
                results["mappings"] += 1
            except NotFoundError:
                logger.warning(f"Mapping {mapping_id} already deleted")
            except Exception as e:
                logger.error(f"Failed to delete mapping {mapping_id}: {e}")

        # Remove from global registry
        _active_contexts.pop(self._context_id, None)

        # Close all clients
        try:
            self.client.close()
        except Exception:
            pass
        for client in self._persona_clients.values():
            try:
                client.close()
            except Exception:
                pass

        logger.info(
            f"Cleanup complete: {results['instances']} instances, "
            f"{results['snapshots']} snapshots, {results['mappings']} mappings"
        )

        return results

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"NotebookTest(prefix={self.prefix!r}, run_id={self.run_id!r}, "
            f"persona={self._persona.value.name!r}, resources={len(self._resources)})"
        )
