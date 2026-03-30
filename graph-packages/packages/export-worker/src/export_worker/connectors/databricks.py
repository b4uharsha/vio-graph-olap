"""Databricks connector using databricks-sql-connector."""

from __future__ import annotations

from typing import Any

import structlog

from export_worker.connectors.base import DataConnector

logger = structlog.get_logger()


class DatabricksConnector(DataConnector):
    """Connector for Databricks SQL Warehouses.

    Config keys: host, http_path, catalog, schema
    Credential keys: token
    """

    def __init__(self, config: dict[str, Any], credentials: dict[str, Any]) -> None:
        super().__init__(config, credentials)

        self._host = config.get("host", "")
        self._http_path = config.get("http_path", "")
        self._catalog = config.get("catalog", "")
        self._schema = config.get("schema", "default")
        self._token = credentials.get("token", "")
        self._conn: Any = None  # Lazy init
        self._logger = logger.bind(
            connector="databricks",
            host=self._host,
            catalog=self._catalog,
        )

    def _get_connection(self) -> Any:
        """Lazily create the Databricks connection."""
        if self._conn is not None:
            return self._conn

        from databricks import sql as dbsql

        self._conn = dbsql.connect(
            server_hostname=self._host,
            http_path=self._http_path,
            access_token=self._token,
            catalog=self._catalog,
            schema=self._schema,
        )
        return self._conn

    async def execute_query(self, sql: str) -> tuple[list[str], list[list[Any]]]:
        """Execute SQL on Databricks and return columns + rows."""
        import asyncio

        self._logger.info("Executing Databricks query", sql_preview=sql[:120])

        def _run() -> tuple[list[str], list[list[Any]]]:
            conn = self._get_connection()
            cur = conn.cursor()
            try:
                cur.execute(sql)
                columns = (
                    [desc[0] for desc in cur.description] if cur.description else []
                )
                rows = [list(row) for row in cur.fetchall()]
                return columns, rows
            finally:
                cur.close()

        return await asyncio.get_running_loop().run_in_executor(None, _run)

    async def execute_and_export_parquet(
        self, sql: str, gcs_path: str
    ) -> tuple[int, int]:
        """Execute Databricks query and write Parquet to GCS."""
        import asyncio

        import pyarrow as pa

        self._logger.info(
            "Executing Databricks export", gcs_path=gcs_path, sql_preview=sql[:120]
        )

        def _run() -> pa.Table:
            conn = self._get_connection()
            cur = conn.cursor()
            try:
                cur.execute(sql)
                # Use fetch_arrow_all when available (databricks-sql-connector >=2.7)
                if hasattr(cur, "fetchall_arrow"):
                    return cur.fetchall_arrow()

                # Fallback: manual Arrow construction
                columns = (
                    [desc[0] for desc in cur.description] if cur.description else []
                )
                rows = cur.fetchall()
                if not rows:
                    return pa.table({})
                col_data = {
                    col: [row[i] for row in rows] for i, col in enumerate(columns)
                }
                return pa.table(col_data)
            finally:
                cur.close()

        table = await asyncio.get_running_loop().run_in_executor(None, _run)

        if table.num_rows == 0:
            self._logger.warning(
                "Databricks query returned no rows", gcs_path=gcs_path
            )
            return 0, 0

        return self._write_parquet_to_gcs(table, gcs_path)

    async def test_connection(self) -> tuple[bool, str]:
        """Test Databricks connectivity."""
        try:
            cols, rows = await self.execute_query("SELECT 1 AS health")
            if rows:
                return True, "Databricks connection successful"
            return False, "Query returned no rows"
        except Exception as e:
            return False, f"Databricks connection failed: {e}"

    async def close(self) -> None:
        """Close the Databricks connection."""
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception as e:
                self._logger.warning(
                    "Error closing Databricks connection", error=str(e)
                )
            finally:
                self._conn = None
        self._logger.debug("Databricks connector closed")
