"""Graph OLAP SDK - Python client for Graph OLAP Platform.

A full-featured Python SDK for analysts working in Jupyter notebooks,
providing both control plane operations and graph query/algorithm interface.

Quick Start:
    >>> from graph_olap import notebook
    >>> client = notebook.connect()  # Auto-discovers from environment

    >>> # Or with explicit configuration
    >>> from graph_olap import GraphOLAPClient
    >>> client = GraphOLAPClient(
    ...     api_url="https://graph-olap.example.com",
    ...     api_key="sk-xxx",
    ... )

Example Workflow:
    >>> from graph_olap import notebook
    >>> client = notebook.connect()

    >>> # Create snapshot and instance
    >>> snapshot = client.snapshots.create_and_wait(mapping_id=1, name="Analysis")
    >>> instance = client.instances.create_and_wait(snapshot_id=snapshot.id, name="Analysis")

    >>> # Connect and query
    >>> conn = client.instances.connect(instance.id)
    >>> result = conn.query("MATCH (n:Customer)-[p]->(pr:Product) RETURN n, p, pr")
    >>> result.show()  # Auto-selects best visualization

    >>> # Run algorithms
    >>> conn.networkx.run("pagerank", node_label="Customer", property_name="pr")

    >>> # Export results
    >>> df = conn.query_df("MATCH (n) RETURN n.name, n.pr")
    >>> df.to_csv("results.csv")

    >>> # Clean up
    >>> client.instances.terminate(instance.id)
"""

from graph_olap.client import GraphOLAPClient
from graph_olap.config import Config
from graph_olap.exceptions import (
    AlgorithmFailedError,
    AlgorithmNotFoundError,
    AlgorithmTimeoutError,
    AuthenticationError,
    ConcurrencyLimitError,
    ConflictError,
    DependencyError,
    GraphOLAPError,
    InstanceFailedError,
    InvalidStateError,
    NotFoundError,
    PermissionDeniedError,
    QueryTimeoutError,
    ResourceLockedError,
    RyugraphError,
    ServerError,
    SnapshotFailedError,
    TimeoutError,
    ValidationError,
)
from graph_olap.models import (
    AlgorithmExecution,
    ClusterHealth,
    ClusterInstances,
    ComponentHealth,
    ConcurrencyConfig,
    EdgeDefinition,
    ExportConfig,
    Favorite,
    HealthStatus,
    Instance,
    InstanceLimits,
    InstanceProgress,
    LifecycleConfig,
    LockStatus,
    MaintenanceMode,
    Mapping,
    MappingVersion,
    NodeDefinition,
    OwnerInstanceCount,
    PaginatedList,
    QueryResult,
    ResourceLifecycleConfig,
    Schema,
    # SNAPSHOT FUNCTIONALITY DISABLED
    # Snapshots are now created implicitly when instances are created from mappings.
    # Snapshot,
    # SnapshotProgress,
)
from graph_olap.testing import NotebookTest, PersonaConfig, TestPersona

__version__ = "0.1.0"

__all__ = [
    "AlgorithmExecution",
    "AlgorithmFailedError",
    "AlgorithmNotFoundError",
    "AlgorithmTimeoutError",
    "AuthenticationError",
    "ClusterHealth",
    "ClusterInstances",
    "ComponentHealth",
    "ConcurrencyConfig",
    "ConcurrencyLimitError",
    "Config",
    "ConflictError",
    "DependencyError",
    "EdgeDefinition",
    "ExportConfig",
    "Favorite",
    # Main client
    "GraphOLAPClient",
    # Exceptions
    "GraphOLAPError",
    "HealthStatus",
    "Instance",
    "InstanceFailedError",
    "InstanceLimits",
    "InstanceProgress",
    "InvalidStateError",
    "LifecycleConfig",
    "LockStatus",
    "MaintenanceMode",
    # Models - Core
    "Mapping",
    "MappingVersion",
    "NodeDefinition",
    # Testing
    "NotebookTest",
    "NotFoundError",
    "OwnerInstanceCount",
    "PaginatedList",
    "PermissionDeniedError",
    "PersonaConfig",
    "QueryResult",
    "QueryTimeoutError",
    # Models - Ops
    "ResourceLifecycleConfig",
    "ResourceLockedError",
    "RyugraphError",
    "Schema",
    "ServerError",
    # SNAPSHOT FUNCTIONALITY DISABLED
    # Snapshots are now created implicitly when instances are created from mappings.
    # "Snapshot",
    "SnapshotFailedError",  # Keep exception for backward compatibility
    # "SnapshotProgress",
    # Testing
    "TestPersona",
    "TimeoutError",
    "ValidationError",
]
