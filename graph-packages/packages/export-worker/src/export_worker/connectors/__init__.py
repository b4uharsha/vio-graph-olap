"""Connector plugin architecture for dynamic data sources.

Provides a unified interface for querying different data platforms
(Starburst, BigQuery, Snowflake, Databricks, file/storage) and
exporting results as Parquet to GCS.
"""

from export_worker.connectors.base import DataConnector
from export_worker.connectors.factory import create_connector

__all__ = [
    "DataConnector",
    "create_connector",
]
