"""BigQuery connector using google-cloud-bigquery + PyArrow."""

from __future__ import annotations

import json
from typing import Any

import structlog

from export_worker.connectors.base import DataConnector

logger = structlog.get_logger()


class BigQueryConnector(DataConnector):
    """Connector for Google BigQuery.

    Config keys: project_id, dataset, location
    Credential keys: service_account_json (JSON string or dict)
    """

    def __init__(self, config: dict[str, Any], credentials: dict[str, Any]) -> None:
        super().__init__(config, credentials)

        self._project_id = config.get("project_id", "")
        self._dataset = config.get("dataset", "")
        self._location = config.get("location", "US")
        self._client: Any = None  # Lazy init
        self._logger = logger.bind(
            connector="bigquery",
            project_id=self._project_id,
            dataset=self._dataset,
        )

    def _get_client(self) -> Any:
        """Lazily initialise the BigQuery client."""
        if self._client is not None:
            return self._client

        from google.cloud import bigquery
        from google.oauth2 import service_account as sa

        sa_json = self.credentials.get("service_account_json")
        if sa_json:
            if isinstance(sa_json, str):
                sa_json = json.loads(sa_json)
            creds = sa.Credentials.from_service_account_info(sa_json)
            self._client = bigquery.Client(
                project=self._project_id, credentials=creds, location=self._location
            )
        else:
            # Fall back to Application Default Credentials
            self._client = bigquery.Client(
                project=self._project_id, location=self._location
            )

        return self._client

    async def execute_query(self, sql: str) -> tuple[list[str], list[list[Any]]]:
        """Execute SQL on BigQuery and return columns + rows."""
        import asyncio

        self._logger.info("Executing BigQuery query", sql_preview=sql[:120])
        client = self._get_client()

        # BigQuery client is synchronous — run in executor
        def _run() -> tuple[list[str], list[list[Any]]]:
            query_job = client.query(sql)
            result = query_job.result()
            columns = [field.name for field in result.schema]
            rows = [list(row.values()) for row in result]
            return columns, rows

        return await asyncio.get_running_loop().run_in_executor(None, _run)

    async def execute_and_export_parquet(
        self, sql: str, gcs_path: str
    ) -> tuple[int, int]:
        """Execute BigQuery query and write Parquet to GCS."""
        import asyncio

        import pyarrow as pa

        self._logger.info(
            "Executing BigQuery export", gcs_path=gcs_path, sql_preview=sql[:120]
        )
        client = self._get_client()

        def _run() -> pa.Table:
            query_job = client.query(sql)
            return query_job.result().to_arrow()

        table = await asyncio.get_running_loop().run_in_executor(None, _run)

        if table.num_rows == 0:
            self._logger.warning("BigQuery query returned no rows", gcs_path=gcs_path)
            return 0, 0

        return self._write_parquet_to_gcs(
            table, gcs_path, gcp_project=self._project_id
        )

    async def test_connection(self) -> tuple[bool, str]:
        """Test BigQuery connectivity."""
        try:
            cols, rows = await self.execute_query("SELECT 1 AS health")
            if rows:
                return True, "BigQuery connection successful"
            return False, "Query returned no rows"
        except Exception as e:
            return False, f"BigQuery connection failed: {e}"

    async def close(self) -> None:
        """Close the BigQuery client."""
        if self._client is not None:
            self._client.close()
            self._client = None
        self._logger.debug("BigQuery connector closed")
