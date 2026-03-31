"""Unit tests for connector factory and connector classes."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from export_worker.connectors.base import DataConnector
from export_worker.connectors.factory import _import_class, create_connector


class TestImportClass:
    """Tests for _import_class helper."""

    def test_import_known_class(self) -> None:
        """Test importing a known class from a dotted path."""
        cls = _import_class("export_worker.connectors.base.DataConnector")
        assert cls is DataConnector

    def test_import_invalid_module(self) -> None:
        """Test importing from a nonexistent module."""
        with pytest.raises(ModuleNotFoundError):
            _import_class("nonexistent.module.SomeClass")

    def test_import_invalid_class(self) -> None:
        """Test importing a nonexistent class from a valid module."""
        with pytest.raises(AttributeError):
            _import_class("export_worker.connectors.base.NonExistentClass")


class TestCreateConnector:
    """Tests for create_connector factory function."""

    def test_unknown_source_type_raises(self) -> None:
        """Test that unknown source type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown data source type"):
            create_connector(source_type="oracle", config={}, credentials={})

    def test_unknown_source_lists_supported(self) -> None:
        """Test that error message lists supported types."""
        with pytest.raises(ValueError, match="bigquery"):
            create_connector(source_type="oracle", config={}, credentials={})

    def test_source_type_case_insensitive(self) -> None:
        """Test that source type is case-insensitive."""
        with patch("export_worker.connectors.factory._import_class") as mock_import:
            mock_cls = MagicMock()
            mock_cls.__name__ = "MockConnector"
            mock_import.return_value = mock_cls

            create_connector(source_type="  BigQuery  ", config={"a": 1}, credentials={"b": 2})

            mock_cls.assert_called_once_with({"a": 1}, {"b": 2})

    def test_create_starburst_connector(self) -> None:
        """Test creating a Starburst connector."""
        connector = create_connector(
            source_type="starburst",
            config={"host": "localhost", "port": 8080, "catalog": "hive"},
            credentials={"user": "admin", "password": "secret"},
        )
        assert isinstance(connector, DataConnector)

    def test_create_file_connector(self) -> None:
        """Test creating a file connector."""
        connector = create_connector(
            source_type="file",
            config={"bucket": "test-bucket", "prefix": "data/"},
            credentials={},
        )
        assert isinstance(connector, DataConnector)

    def test_create_s3_connector(self) -> None:
        """Test creating an S3 connector (maps to file source)."""
        connector = create_connector(
            source_type="s3",
            config={"bucket": "test-bucket"},
            credentials={"access_key": "ak", "secret_key": "sk"},
        )
        assert isinstance(connector, DataConnector)

    def test_create_csv_connector(self) -> None:
        """Test creating a CSV connector (maps to file source)."""
        connector = create_connector(
            source_type="csv",
            config={"bucket": "test-bucket"},
            credentials={},
        )
        assert isinstance(connector, DataConnector)

    def test_create_gcs_connector(self) -> None:
        """Test creating a GCS connector (maps to file source)."""
        connector = create_connector(
            source_type="gcs",
            config={"bucket": "test-bucket"},
            credentials={},
        )
        assert isinstance(connector, DataConnector)


class TestBigQueryConnector:
    """Tests for BigQueryConnector."""

    def test_init_stores_config(self) -> None:
        """Test that BigQueryConnector stores config."""
        from export_worker.connectors.bigquery import BigQueryConnector

        connector = BigQueryConnector(
            config={"project_id": "my-proj", "dataset": "my_ds", "location": "EU"},
            credentials={},
        )
        assert connector._project_id == "my-proj"
        assert connector._dataset == "my_ds"
        assert connector._location == "EU"

    def test_init_defaults(self) -> None:
        """Test default values."""
        from export_worker.connectors.bigquery import BigQueryConnector

        connector = BigQueryConnector(config={}, credentials={})
        assert connector._project_id == ""
        assert connector._location == "US"

    @pytest.mark.asyncio
    async def test_close_clears_client(self) -> None:
        """Test close sets client to None."""
        from export_worker.connectors.bigquery import BigQueryConnector

        connector = BigQueryConnector(config={}, credentials={})
        mock_client = MagicMock()
        connector._client = mock_client

        await connector.close()

        mock_client.close.assert_called_once()
        assert connector._client is None

    @pytest.mark.asyncio
    async def test_close_when_no_client(self) -> None:
        """Test close when no client initialized."""
        from export_worker.connectors.bigquery import BigQueryConnector

        connector = BigQueryConnector(config={}, credentials={})
        await connector.close()  # Should not raise

    @pytest.mark.asyncio
    async def test_test_connection_failure(self) -> None:
        """Test test_connection on failure."""
        from export_worker.connectors.bigquery import BigQueryConnector

        connector = BigQueryConnector(config={}, credentials={})
        connector.execute_query = AsyncMock(side_effect=RuntimeError("No BQ"))

        ok, msg = await connector.test_connection()
        assert ok is False
        assert "failed" in msg.lower()


class TestSnowflakeConnector:
    """Tests for SnowflakeConnector."""

    def test_init_stores_config(self) -> None:
        """Test that SnowflakeConnector stores config."""
        from export_worker.connectors.snowflake import SnowflakeConnector

        connector = SnowflakeConnector(
            config={"account": "acct", "warehouse": "wh", "database": "db", "schema": "sc"},
            credentials={"user": "u", "password": "p"},
        )
        assert connector._account == "acct"
        assert connector._warehouse == "wh"
        assert connector._database == "db"
        assert connector._schema == "sc"

    @pytest.mark.asyncio
    async def test_close_clears_connection(self) -> None:
        """Test close sets connection to None."""
        from export_worker.connectors.snowflake import SnowflakeConnector

        connector = SnowflakeConnector(config={}, credentials={})
        mock_conn = MagicMock()
        connector._conn = mock_conn

        await connector.close()

        mock_conn.close.assert_called_once()
        assert connector._conn is None

    @pytest.mark.asyncio
    async def test_close_handles_error(self) -> None:
        """Test close handles error during close."""
        from export_worker.connectors.snowflake import SnowflakeConnector

        connector = SnowflakeConnector(config={}, credentials={})
        mock_conn = MagicMock()
        mock_conn.close.side_effect = RuntimeError("Close error")
        connector._conn = mock_conn

        await connector.close()  # Should not raise
        assert connector._conn is None

    @pytest.mark.asyncio
    async def test_test_connection_failure(self) -> None:
        """Test test_connection on failure."""
        from export_worker.connectors.snowflake import SnowflakeConnector

        connector = SnowflakeConnector(config={}, credentials={})
        connector.execute_query = AsyncMock(side_effect=RuntimeError("No Snowflake"))

        ok, msg = await connector.test_connection()
        assert ok is False
        assert "failed" in msg.lower()


class TestDatabricksConnector:
    """Tests for DatabricksConnector."""

    def test_init_stores_config(self) -> None:
        """Test that DatabricksConnector stores config."""
        from export_worker.connectors.databricks import DatabricksConnector

        connector = DatabricksConnector(
            config={"host": "h", "http_path": "/sql", "catalog": "c", "schema": "s"},
            credentials={"token": "tk"},
        )
        assert connector._host == "h"
        assert connector._http_path == "/sql"
        assert connector._catalog == "c"
        assert connector._token == "tk"

    @pytest.mark.asyncio
    async def test_close_clears_connection(self) -> None:
        """Test close sets connection to None."""
        from export_worker.connectors.databricks import DatabricksConnector

        connector = DatabricksConnector(config={}, credentials={})
        mock_conn = MagicMock()
        connector._conn = mock_conn

        await connector.close()

        mock_conn.close.assert_called_once()
        assert connector._conn is None

    @pytest.mark.asyncio
    async def test_close_handles_error(self) -> None:
        """Test close handles error during close."""
        from export_worker.connectors.databricks import DatabricksConnector

        connector = DatabricksConnector(config={}, credentials={})
        mock_conn = MagicMock()
        mock_conn.close.side_effect = RuntimeError("Close error")
        connector._conn = mock_conn

        await connector.close()  # Should not raise
        assert connector._conn is None

    @pytest.mark.asyncio
    async def test_test_connection_failure(self) -> None:
        """Test test_connection on failure."""
        from export_worker.connectors.databricks import DatabricksConnector

        connector = DatabricksConnector(config={}, credentials={})
        connector.execute_query = AsyncMock(side_effect=RuntimeError("No DB"))

        ok, msg = await connector.test_connection()
        assert ok is False
        assert "failed" in msg.lower()


class TestStarburstConnector:
    """Tests for StarburstConnector."""

    def test_init_creates_client(self) -> None:
        """Test that StarburstConnector creates a StarburstClient."""
        from export_worker.connectors.starburst import StarburstConnector

        connector = StarburstConnector(
            config={"host": "starburst.local", "port": 443, "catalog": "hive"},
            credentials={"user": "admin", "password": "pass"},
        )
        assert connector._client is not None
        assert connector._client.catalog == "hive"

    def test_init_ssl_verify_false_uses_http(self) -> None:
        """Test that ssl_verify=False uses http protocol."""
        from export_worker.connectors.starburst import StarburstConnector

        connector = StarburstConnector(
            config={"host": "starburst.local", "port": 8080, "ssl_verify": False},
            credentials={"user": "admin"},
        )
        assert connector._client.url.startswith("http://")

    @pytest.mark.asyncio
    async def test_close_does_not_raise(self) -> None:
        """Test close completes without error."""
        from export_worker.connectors.starburst import StarburstConnector

        connector = StarburstConnector(
            config={"host": "localhost"},
            credentials={"user": "test"},
        )
        await connector.close()  # Should not raise

    @pytest.mark.asyncio
    async def test_test_connection_failure(self) -> None:
        """Test test_connection on failure."""
        from export_worker.connectors.starburst import StarburstConnector

        connector = StarburstConnector(
            config={"host": "localhost"},
            credentials={"user": "test"},
        )
        connector.execute_query = AsyncMock(side_effect=RuntimeError("No Starburst"))

        ok, msg = await connector.test_connection()
        assert ok is False
        assert "failed" in msg.lower()


class TestFileSourceConnector:
    """Tests for FileSourceConnector."""

    def test_init_stores_config(self) -> None:
        """Test that FileSourceConnector stores config."""
        from export_worker.connectors.file_source import FileSourceConnector

        connector = FileSourceConnector(
            config={"bucket": "bkt", "prefix": "pfx", "region": "eu-west-1", "file_format": "csv"},
            credentials={},
        )
        assert connector._bucket == "bkt"
        assert connector._prefix == "pfx"
        assert connector._region == "eu-west-1"
        assert connector._file_format == "csv"

    def test_init_defaults(self) -> None:
        """Test default values."""
        from export_worker.connectors.file_source import FileSourceConnector

        connector = FileSourceConnector(config={}, credentials={})
        assert connector._file_format == "parquet"
        assert connector._region == "us-east-1"

    def test_extract_file_from_sql(self) -> None:
        """Test SQL parsing for file path extraction."""
        from export_worker.connectors.file_source import FileSourceConnector

        connector = FileSourceConnector(config={}, credentials={})

        result = connector._extract_file_from_sql("SELECT * FROM game-of-thrones/characters.csv")
        assert result == "game-of-thrones/characters.csv"

    def test_extract_file_from_sql_no_match(self) -> None:
        """Test SQL parsing returns None on non-matching SQL."""
        from export_worker.connectors.file_source import FileSourceConnector

        connector = FileSourceConnector(config={}, credentials={})

        result = connector._extract_file_from_sql("INSERT INTO foo VALUES (1)")
        assert result is None

    @pytest.mark.asyncio
    async def test_close_does_not_raise(self) -> None:
        """Test close completes without error."""
        from export_worker.connectors.file_source import FileSourceConnector

        connector = FileSourceConnector(config={}, credentials={})
        await connector.close()  # Should not raise


class TestBaseConnector:
    """Tests for DataConnector base class."""

    def test_cannot_instantiate_abstract(self) -> None:
        """Test that DataConnector cannot be instantiated directly."""
        with pytest.raises(TypeError):
            DataConnector({}, {})  # type: ignore
