"""File/Storage connector for S3, GCS, and local CSV/Parquet sources.

Reads Parquet or CSV files from cloud storage using PyArrow filesystem
abstractions and re-exports to GCS as Parquet.
"""

from __future__ import annotations

from typing import Any

import structlog

from export_worker.connectors.base import DataConnector

logger = structlog.get_logger()


class FileSourceConnector(DataConnector):
    """Connector for cloud storage file sources (S3, GCS, CSV).

    Config keys: bucket, prefix, region, file_format (parquet|csv)
    Credential keys:
      - S3: access_key, secret_key
      - GCS: service_account_json (JSON string or dict)
    """

    def __init__(self, config: dict[str, Any], credentials: dict[str, Any]) -> None:
        super().__init__(config, credentials)

        self._bucket = config.get("bucket", "")
        self._prefix = config.get("prefix", "")
        self._region = config.get("region", "us-east-1")
        self._file_format = config.get("file_format", "parquet").lower()
        self._logger = logger.bind(
            connector="file_source",
            bucket=self._bucket,
            prefix=self._prefix,
            file_format=self._file_format,
        )

    def _get_filesystem(self) -> Any:
        """Create the appropriate PyArrow filesystem.

        Returns an S3 or GCS filesystem depending on credentials.
        """
        import pyarrow.fs as pafs

        access_key = self.credentials.get("access_key")
        secret_key = self.credentials.get("secret_key")
        sa_json = self.credentials.get("service_account_json")

        if access_key and secret_key:
            return pafs.S3FileSystem(
                access_key=access_key,
                secret_key=secret_key,
                region=self._region,
            )

        if sa_json:
            import json
            import os
            import tempfile

            if isinstance(sa_json, str):
                sa_json = json.loads(sa_json)
            # Write SA key to temp file for pyarrow GCS auth
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as f:
                json.dump(sa_json, f)
                key_path = f.name
            try:
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path
                return pafs.GcsFileSystem()
            finally:
                # Clean env but leave file — pyarrow may still need it
                pass

        # Default: use Application Default Credentials for GCS
        return pafs.GcsFileSystem()

    def _read_source(self) -> "pa.Table":  # noqa: F821
        """Read the source data from cloud storage into a PyArrow table."""
        import pyarrow.csv as pcsv
        import pyarrow.parquet as pq

        fs = self._get_filesystem()
        base_path = f"{self._bucket}/{self._prefix}".rstrip("/")

        if self._file_format == "csv":
            # Read all CSV files under the prefix
            file_info = fs.get_file_info(
                pyarrow_fs_selector(base_path, recursive=True)
            )
            csv_paths = [
                fi.path for fi in file_info if fi.path.endswith(".csv")
            ]
            if not csv_paths:
                raise FileNotFoundError(
                    f"No CSV files found under {base_path}"
                )
            tables = [pcsv.read_csv(fs.open_input_stream(p)) for p in csv_paths]
            import pyarrow as pa

            return pa.concat_tables(tables)
        else:
            # Parquet — use dataset reader for partitioned data
            return pq.read_table(base_path, filesystem=fs)

    async def execute_query(self, sql: str) -> tuple[list[str], list[list[Any]]]:
        """File sources do not support SQL.

        This reads all data from the configured path and returns it.
        The ``sql`` parameter is ignored.
        """
        import asyncio

        self._logger.info("Reading file source (SQL ignored)")

        def _run() -> tuple[list[str], list[list[Any]]]:
            table = self._read_source()
            columns = table.column_names
            rows = [
                [table.column(col)[i].as_py() for col in columns]
                for i in range(table.num_rows)
            ]
            return columns, rows

        return await asyncio.get_running_loop().run_in_executor(None, _run)

    async def execute_and_export_parquet(
        self, sql: str, gcs_path: str
    ) -> tuple[int, int]:
        """Read source files and re-export as Parquet to GCS."""
        import asyncio

        self._logger.info(
            "Re-exporting file source as Parquet", gcs_path=gcs_path
        )

        def _run() -> "pa.Table":  # noqa: F821
            return self._read_source()

        table = await asyncio.get_running_loop().run_in_executor(None, _run)

        if table.num_rows == 0:
            self._logger.warning("File source contains no rows", gcs_path=gcs_path)
            return 0, 0

        return self._write_parquet_to_gcs(table, gcs_path)

    async def test_connection(self) -> tuple[bool, str]:
        """Test that the configured bucket/prefix is accessible."""
        try:
            fs = self._get_filesystem()
            base_path = f"{self._bucket}/{self._prefix}".rstrip("/")
            info = fs.get_file_info(base_path)
            if info.type.name == "NotFound":
                return False, f"Path not found: {base_path}"
            return True, "File source accessible"
        except Exception as e:
            return False, f"File source connection failed: {e}"

    async def close(self) -> None:
        """No persistent resources for file source connector."""
        self._logger.debug("File source connector closed")


def pyarrow_fs_selector(base_path: str, recursive: bool = True) -> Any:
    """Create a PyArrow FileSelector."""
    import pyarrow.fs as pafs

    return pafs.FileSelector(base_path, recursive=recursive)
