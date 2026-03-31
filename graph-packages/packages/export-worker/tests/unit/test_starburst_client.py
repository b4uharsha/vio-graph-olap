"""Unit tests for StarburstClient."""

from __future__ import annotations

import httpx
import pytest
import respx

from export_worker.clients import StarburstClient
from export_worker.clients.starburst import QueryPollResult, QuerySubmissionResult
from export_worker.exceptions import StarburstError


class TestStarburstClient:
    """Tests for StarburstClient."""

    @pytest.fixture
    def client(self) -> StarburstClient:
        """Create client for testing."""
        return StarburstClient(
            url="http://starburst.test:8080",
            user="test_user",
            password="test_password",
            catalog="analytics",
            schema="public",
            request_timeout=60,
        )

    @pytest.fixture
    def unload_columns(self) -> list[str]:
        """Sample columns for UNLOAD tests."""
        return ["customer_id", "name", "email"]

    @pytest.fixture
    def source_sql(self) -> str:
        """Sample SQL for UNLOAD tests."""
        return "SELECT customer_id, name, email FROM customers"

    @respx.mock
    def test_validate_query_success(self, client: StarburstClient) -> None:
        """Test successful query validation."""
        respx.post("http://starburst.test:8080/v1/statement").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "query-123",
                    "nextUri": "http://starburst.test:8080/v1/statement/query-123/1",
                },
            )
        )

        respx.get("http://starburst.test:8080/v1/statement/query-123/1").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "query-123",
                    "data": [
                        ["customer_id", "varchar"],
                        ["name", "varchar"],
                        ["amount", "double"],
                    ],
                },
            )
        )

        columns = client.validate_query("SELECT customer_id, name, amount FROM t")

        assert len(columns) == 3
        assert columns[0] == {"name": "customer_id", "type": "varchar"}
        assert columns[1] == {"name": "name", "type": "varchar"}
        assert columns[2] == {"name": "amount", "type": "double"}

    @respx.mock
    def test_validate_query_invalid(self, client: StarburstClient) -> None:
        """Test validation of invalid query."""
        respx.post("http://starburst.test:8080/v1/statement").mock(
            return_value=httpx.Response(
                200,
                json={
                    "error": {
                        "message": "Table 'nonexistent' does not exist",
                        "errorCode": "TABLE_NOT_FOUND",
                    }
                },
            )
        )

        with pytest.raises(StarburstError) as exc_info:
            client.validate_query("SELECT * FROM nonexistent")

        assert "does not exist" in str(exc_info.value)

    def test_build_unload_query(
        self,
        client: StarburstClient,
        unload_columns: list[str],
        source_sql: str,
    ) -> None:
        """Test UNLOAD query building."""
        query = client._build_unload_query(
            sql=source_sql,
            columns=unload_columns,
            destination="gs://test-bucket/export/",
        )

        # Verify query structure
        assert "SELECT * FROM TABLE(" in query
        assert "system.unload(" in query
        assert '"customer_id", "name", "email"' in query
        assert source_sql in query
        assert "gs://test-bucket/export/" in query
        assert "format => 'PARQUET'" in query
        assert "compression => 'SNAPPY'" in query

    def test_build_unload_query_special_columns(self, client: StarburstClient) -> None:
        """Test UNLOAD query with reserved word columns."""
        columns = ["select", "from", "where", "order"]
        sql = "SELECT * FROM t"

        query = client._build_unload_query(
            sql=sql,
            columns=columns,
            destination="gs://bucket/path/",
        )

        # Reserved words should be quoted
        assert '"select"' in query
        assert '"from"' in query
        assert '"where"' in query
        assert '"order"' in query


class TestStarburstAsyncAPI:
    """Tests for async API (ADR-025) - submit_unload and poll_query."""

    @pytest.fixture
    def client(self) -> StarburstClient:
        """Create client for testing."""
        return StarburstClient(
            url="http://starburst.test:8080",
            user="test_user",
            password="test_password",
            catalog="analytics",
            schema="public",
        )

    @pytest.fixture
    def unload_columns(self) -> list[str]:
        """Sample columns for UNLOAD tests."""
        return ["customer_id", "name", "email"]

    @pytest.fixture
    def source_sql(self) -> str:
        """Sample SQL for UNLOAD tests."""
        return "SELECT customer_id, name, email FROM customers"

    @respx.mock
    def test_submit_unload_returns_query_id_and_next_uri(
        self,
        client: StarburstClient,
        unload_columns: list[str],
        source_sql: str,
    ) -> None:
        """submit_unload returns query ID and nextUri for polling."""
        respx.post("http://starburst.test:8080/v1/statement").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "query-abc-123",
                    "nextUri": "http://starburst.test:8080/v1/statement/query-abc-123/1",
                    "stats": {"state": "QUEUED"},
                },
            )
        )

        result = client.submit_unload(
            sql=source_sql,
            columns=unload_columns,
            destination="gs://test-bucket/export/",
        )

        assert isinstance(result, QuerySubmissionResult)
        assert result.query_id == "query-abc-123"
        assert result.next_uri == "http://starburst.test:8080/v1/statement/query-abc-123/1"

    @respx.mock
    def test_submit_unload_raises_on_immediate_error(
        self,
        client: StarburstClient,
        unload_columns: list[str],
        source_sql: str,
    ) -> None:
        """submit_unload raises StarburstError on immediate query error."""
        respx.post("http://starburst.test:8080/v1/statement").mock(
            return_value=httpx.Response(
                200,
                json={
                    "error": {
                        "message": "Table not found: customers",
                        "errorCode": "TABLE_NOT_FOUND",
                    }
                },
            )
        )

        with pytest.raises(StarburstError) as exc_info:
            client.submit_unload(
                sql=source_sql,
                columns=unload_columns,
                destination="gs://test-bucket/export/",
            )

        assert "Table not found" in str(exc_info.value)

    @respx.mock
    def test_submit_unload_raises_on_missing_next_uri(
        self,
        client: StarburstClient,
        unload_columns: list[str],
        source_sql: str,
    ) -> None:
        """submit_unload raises StarburstError if response missing nextUri."""
        respx.post("http://starburst.test:8080/v1/statement").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "query-123",
                    # Missing nextUri
                },
            )
        )

        with pytest.raises(StarburstError) as exc_info:
            client.submit_unload(
                sql=source_sql,
                columns=unload_columns,
                destination="gs://test-bucket/export/",
            )

        assert "missing id or nextUri" in str(exc_info.value)

    @respx.mock
    def test_poll_query_returns_finished(self, client: StarburstClient) -> None:
        """poll_query returns FINISHED state when query completes."""
        respx.get("http://starburst.test:8080/v1/statement/query-123/1").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "query-123",
                    "stats": {"state": "FINISHED", "completedSplits": 10},
                },
            )
        )

        result = client.poll_query("http://starburst.test:8080/v1/statement/query-123/1")

        assert isinstance(result, QueryPollResult)
        assert result.state == "FINISHED"
        assert result.next_uri is None
        assert result.error_message is None

    @respx.mock
    def test_poll_query_returns_running_with_next_uri(self, client: StarburstClient) -> None:
        """poll_query returns RUNNING state with updated nextUri."""
        respx.get("http://starburst.test:8080/v1/statement/query-123/1").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "query-123",
                    "nextUri": "http://starburst.test:8080/v1/statement/query-123/2",
                    "stats": {"state": "RUNNING", "completedSplits": 5},
                },
            )
        )

        result = client.poll_query("http://starburst.test:8080/v1/statement/query-123/1")

        assert result.state == "RUNNING"
        assert result.next_uri == "http://starburst.test:8080/v1/statement/query-123/2"
        assert result.error_message is None

    @respx.mock
    def test_poll_query_returns_failed_with_error(self, client: StarburstClient) -> None:
        """poll_query returns FAILED state with error message."""
        respx.get("http://starburst.test:8080/v1/statement/query-123/1").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "query-123",
                    "error": {
                        "message": "Query cancelled by user",
                        "errorCode": "USER_CANCELLED",
                    },
                },
            )
        )

        result = client.poll_query("http://starburst.test:8080/v1/statement/query-123/1")

        assert result.state == "FAILED"
        assert result.next_uri is None
        assert "Query cancelled" in result.error_message

    @respx.mock
    def test_poll_query_raises_on_http_error(self, client: StarburstClient) -> None:
        """poll_query raises StarburstError on HTTP errors."""
        respx.get("http://starburst.test:8080/v1/statement/query-123/1").mock(
            return_value=httpx.Response(503)
        )

        with pytest.raises(StarburstError) as exc_info:
            client.poll_query("http://starburst.test:8080/v1/statement/query-123/1")

        assert "503" in str(exc_info.value)

    @respx.mock
    def test_poll_query_handles_all_intermediate_states(self, client: StarburstClient) -> None:
        """poll_query maps QUEUED, PLANNING, STARTING states to RUNNING."""
        for state in ["QUEUED", "PLANNING", "STARTING", "RUNNING", "FINISHING"]:
            respx.get("http://starburst.test:8080/v1/statement/query-123/1").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "id": "query-123",
                        "nextUri": "http://starburst.test:8080/v1/statement/query-123/2",
                        "stats": {"state": state},
                    },
                )
            )

            result = client.poll_query("http://starburst.test:8080/v1/statement/query-123/1")
            assert result.state == "RUNNING", f"State {state} should map to RUNNING"
            respx.reset()


class TestStarburstAsyncMethods:
    """Tests for async versions of submit/poll methods."""

    @pytest.fixture
    def client(self) -> StarburstClient:
        """Create client for testing."""
        return StarburstClient(
            url="http://starburst.test:8080",
            user="test_user",
            password="test_password",
            catalog="analytics",
            schema="public",
        )

    @pytest.mark.asyncio
    @respx.mock
    async def test_submit_unload_async_success(self, client: StarburstClient) -> None:
        """Test submit_unload_async returns query ID and next_uri."""
        respx.post("http://starburst.test:8080/v1/statement").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "query-async-123",
                    "nextUri": "http://starburst.test:8080/v1/statement/query-async-123/1",
                    "stats": {"state": "QUEUED"},
                },
            )
        )

        result = await client.submit_unload_async(
            sql="SELECT * FROM test",
            columns=["id", "name"],
            destination="gs://bucket/path/",
        )

        assert result.query_id == "query-async-123"
        assert result.next_uri == "http://starburst.test:8080/v1/statement/query-async-123/1"

    @pytest.mark.asyncio
    @respx.mock
    async def test_submit_unload_async_raises_on_error(self, client: StarburstClient) -> None:
        """Test submit_unload_async raises on immediate error."""
        respx.post("http://starburst.test:8080/v1/statement").mock(
            return_value=httpx.Response(
                200,
                json={
                    "error": {
                        "message": "Syntax error",
                        "errorCode": "SYNTAX_ERROR",
                    }
                },
            )
        )

        with pytest.raises(StarburstError) as exc_info:
            await client.submit_unload_async(
                sql="SELECT * FROM test",
                columns=["id"],
                destination="gs://bucket/path/",
            )

        assert "Syntax error" in str(exc_info.value)

    @pytest.mark.asyncio
    @respx.mock
    async def test_submit_unload_async_raises_on_http_error(self, client: StarburstClient) -> None:
        """Test submit_unload_async raises on HTTP error."""
        respx.post("http://starburst.test:8080/v1/statement").mock(
            return_value=httpx.Response(500)
        )

        with pytest.raises(StarburstError) as exc_info:
            await client.submit_unload_async(
                sql="SELECT * FROM test",
                columns=["id"],
                destination="gs://bucket/path/",
            )

        assert "500" in str(exc_info.value)

    @pytest.mark.asyncio
    @respx.mock
    async def test_submit_unload_async_raises_on_missing_fields(self, client: StarburstClient) -> None:
        """Test submit_unload_async raises when response missing id/nextUri."""
        respx.post("http://starburst.test:8080/v1/statement").mock(
            return_value=httpx.Response(
                200,
                json={"stats": {"state": "QUEUED"}},  # Missing id and nextUri
            )
        )

        with pytest.raises(StarburstError) as exc_info:
            await client.submit_unload_async(
                sql="SELECT * FROM test",
                columns=["id"],
                destination="gs://bucket/path/",
            )

        assert "missing id or nextUri" in str(exc_info.value)

    @pytest.mark.asyncio
    @respx.mock
    async def test_poll_query_async_finished(self, client: StarburstClient) -> None:
        """Test poll_query_async returns FINISHED state."""
        respx.get("http://starburst.test:8080/v1/query/123").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "query-123",
                    "stats": {"state": "FINISHED", "completedSplits": 10},
                },
            )
        )

        result = await client.poll_query_async("http://starburst.test:8080/v1/query/123")

        assert result.state == "FINISHED"
        assert result.next_uri is None
        assert result.error_message is None

    @pytest.mark.asyncio
    @respx.mock
    async def test_poll_query_async_running(self, client: StarburstClient) -> None:
        """Test poll_query_async returns RUNNING with next_uri."""
        respx.get("http://starburst.test:8080/v1/query/123").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "query-123",
                    "nextUri": "http://starburst.test:8080/v1/query/123/2",
                    "stats": {"state": "RUNNING"},
                },
            )
        )

        result = await client.poll_query_async("http://starburst.test:8080/v1/query/123")

        assert result.state == "RUNNING"
        assert result.next_uri == "http://starburst.test:8080/v1/query/123/2"

    @pytest.mark.asyncio
    @respx.mock
    async def test_poll_query_async_failed(self, client: StarburstClient) -> None:
        """Test poll_query_async returns FAILED with error."""
        respx.get("http://starburst.test:8080/v1/query/123").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "query-123",
                    "error": {
                        "message": "Out of memory",
                        "errorCode": "EXCEEDED_MEMORY_LIMIT",
                    },
                },
            )
        )

        result = await client.poll_query_async("http://starburst.test:8080/v1/query/123")

        assert result.state == "FAILED"
        assert "Out of memory" in result.error_message

    @pytest.mark.asyncio
    @respx.mock
    async def test_poll_query_async_raises_on_http_error(self, client: StarburstClient) -> None:
        """Test poll_query_async raises on HTTP error."""
        respx.get("http://starburst.test:8080/v1/query/123").mock(
            return_value=httpx.Response(503)
        )

        with pytest.raises(StarburstError) as exc_info:
            await client.poll_query_async("http://starburst.test:8080/v1/query/123")

        assert "503" in str(exc_info.value)


class TestStarburstRoleHandling:
    """Tests for SET ROLE functionality."""

    @pytest.fixture
    def client_with_role(self) -> StarburstClient:
        """Create client with role configured."""
        return StarburstClient(
            url="http://starburst.test:8080",
            user="test_user",
            password="test_password",
            catalog="analytics",
            schema="public",
            role="admin_role",
        )

    @pytest.fixture
    def client_without_role(self) -> StarburstClient:
        """Create client without role."""
        return StarburstClient(
            url="http://starburst.test:8080",
            user="test_user",
            password="test_password",
            catalog="analytics",
            schema="public",
        )

    def test_get_headers_includes_role(self, client_with_role: StarburstClient) -> None:
        """Test that role is included in headers when configured."""
        headers = client_with_role._get_headers("analytics")
        assert headers["X-Trino-Role"] == "admin_role"

    def test_get_headers_excludes_role_when_not_set(self, client_without_role: StarburstClient) -> None:
        """Test that role is not in headers when not configured."""
        headers = client_without_role._get_headers("analytics")
        assert "X-Trino-Role" not in headers

    @respx.mock
    def test_set_role_sync_sends_set_role(self, client_with_role: StarburstClient) -> None:
        """Test that _set_role_sync sends SET ROLE statement."""
        route = respx.post("http://starburst.test:8080/v1/statement").mock(
            return_value=httpx.Response(200, json={})
        )

        with httpx.Client(timeout=30) as http_client:
            client_with_role._set_role_sync(http_client, "analytics")

        assert route.called

    @respx.mock
    def test_set_role_sync_skips_when_no_role(self, client_without_role: StarburstClient) -> None:
        """Test that _set_role_sync does nothing when no role."""
        route = respx.post("http://starburst.test:8080/v1/statement").mock(
            return_value=httpx.Response(200, json={})
        )

        with httpx.Client(timeout=30) as http_client:
            client_without_role._set_role_sync(http_client, "analytics")

        assert not route.called

    @respx.mock
    def test_set_role_sync_handles_failure(self, client_with_role: StarburstClient) -> None:
        """Test that _set_role_sync handles failure gracefully."""
        respx.post("http://starburst.test:8080/v1/statement").mock(
            return_value=httpx.Response(500, text="Error")
        )

        with httpx.Client(timeout=30) as http_client:
            # Should not raise
            client_with_role._set_role_sync(http_client, "analytics")

    @pytest.mark.asyncio
    @respx.mock
    async def test_set_role_async_sends_set_role(self, client_with_role: StarburstClient) -> None:
        """Test that _set_role_async sends SET ROLE statement."""
        route = respx.post("http://starburst.test:8080/v1/statement").mock(
            return_value=httpx.Response(200, json={})
        )

        async with httpx.AsyncClient(timeout=30) as http_client:
            await client_with_role._set_role_async(http_client, "analytics")

        assert route.called

    @pytest.mark.asyncio
    @respx.mock
    async def test_set_role_async_skips_when_no_role(self, client_without_role: StarburstClient) -> None:
        """Test that _set_role_async does nothing when no role."""
        route = respx.post("http://starburst.test:8080/v1/statement").mock(
            return_value=httpx.Response(200, json={})
        )

        async with httpx.AsyncClient(timeout=30) as http_client:
            await client_without_role._set_role_async(http_client, "analytics")

        assert not route.called

    @pytest.mark.asyncio
    @respx.mock
    async def test_set_role_async_handles_failure(self, client_with_role: StarburstClient) -> None:
        """Test that _set_role_async handles failure gracefully."""
        respx.post("http://starburst.test:8080/v1/statement").mock(
            return_value=httpx.Response(500, text="Error")
        )

        async with httpx.AsyncClient(timeout=30) as http_client:
            # Should not raise
            await client_with_role._set_role_async(http_client, "analytics")


class TestStarburstSubmitUnloadErrors:
    """Tests for submit_unload error paths."""

    @pytest.fixture
    def client(self) -> StarburstClient:
        """Create client for testing."""
        return StarburstClient(
            url="http://starburst.test:8080",
            user="test_user",
            password="test_password",
            catalog="analytics",
            schema="public",
        )

    @respx.mock
    def test_submit_unload_http_error(self, client: StarburstClient) -> None:
        """Test submit_unload raises on HTTP status error."""
        respx.post("http://starburst.test:8080/v1/statement").mock(
            return_value=httpx.Response(500, text="Server Error")
        )

        with pytest.raises(StarburstError) as exc_info:
            client.submit_unload(
                sql="SELECT * FROM t",
                columns=["id"],
                destination="gs://bucket/path/",
            )

        assert "500" in str(exc_info.value)

    @respx.mock
    def test_poll_query_request_error(self, client: StarburstClient) -> None:
        """Test poll_query raises on request error."""
        respx.get("http://starburst.test:8080/v1/query/123").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        with pytest.raises(StarburstError):
            client.poll_query("http://starburst.test:8080/v1/query/123")

    @respx.mock
    def test_poll_query_failed_state_from_stats(self, client: StarburstClient) -> None:
        """Test poll_query returns FAILED from stats state."""
        respx.get("http://starburst.test:8080/v1/query/123").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "query-123",
                    "stats": {"state": "FAILED"},
                },
            )
        )

        result = client.poll_query("http://starburst.test:8080/v1/query/123")
        assert result.state == "FAILED"
        assert result.error_message == "Query failed"


class TestStarburstClientNoPassword:
    """Test client auth with no password."""

    def test_no_password_disables_auth(self) -> None:
        """Test that empty password disables basic auth."""
        client = StarburstClient(
            url="http://starburst.test:8080",
            user="test_user",
            password="",
            catalog="analytics",
        )
        assert client.auth is None

    def test_password_enables_auth(self) -> None:
        """Test that non-empty password enables basic auth."""
        client = StarburstClient(
            url="http://starburst.test:8080",
            user="test_user",
            password="secret",
            catalog="analytics",
        )
        assert client.auth == ("test_user", "secret")


class TestStarburstValidateQueryErrors:
    """Tests for validate_query error paths."""

    @pytest.fixture
    def client(self) -> StarburstClient:
        """Create client for testing."""
        return StarburstClient(
            url="http://starburst.test:8080",
            user="test_user",
            password="test_password",
            catalog="analytics",
            schema="public",
        )

    @respx.mock
    def test_validate_query_http_error(self, client: StarburstClient) -> None:
        """Test validate_query raises on HTTP error."""
        respx.post("http://starburst.test:8080/v1/statement").mock(
            return_value=httpx.Response(500, text="Error")
        )

        with pytest.raises(StarburstError):
            client.validate_query("SELECT * FROM t")


class TestStarburstAsyncPollErrors:
    """Tests for async poll error paths."""

    @pytest.fixture
    def client(self) -> StarburstClient:
        """Create client for testing."""
        return StarburstClient(
            url="http://starburst.test:8080",
            user="test_user",
            password="test_password",
            catalog="analytics",
            schema="public",
        )

    @pytest.mark.asyncio
    @respx.mock
    async def test_poll_query_async_request_error(self, client: StarburstClient) -> None:
        """Test async poll raises on request error."""
        respx.get("http://starburst.test:8080/v1/query/123").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        with pytest.raises(StarburstError):
            await client.poll_query_async("http://starburst.test:8080/v1/query/123")

    @pytest.mark.asyncio
    @respx.mock
    async def test_submit_unload_async_request_error(self, client: StarburstClient) -> None:
        """Test async submit raises on request error."""
        respx.post("http://starburst.test:8080/v1/statement").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        with pytest.raises(StarburstError):
            await client.submit_unload_async(
                sql="SELECT * FROM t",
                columns=["id"],
                destination="gs://bucket/path/",
            )

    @pytest.mark.asyncio
    @respx.mock
    async def test_poll_query_async_failed_from_stats(self, client: StarburstClient) -> None:
        """Test async poll returns FAILED from stats state."""
        respx.get("http://starburst.test:8080/v1/query/123").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "query-123",
                    "stats": {"state": "FAILED"},
                },
            )
        )

        result = await client.poll_query_async("http://starburst.test:8080/v1/query/123")
        assert result.state == "FAILED"


class TestStarburstClientFromConfig:
    """Tests for StarburstClient.from_config()."""

    def test_from_config_creates_client(self, mock_env: None) -> None:
        """Test that from_config creates properly configured client."""
        from export_worker.config import StarburstConfig

        config = StarburstConfig()
        client = StarburstClient.from_config(config)

        assert client.url == "http://starburst.test:8080"
        assert client.auth == ("test_user", "test_password")
        assert client.catalog == "analytics"
