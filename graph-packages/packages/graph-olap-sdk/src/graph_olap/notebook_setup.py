"""Shared notebook setup -- provides clients and resource tracking.

Every notebook (tutorial, E2E, reference, UAT) should start with:

    from graph_olap.notebook_setup import setup
    ctx = setup()
    client = ctx.client          # analyst (Alice)

And end with:

    ctx.teardown()

For E2E tests:

    from graph_olap.notebook_setup import setup
    from graph_olap.personas import Persona

    ctx = setup(prefix="AlgoTest", persona=Persona.ANALYST_ALICE)
    client = ctx.client
    mapping = ctx.mapping(node_definitions=[...])
    instance = ctx.instance(mapping)
    conn = ctx.connect(instance)
    ctx.teardown()

Environment Variables:
    GRAPH_OLAP_API_URL:    Control plane URL (required)
    JUPYTERHUB_USER:       JupyterHub user for namespace isolation (default: "local")
    GRAPH_OLAP_USERNAME_*: Per-persona usernames for E2E tests (optional)
"""

from __future__ import annotations

import atexit
import logging
import os
import signal
import uuid
from typing import TYPE_CHECKING, Any

from graph_olap.client import GraphOLAPClient
from graph_olap.exceptions import NotFoundError
from graph_olap.personas import Persona

if TYPE_CHECKING:
    from graph_olap.instance.connection import InstanceConnection
    from graph_olap.models import Instance, Mapping, Snapshot

logger = logging.getLogger(__name__)


def _get_hub_user() -> str:
    """Get JupyterHub username, defaulting to ``'local'`` for dev."""
    return os.environ.get("JUPYTERHUB_USER", "local")


def _make_username(persona_name: str) -> str:
    """Build a namespaced username for the given persona."""
    hub_user = _get_hub_user()
    if hub_user == "local":
        return f"{persona_name}@e2e.local"
    return f"{persona_name}@e2e.{hub_user}.local"


def _get_api_url(api_url: str | None = None) -> str:
    """Resolve the API URL from an explicit argument or the environment."""
    url = api_url or os.environ.get("GRAPH_OLAP_API_URL")
    if not url:
        raise RuntimeError(
            "GRAPH_OLAP_API_URL is not set. Pass api_url=... explicitly to "
            "setup(), or set the GRAPH_OLAP_API_URL environment variable."
        )
    return url


def _make_client(api_url: str, username: str) -> GraphOLAPClient:
    """Create a GraphOLAPClient."""
    return GraphOLAPClient(
        username=username,
        api_url=api_url,
    )


class NotebookContext:
    """Pre-authenticated clients and resource tracker for notebook sessions.

    In **tutorial mode** (no ``prefix``), provides three pre-built clients
    (:attr:`client`, :attr:`admin`, :attr:`ops`).
    In **E2E test mode** (with ``prefix``), provides a single primary client.
    """

    def __init__(
        self,
        api_url: str,
        hub_user: str,
        *,
        prefix: str | None = None,
        persona: Persona | None = None,
    ) -> None:
        self.api_url = api_url
        self.hub_user = hub_user
        self.prefix = prefix
        self.run_id = uuid.uuid4().hex[:8] if prefix else None
        self._persona = persona

        self._tracked_instances: list[int] = []
        self._tracked_mappings: list[int] = []
        self._resources: list[tuple[str, Any, Any]] = []
        self._cleaned_up = False
        self._persona_clients: dict[Persona, GraphOLAPClient] = {}

        if prefix and persona:
            self.client = self._create_persona_client(persona)
            self._persona_clients[persona] = self.client
            self.admin = None
            self.ops = None
        else:
            self.client = _make_client(api_url, _make_username("analyst_alice"))
            self.admin = _make_client(api_url, _make_username("admin_carol"))
            self.ops = _make_client(api_url, _make_username("ops_dave"))

        atexit.register(self._atexit_cleanup)
        self._original_sigterm = signal.getsignal(signal.SIGTERM)
        self._original_sigint = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def _create_persona_client(self, persona: Persona) -> GraphOLAPClient:
        config = persona.value
        if self.prefix:
            username = os.environ.get(config.env_var) or f"{config.name}@e2e.local"
        else:
            username = _make_username(config.name)
        return _make_client(self.api_url, username)

    def with_persona(self, persona: Persona) -> GraphOLAPClient:
        """Get a client authenticated as a different persona."""
        if persona not in self._persona_clients:
            self._persona_clients[persona] = self._create_persona_client(persona)
        return self._persona_clients[persona]

    def track(self, resource_type: str, resource_id: Any, name: Any) -> None:
        """Track a resource for cleanup on teardown."""
        self._resources.append((resource_type, resource_id, name))
        logger.info("Tracking %s %s (%s)", resource_type, resource_id, name)

    _track = track

    def connect(self, instance_id: int | Instance) -> InstanceConnection:
        """Connect to a graph instance."""
        if hasattr(instance_id, "id"):
            return self.client.instances.connect(instance_id.id)
        return self.client.instances.connect(instance_id)

    def create_mapping(self, **kwargs: Any) -> Mapping:
        """Create a mapping and track it for cleanup."""
        mapping = self.client.mappings.create(**kwargs)
        self._tracked_mappings.append(mapping.id)
        return mapping

    def create_instance(self, **kwargs: Any) -> Instance:
        """Create an instance and track it for cleanup."""
        instance = self.client.instances.create_and_wait(**kwargs)
        self._tracked_instances.append(instance.id)
        return instance

    def mapping(
        self,
        *,
        name: str | None = None,
        node_definitions: list[dict[str, Any]] | None = None,
        edge_definitions: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> Mapping:
        """Create a mapping with auto-naming and auto-tracking."""
        if name is None and self.prefix:
            name = f"{self.prefix}-Mapping-{self.run_id}"
        mapping = self.client.mappings.create(
            name=name,
            node_definitions=node_definitions or [],
            edge_definitions=edge_definitions or [],
            **kwargs,
        )
        self.track("mapping", mapping.id, mapping.name)
        return mapping

    def instance(
        self,
        mapping: Mapping | int,
        *,
        name: str | None = None,
        wrapper_type: str = "ryugraph",
        timeout: int = 300,
        **kwargs: Any,
    ) -> Instance:
        """Create an instance from a mapping and wait for running."""
        mapping_id = mapping.id if hasattr(mapping, "id") else mapping
        if name is None and self.prefix:
            name = f"{self.prefix}-Instance-{self.run_id}"
        instance = self.client.instances.create_and_wait(
            mapping_id=mapping_id,
            name=name,
            wrapper_type=wrapper_type,
            timeout=timeout,
            **kwargs,
        )
        self.track("instance", instance.id, instance.name)
        return instance

    def snapshot(
        self,
        mapping: Mapping | int,
        *,
        name: str | None = None,
        timeout: int = 300,
        **kwargs: Any,
    ) -> Snapshot:
        """Create a snapshot and wait for ready."""
        mapping_id = mapping.id if hasattr(mapping, "id") else mapping
        if name is None and self.prefix:
            name = f"{self.prefix}-Snapshot-{self.run_id}"
        snapshot = self.client.snapshots.create_and_wait(
            mapping_id=mapping_id,
            name=name,
            timeout=timeout,
            **kwargs,
        )
        self.track("snapshot", snapshot.id, snapshot.name)
        return snapshot

    def cleanup(self) -> dict[str, int]:
        """Alias for teardown that returns cleanup counts."""
        return self.teardown()

    def _atexit_cleanup(self) -> None:
        if not self._cleaned_up:
            logger.info("atexit: teardown() was not called, cleaning up now")
            self.teardown()

    def _signal_handler(self, signum: int, frame: Any) -> None:
        logger.info("Signal %d received, cleaning up", signum)
        self.teardown()
        if signum == signal.SIGTERM:
            if self._original_sigterm not in (signal.SIG_DFL, signal.SIG_IGN, None):
                self._original_sigterm(signum, frame)
        elif signum == signal.SIGINT:
            if self._original_sigint not in (signal.SIG_DFL, signal.SIG_IGN, None):
                self._original_sigint(signum, frame)
            else:
                raise KeyboardInterrupt

    def teardown(self) -> dict[str, int]:
        """Terminate tracked resources and close clients."""
        if self._cleaned_up:
            return {"instances": 0, "snapshots": 0, "mappings": 0, "graph_properties": 0}
        self._cleaned_up = True

        results = {"instances": 0, "snapshots": 0, "mappings": 0, "graph_properties": 0}

        if self._resources:
            logger.info("Cleaning up %d tracked resource(s)...", len(self._resources))

            graph_props = [(id_, name) for t, id_, name in self._resources if t == "graph_properties"]
            instances = [(id_, name) for t, id_, name in self._resources if t == "instance"]
            snapshots = [(id_, name) for t, id_, name in self._resources if t == "snapshot"]
            mappings = [(id_, name) for t, id_, name in self._resources if t == "mapping"]

            for conn_obj, meta in graph_props:
                try:
                    node_label = meta.get("node_label", "Customer") if isinstance(meta, dict) else "Customer"
                    prop_names = meta.get("property_names", []) if isinstance(meta, dict) else []
                    if prop_names:
                        remove_clause = ", ".join(f"n.{p}" for p in prop_names)
                        conn_obj.query_scalar(
                            f"MATCH (n:{node_label}) REMOVE {remove_clause} RETURN count(n)"
                        )
                        results["graph_properties"] += 1
                except Exception as exc:
                    logger.warning("Could not clean graph properties: %s", exc)

            for instance_id, name in reversed(instances):
                try:
                    self.client.instances.terminate(instance_id)
                    results["instances"] += 1
                except NotFoundError:
                    pass
                except Exception as exc:
                    logger.warning("Teardown: failed to terminate instance %d: %s", instance_id, exc)

            for snapshot_id, name in reversed(snapshots):
                try:
                    self.client.snapshots.delete(snapshot_id)
                    results["snapshots"] += 1
                except NotFoundError:
                    pass
                except Exception as exc:
                    logger.warning("Teardown: failed to delete snapshot %d: %s", snapshot_id, exc)

            for mapping_id, name in reversed(mappings):
                try:
                    self.client.mappings.delete(mapping_id)
                    results["mappings"] += 1
                except NotFoundError:
                    pass
                except Exception as exc:
                    logger.warning("Teardown: failed to delete mapping %d: %s", mapping_id, exc)

        for iid in self._tracked_instances:
            try:
                self.client.instances.terminate(iid)
                results["instances"] += 1
            except Exception as exc:
                logger.warning("Teardown: failed to terminate instance %d: %s", iid, exc)

        for mid in self._tracked_mappings:
            try:
                self.client.mappings.delete(mid)
                results["mappings"] += 1
            except Exception as exc:
                logger.warning("Teardown: failed to delete mapping %d: %s", mid, exc)

        self._tracked_instances.clear()
        self._tracked_mappings.clear()
        self._resources.clear()

        for _, client_obj in [("client", self.client), ("admin", self.admin), ("ops", self.ops)]:
            if client_obj is not None:
                try:
                    client_obj.close()
                except Exception:
                    pass

        for persona, client_obj in self._persona_clients.items():
            if client_obj is not self.client:
                try:
                    client_obj.close()
                except Exception:
                    pass

        return results

    def __enter__(self) -> NotebookContext:
        return self

    def __exit__(self, *args: Any) -> None:
        self.teardown()

    def __repr__(self) -> str:
        parts = [f"NotebookContext(api_url={self.api_url!r}", f"hub_user={self.hub_user!r}"]
        if self.prefix:
            parts.append(f"prefix={self.prefix!r}")
            parts.append(f"run_id={self.run_id!r}")
        resource_count = len(self._resources) + len(self._tracked_instances) + len(self._tracked_mappings)
        parts.append(f"resources={resource_count}")
        return ", ".join(parts) + ")"


def setup(
    api_url: str | None = None,
    *,
    prefix: str | None = None,
    persona: Persona | None = None,
) -> NotebookContext:
    """Set up the notebook environment.

    **Tutorial mode** (no ``prefix``): three pre-built clients (alice, carol, dave).
    **E2E test mode** (with ``prefix`` and ``persona``): single primary client.
    """
    if prefix and not persona:
        raise ValueError("persona is required when prefix is set (E2E test mode)")

    resolved_url = _get_api_url(api_url)
    hub_user = _get_hub_user()

    return NotebookContext(
        api_url=resolved_url,
        hub_user=hub_user,
        prefix=prefix,
        persona=persona,
    )
