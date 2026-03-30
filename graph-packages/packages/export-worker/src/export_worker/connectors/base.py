"""Abstract base connector for all data source plugins."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import structlog

logger = structlog.get_logger()


class DataConnector(ABC):
    """Abstract base for all data source connectors.

    Each connector wraps a specific data platform client and provides
    a uniform interface for query execution, Parquet export, and
    connection testing.
    """

    def __init__(self, config: dict[str, Any], credentials: dict[str, Any]) -> None:
        self.config = config
        self.credentials = credentials
        self._logger = logger.bind(connector=self.__class__.__name__)

    @abstractmethod
    async def execute_query(self, sql: str) -> tuple[list[str], list[list[Any]]]:
        """Execute SQL and return (columns, rows).

        Args:
            sql: SQL query to execute.

        Returns:
            Tuple of (column_names, rows) where each row is a list of values.
        """

    @abstractmethod
    async def execute_and_export_parquet(
        self, sql: str, gcs_path: str
    ) -> tuple[int, int]:
        """Execute query and write results to GCS as Parquet.

        Args:
            sql: SQL query to execute.
            gcs_path: GCS destination path (gs://bucket/path/).

        Returns:
            Tuple of (row_count, size_bytes).
        """

    @abstractmethod
    async def test_connection(self) -> tuple[bool, str]:
        """Test connectivity to the data source.

        Returns:
            Tuple of (success, message).
        """

    @abstractmethod
    async def close(self) -> None:
        """Clean up resources (connections, temp files, etc.)."""

    # -- Shared helpers --------------------------------------------------------

    def _write_parquet_to_gcs(
        self,
        table: "pa.Table",  # noqa: F821
        gcs_path: str,
        gcp_project: str | None = None,
    ) -> tuple[int, int]:
        """Write a PyArrow table to GCS as a single Parquet file.

        Args:
            table: PyArrow table to write.
            gcs_path: GCS destination (gs://bucket/path/).
            gcp_project: Optional GCP project for the storage client.

        Returns:
            Tuple of (row_count, size_bytes).
        """
        import os
        import tempfile

        import pyarrow.parquet as pq
        from google.cloud import storage

        if not gcs_path.startswith("gs://"):
            raise ValueError(f"Invalid GCS path: {gcs_path}")

        path_without_prefix = gcs_path[5:]
        parts = path_without_prefix.split("/", 1)
        bucket_name = parts[0]
        blob_prefix = parts[1] if len(parts) > 1 else ""

        if blob_prefix and not blob_prefix.endswith("/"):
            blob_prefix += "/"

        blob_name = f"{blob_prefix}data.parquet"

        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
            temp_path = f.name
            pq.write_table(table, temp_path, compression="snappy")

        try:
            size_bytes = os.path.getsize(temp_path)
            gcs_client = storage.Client(project=gcp_project)
            bucket = gcs_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            blob.upload_from_filename(temp_path)

            self._logger.debug(
                "Uploaded Parquet to GCS",
                bucket=bucket_name,
                blob=blob_name,
                row_count=table.num_rows,
                size_bytes=size_bytes,
            )
        finally:
            os.unlink(temp_path)

        return (table.num_rows, size_bytes)
