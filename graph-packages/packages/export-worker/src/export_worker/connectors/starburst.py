"""Starburst connector — wraps the existing StarburstClient."""

from __future__ import annotations

from typing import Any

import structlog

from export_worker.clients.starburst import StarburstClient
from export_worker.connectors.base import DataConnector

logger = structlog.get_logger()


class StarburstConnector(DataConnector):
    """Connector for Starburst/Trino data sources.

    Wraps the existing StarburstClient to conform to the DataConnector
    interface.  Constructor accepts config/credentials dicts so it can
    be created uniformly via the connector factory.

    Config keys: host, port, catalog, schema, role, ssl_verify, source
    Credential keys: user, password
    """

    def __init__(self, config: dict[str, Any], credentials: dict[str, Any]) -> None:
        super().__init__(config, credentials)

        host = config.get("host", "localhost")
        port = config.get("port", 8080)
        protocol = "https" if config.get("ssl_verify", True) else "http"
        url = f"{protocol}://{host}:{port}"

        self._client = StarburstClient(
            url=url,
            user=credentials.get("user", ""),
            password=credentials.get("password", ""),
            catalog=config.get("catalog", "bigquery"),
            schema=config.get("schema", "public"),
            role=config.get("role"),
            ssl_verify=config.get("ssl_verify", True),
            source=config.get("source", "graph-olap-export-worker"),
            gcp_project=config.get("gcp_project"),
        )
        self._logger = logger.bind(connector="starburst", host=host, port=port)

    async def execute_query(self, sql: str) -> tuple[list[str], list[list[Any]]]:
        """Execute SQL via Starburst and return columns + rows."""
        import httpx

        self._logger.info("Executing query via Starburst", sql_preview=sql[:120])

        columns: list[str] = []
        rows: list[list[Any]] = []

        async with httpx.AsyncClient(
            auth=self._client.auth,
            timeout=self._client.request_timeout,
            verify=self._client.ssl_verify,
        ) as client:
            await self._client._set_role_async(client, self._client.catalog)

            response = await client.post(
                f"{self._client.url}/v1/statement",
                content=sql,
                headers=self._client._get_headers(self._client.catalog),
            )
            response.raise_for_status()
            result = response.json()

            if "error" in result:
                raise RuntimeError(result["error"].get("message", "Query error"))

            if "columns" in result:
                columns = [c["name"] for c in result["columns"]]
            if "data" in result:
                rows.extend(result["data"])

            next_uri = result.get("nextUri")
            while next_uri:
                response = await client.get(next_uri)
                response.raise_for_status()
                result = response.json()

                if "error" in result:
                    raise RuntimeError(result["error"].get("message", "Query error"))
                if "columns" in result and not columns:
                    columns = [c["name"] for c in result["columns"]]
                if "data" in result:
                    rows.extend(result["data"])
                next_uri = result.get("nextUri")

        return columns, rows

    async def execute_and_export_parquet(
        self, sql: str, gcs_path: str
    ) -> tuple[int, int]:
        """Execute query and export as Parquet to GCS.

        Delegates to the existing StarburstClient direct-export method.
        """
        self._logger.info(
            "Executing export via Starburst",
            gcs_path=gcs_path,
            sql_preview=sql[:120],
        )

        # We need column names for the export.  Infer from a cheap DESCRIBE.
        columns_meta = self._client.validate_query(sql)
        column_names = [c["name"] for c in columns_meta]

        row_count, size_bytes = await self._client.execute_and_export_async(
            sql=sql,
            columns=column_names,
            destination=gcs_path,
        )
        return row_count, size_bytes

    async def test_connection(self) -> tuple[bool, str]:
        """Test Starburst connectivity with a trivial query."""
        try:
            cols, rows = await self.execute_query("SELECT 1 AS health")
            if rows:
                return True, "Starburst connection successful"
            return False, "Query returned no rows"
        except Exception as e:
            return False, f"Starburst connection failed: {e}"

    async def close(self) -> None:
        """No persistent resources to clean up for Starburst HTTP client."""
        self._logger.debug("Starburst connector closed")
