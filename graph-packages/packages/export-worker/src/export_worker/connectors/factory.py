"""Connector factory — instantiates the right DataConnector for a source type."""

from __future__ import annotations

from typing import Any

import structlog

from export_worker.connectors.base import DataConnector

logger = structlog.get_logger()

# Registry of supported source types -> connector classes (lazy imports to
# avoid pulling in optional dependencies at module load time).
_CONNECTOR_REGISTRY: dict[str, str] = {
    "starburst": "export_worker.connectors.starburst.StarburstConnector",
    "bigquery": "export_worker.connectors.bigquery.BigQueryConnector",
    "snowflake": "export_worker.connectors.snowflake.SnowflakeConnector",
    "databricks": "export_worker.connectors.databricks.DatabricksConnector",
    "file": "export_worker.connectors.file_source.FileSourceConnector",
    "s3": "export_worker.connectors.file_source.FileSourceConnector",
    "gcs": "export_worker.connectors.file_source.FileSourceConnector",
    "csv": "export_worker.connectors.file_source.FileSourceConnector",
}


def _import_class(dotted_path: str) -> type:
    """Import a class from a dotted module path."""
    module_path, class_name = dotted_path.rsplit(".", 1)
    import importlib

    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def create_connector(
    source_type: str,
    config: dict[str, Any],
    credentials: dict[str, Any],
) -> DataConnector:
    """Create a DataConnector for the given source type.

    Args:
        source_type: One of starburst, bigquery, snowflake, databricks,
                     file, s3, gcs, csv.
        config: Source-specific configuration dict.
        credentials: Source-specific credentials dict.

    Returns:
        An initialised DataConnector instance.

    Raises:
        ValueError: If source_type is not supported.
    """
    source_type = source_type.lower().strip()
    dotted_path = _CONNECTOR_REGISTRY.get(source_type)

    if dotted_path is None:
        supported = ", ".join(sorted(_CONNECTOR_REGISTRY))
        raise ValueError(
            f"Unknown data source type: '{source_type}'. "
            f"Supported types: {supported}"
        )

    cls = _import_class(dotted_path)

    logger.info(
        "Creating data connector",
        source_type=source_type,
        connector_class=cls.__name__,
    )

    return cls(config, credentials)
