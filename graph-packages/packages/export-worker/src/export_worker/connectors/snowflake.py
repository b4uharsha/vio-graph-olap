"""Snowflake connector using snowflake-connector-python."""

from __future__ import annotations

from typing import Any

import structlog

from export_worker.connectors.base import DataConnector

logger = structlog.get_logger()


class SnowflakeConnector(DataConnector):
    """Connector for Snowflake.

    Config keys: account, warehouse, database, schema
    Credential keys: user, password
    """

    def __init__(self, config: dict[str, Any], credentials: dict[str, Any]) -> None:
        super().__init__(config, credentials)

        self._account = config.get("account", "")
        self._warehouse = config.get("warehouse", "")
        self._database = config.get("database", "")
        self._schema = config.get("schema", "public")
        self._user = credentials.get("user", "")
        self._password = credentials.get("password", "")
        self._conn: Any = None  # Lazy init
        self._logger = logger.bind(
            connector="snowflake",
            account=self._account,
            database=self._database,
        )

    def _get_connection(self) -> Any:
        """Lazily create the Snowflake connection."""
        if self._conn is not None:
            return self._conn

        import snowflake.connector

        self._conn = snowflake.connector.connect(
            account=self._account,
            user=self._user,
            password=self._password,
            warehouse=self._warehouse,
            database=self._database,
            schema=self._schema,
        )
        return self._conn

    async def execute_query(self, sql: str) -> tuple[list[str], list[list[Any]]]:
        """Execute SQL on Snowflake and return columns + rows."""
        import asyncio

        self._logger.info("Executing Snowflake query", sql_preview=sql[:120])

        def _run() -> tuple[list[str], list[list[Any]]]:
            conn = self._get_connection()
            cur = conn.cursor()
            try:
                cur.execute(sql)
                columns = [desc[0] for desc in cur.description] if cur.description else []
                rows = [list(row) for row in cur.fetchall()]
                return columns, rows
            finally:
                cur.close()

        return await asyncio.get_running_loop().run_in_executor(None, _run)

    async def execute_and_export_parquet(
        self, sql: str, gcs_path: str
    ) -> tuple[int, int]:
        """Execute Snowflake query and write Parquet to GCS."""
        import asyncio

        import pyarrow as pa

        self._logger.info(
            "Executing Snowflake export", gcs_path=gcs_path, sql_preview=sql[:120]
        )

        def _run() -> pa.Table:
            conn = self._get_connection()
            cur = conn.cursor()
            try:
                cur.execute(sql)
                # Use fetch_arrow_all for efficient Arrow conversion
                table = cur.fetch_arrow_all()
                if table is None:
                    return pa.table({})
                return table
            finally:
                cur.close()

        table = await asyncio.get_running_loop().run_in_executor(None, _run)

        if table.num_rows == 0:
            self._logger.warning(
                "Snowflake query returned no rows", gcs_path=gcs_path
            )
            return 0, 0

        return self._write_parquet_to_gcs(table, gcs_path)

    async def test_connection(self) -> tuple[bool, str]:
        """Test Snowflake connectivity."""
        try:
            cols, rows = await self.execute_query("SELECT 1 AS health")
            if rows:
                return True, "Snowflake connection successful"
            return False, "Query returned no rows"
        except Exception as e:
            return False, f"Snowflake connection failed: {e}"

    async def close(self) -> None:
        """Close the Snowflake connection."""
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception as e:
                self._logger.warning("Error closing Snowflake connection", error=str(e))
            finally:
                self._conn = None
        self._logger.debug("Snowflake connector closed")
