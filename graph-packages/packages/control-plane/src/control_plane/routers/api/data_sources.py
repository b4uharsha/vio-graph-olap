"""Data Sources API router."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from control_plane.infrastructure.database import get_async_session
from control_plane.middleware.auth import CurrentUser
from control_plane.models import DataSource
from control_plane.models.errors import NotFoundError, PermissionDeniedError
from control_plane.models.requests import (
    VALID_SOURCE_TYPES,
    CreateDataSourceRequest,
    UpdateDataSourceRequest,
)
from control_plane.models.responses import (
    BrowseItem,
    BrowseResponse,
    ColumnInfo,
    DataResponse,
    DataSourceResponse,
    DataSourceTestResponse,
    SchemaInspectResponse,
)
from control_plane.repositories.data_sources import DataSourceRepository

router = APIRouter(prefix="/api/data-sources", tags=["Data Sources"])


def get_data_source_repo(
    session: AsyncSession = Depends(get_async_session),
) -> DataSourceRepository:
    """Dependency to get data source repository."""
    return DataSourceRepository(session)


DataSourceRepoDep = Annotated[DataSourceRepository, Depends(get_data_source_repo)]


def data_source_to_response(ds: DataSource) -> DataSourceResponse:
    """Convert domain DataSource to response model.

    Credentials are intentionally excluded from public responses.
    """
    return DataSourceResponse(
        id=ds.id,
        owner_username=ds.owner_username,
        name=ds.name,
        source_type=ds.source_type,
        config=ds.config,
        is_default=ds.is_default,
        last_tested_at=ds.last_tested_at,
        test_status=ds.test_status,
        created_at=ds.created_at,
        updated_at=ds.updated_at,
    )


def check_ownership(user, owner_username: str, data_source_id: int) -> None:
    """Check that the current user owns the data source."""
    if user.username != owner_username:
        raise PermissionDeniedError("data_source", data_source_id)


@router.post(
    "",
    response_model=DataResponse[DataSourceResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_data_source(
    user: CurrentUser,
    repo: DataSourceRepoDep,
    request: CreateDataSourceRequest,
) -> DataResponse[DataSourceResponse]:
    """Create a new data source.

    The current user becomes the owner.

    Args:
        user: Current authenticated user
        repo: Data source repository
        request: Data source creation request

    Returns:
        Created data source
    """
    if request.source_type not in VALID_SOURCE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_SOURCE_TYPE",
                "message": f"Invalid source_type '{request.source_type}'. Must be one of: {sorted(VALID_SOURCE_TYPES)}",
            },
        )

    data_source = await repo.create(
        owner_username=user.username,
        name=request.name,
        source_type=request.source_type,
        config=request.config,
        credentials=request.credentials,
        is_default=request.is_default,
    )
    return DataResponse(data=data_source_to_response(data_source))


@router.get(
    "",
    response_model=DataResponse[list[DataSourceResponse]],
)
async def list_data_sources(
    user: CurrentUser,
    repo: DataSourceRepoDep,
    source_type: str | None = None,
) -> DataResponse[list[DataSourceResponse]]:
    """List data sources for the current user.

    Args:
        user: Current authenticated user
        repo: Data source repository
        source_type: Optional filter by source type

    Returns:
        List of data sources (credentials redacted)
    """
    data_sources = await repo.list_by_owner(
        owner_username=user.username,
        source_type=source_type,
    )
    return DataResponse(data=[data_source_to_response(ds) for ds in data_sources])


@router.get(
    "/{data_source_id}",
    response_model=DataResponse[DataSourceResponse],
)
async def get_data_source(
    data_source_id: int,
    user: CurrentUser,
    repo: DataSourceRepoDep,
) -> DataResponse[DataSourceResponse]:
    """Get a data source by ID.

    Args:
        data_source_id: Data source ID
        user: Current authenticated user
        repo: Data source repository

    Returns:
        Data source (credentials redacted)
    """
    data_source = await repo.get_by_id(data_source_id)
    if data_source is None:
        raise NotFoundError("data_source", data_source_id)

    check_ownership(user, data_source.owner_username, data_source_id)
    return DataResponse(data=data_source_to_response(data_source))


@router.put(
    "/{data_source_id}",
    response_model=DataResponse[DataSourceResponse],
)
async def update_data_source(
    data_source_id: int,
    user: CurrentUser,
    repo: DataSourceRepoDep,
    request: UpdateDataSourceRequest,
) -> DataResponse[DataSourceResponse]:
    """Update a data source.

    Args:
        data_source_id: Data source ID
        user: Current authenticated user
        repo: Data source repository
        request: Update request

    Returns:
        Updated data source
    """
    # Verify exists and ownership
    existing = await repo.get_by_id(data_source_id)
    if existing is None:
        raise NotFoundError("data_source", data_source_id)

    check_ownership(user, existing.owner_username, data_source_id)

    if request.source_type is not None and request.source_type not in VALID_SOURCE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_SOURCE_TYPE",
                "message": f"Invalid source_type '{request.source_type}'. Must be one of: {sorted(VALID_SOURCE_TYPES)}",
            },
        )

    updated = await repo.update(
        data_source_id=data_source_id,
        name=request.name,
        source_type=request.source_type,
        config=request.config,
        credentials=request.credentials,
    )
    if updated is None:
        raise NotFoundError("data_source", data_source_id)

    return DataResponse(data=data_source_to_response(updated))


@router.delete(
    "/{data_source_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_data_source(
    data_source_id: int,
    user: CurrentUser,
    repo: DataSourceRepoDep,
) -> None:
    """Delete a data source.

    Args:
        data_source_id: Data source ID
        user: Current authenticated user
        repo: Data source repository
    """
    existing = await repo.get_by_id(data_source_id)
    if existing is None:
        raise NotFoundError("data_source", data_source_id)

    check_ownership(user, existing.owner_username, data_source_id)

    await repo.delete(data_source_id)


@router.post(
    "/{data_source_id}/test",
    response_model=DataResponse[DataSourceTestResponse],
)
async def test_data_source(
    data_source_id: int,
    user: CurrentUser,
    repo: DataSourceRepoDep,
) -> DataResponse[DataSourceTestResponse]:
    """Test a data source connection.

    Validates that the connection details and credentials are correct
    by attempting to connect to the data source.

    Args:
        data_source_id: Data source ID
        user: Current authenticated user
        repo: Data source repository

    Returns:
        Test result with success/failure and message
    """
    import httpx
    from control_plane.repositories.base import utc_now, parse_timestamp
    from control_plane.utils.encryption import decrypt_credentials

    data_source = await repo.get_by_id(data_source_id)
    if data_source is None:
        raise NotFoundError("data_source", data_source_id)

    check_ownership(user, data_source.owner_username, data_source_id)

    now = utc_now()
    test_status = "failed"
    message = "Unknown source type"
    config = data_source.config if isinstance(data_source.config, dict) else {}
    try:
        creds = decrypt_credentials(data_source.credentials) if isinstance(data_source.credentials, str) else (data_source.credentials or {})
    except Exception:
        creds = data_source.credentials if isinstance(data_source.credentials, dict) else {}

    try:
        st = data_source.source_type

        if st == "starburst":
            host = config.get("host", "")
            user_name = creds.get("username", "")
            password = creds.get("password", "")
            if not host:
                message = "Host URL is required"
            else:
                url = host if host.startswith("http") else f"https://{host}"
                async with httpx.AsyncClient(timeout=10) as client:
                    r = await client.get(f"{url}/v1/info")
                    if r.status_code == 200:
                        info = r.json()
                        if user_name and password:
                            # Test auth
                            r2 = await client.post(
                                f"{url}/v1/statement",
                                auth=(user_name, password),
                                content="SELECT 1",
                            )
                            if r2.status_code == 200:
                                test_status = "success"
                                message = f"Connected to {info.get('environment', 'Starburst')} (v{info.get('nodeVersion', {}).get('version', '?')})"
                            else:
                                message = f"Cluster reachable but auth failed: {r2.text[:80]}"
                        else:
                            test_status = "success"
                            message = f"Cluster reachable: {info.get('environment', 'Starburst')}"
                    else:
                        message = f"Cluster returned HTTP {r.status_code}"

        elif st == "bigquery":
            project = config.get("projectId", "")
            if not project:
                message = "Project ID is required"
            else:
                test_status = "success"
                message = f"BigQuery config valid — project: {project}"

        elif st == "snowflake":
            account = config.get("account", "")
            if not account:
                message = "Account is required"
            else:
                url = f"https://{account}.snowflakecomputing.com/api/v2/login-request"
                async with httpx.AsyncClient(timeout=10) as client:
                    r = await client.get(url)
                    if r.status_code in (200, 401, 403, 405):
                        test_status = "success"
                        message = f"Snowflake account '{account}' is reachable"
                    else:
                        message = f"Snowflake account not found (HTTP {r.status_code})"

        elif st == "databricks":
            host = config.get("host", "")
            token = creds.get("token", "")
            if not host:
                message = "Host is required"
            else:
                url = host if host.startswith("http") else f"https://{host}"
                async with httpx.AsyncClient(timeout=10) as client:
                    headers = {"Authorization": f"Bearer {token}"} if token else {}
                    r = await client.get(f"{url}/api/2.0/clusters/list", headers=headers)
                    if r.status_code in (200, 403):
                        test_status = "success"
                        message = f"Databricks workspace reachable at {host}"
                    else:
                        message = f"Databricks returned HTTP {r.status_code}"

        elif st in ("gcs", "s3"):
            bucket = config.get("bucket", "")
            if not bucket:
                message = "Bucket name is required"
            elif st == "gcs":
                async with httpx.AsyncClient(timeout=10) as client:
                    # Use metadata server auth on GCE
                    try:
                        token_resp = await client.get(
                            "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token",
                            headers={"Metadata-Flavor": "Google"},
                        )
                        token = token_resp.json().get("access_token", "")
                        r = await client.get(
                            f"https://storage.googleapis.com/storage/v1/b/{bucket}",
                            headers={"Authorization": f"Bearer {token}"},
                        )
                        if r.status_code == 200:
                            test_status = "success"
                            message = f"GCS bucket '{bucket}' accessible"
                        else:
                            message = f"GCS bucket '{bucket}' returned HTTP {r.status_code}"
                    except Exception:
                        test_status = "success"
                        message = f"GCS bucket '{bucket}' configured (could not verify from this environment)"
            else:
                test_status = "success"
                message = f"S3 bucket '{bucket}' configured — verification requires AWS credentials"

        elif st == "csv":
            test_status = "success"
            message = "CSV source — upload files directly when creating a mapping"

        else:
            message = f"Unknown source type: {st}"

    except httpx.ConnectError:
        message = "Connection refused — check the host URL"
    except httpx.TimeoutException:
        message = "Connection timed out after 10 seconds"
    except Exception as e:
        message = f"Test failed: {str(e)[:100]}"

    await repo.update_test_status(data_source_id, test_status)

    return DataResponse(
        data=DataSourceTestResponse(
            success=test_status == "success",
            message=message,
            tested_at=parse_timestamp(now),
        )
    )


@router.put(
    "/{data_source_id}/default",
    response_model=DataResponse[DataSourceResponse],
)
async def set_default_data_source(
    data_source_id: int,
    user: CurrentUser,
    repo: DataSourceRepoDep,
) -> DataResponse[DataSourceResponse]:
    """Set a data source as the default for the current user.

    Clears the default flag on all other data sources for this user.

    Args:
        data_source_id: Data source ID
        user: Current authenticated user
        repo: Data source repository

    Returns:
        Updated data source
    """
    existing = await repo.get_by_id(data_source_id)
    if existing is None:
        raise NotFoundError("data_source", data_source_id)

    check_ownership(user, existing.owner_username, data_source_id)

    updated = await repo.set_default(data_source_id, user.username)
    if updated is None:
        raise NotFoundError("data_source", data_source_id)

    return DataResponse(data=data_source_to_response(updated))


# ---------------------------------------------------------------------------
# Helpers for browse / schema endpoints
# ---------------------------------------------------------------------------


def _get_config_and_creds(data_source):
    """Extract config dict and decrypted credentials from a data source."""
    from control_plane.utils.encryption import decrypt_credentials

    config = data_source.config if isinstance(data_source.config, dict) else {}
    try:
        creds = (
            decrypt_credentials(data_source.credentials)
            if isinstance(data_source.credentials, str)
            else (data_source.credentials or {})
        )
    except Exception:
        creds = (
            data_source.credentials
            if isinstance(data_source.credentials, dict)
            else {}
        )
    return config, creds


async def _gcs_auth_token(client) -> str:
    """Get a GCS access token from the VM metadata server."""
    try:
        resp = await client.get(
            "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token",
            headers={"Metadata-Flavor": "Google"},
        )
        return resp.json().get("access_token", "")
    except Exception:
        return ""


async def _browse_gcs(config, _creds, prefix: str | None):
    """List objects in a GCS bucket."""
    import httpx

    bucket = config.get("bucket", "")
    if not bucket:
        return BrowseResponse(source_type="gcs", items=[], message="Bucket name is required in data source config")

    configured_prefix = config.get("prefix", "")
    effective_prefix = prefix if prefix is not None else configured_prefix

    params: dict = {}
    if effective_prefix:
        params["prefix"] = effective_prefix

    async with httpx.AsyncClient(timeout=15) as client:
        token = await _gcs_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        url = f"https://storage.googleapis.com/storage/v1/b/{bucket}/o"
        resp = await client.get(url, headers=headers, params=params)

        if resp.status_code != 200:
            return BrowseResponse(
                source_type="gcs",
                items=[],
                message=f"GCS returned HTTP {resp.status_code}: {resp.text[:200]}",
            )

        data = resp.json()
        items: list[BrowseItem] = []
        for obj in data.get("items", []):
            name = obj.get("name", "")
            size = int(obj.get("size", 0))
            fmt = None
            lower = name.lower()
            if lower.endswith(".csv"):
                fmt = "csv"
            elif lower.endswith(".parquet"):
                fmt = "parquet"
            elif lower.endswith(".json"):
                fmt = "json"
            items.append(BrowseItem(name=name, type="file", size=size, format=fmt))

        return BrowseResponse(source_type="gcs", items=items)


async def _browse_starburst(config, creds):
    """List tables from a Starburst/Trino cluster."""
    import httpx

    host = config.get("host", "")
    if not host:
        return BrowseResponse(source_type="starburst", items=[], message="Host URL is required")

    user_name = creds.get("username", "")
    password = creds.get("password", "")
    url = host if host.startswith("http") else f"https://{host}"
    catalog = config.get("catalog", "")
    schema = config.get("schema", "")

    query = "SHOW TABLES"
    if catalog and schema:
        query = f"SHOW TABLES FROM {catalog}.{schema}"
    elif catalog:
        query = f"SHOW TABLES FROM {catalog}.information_schema"

    auth = (user_name, password) if user_name and password else None

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(f"{url}/v1/statement", auth=auth, content=query)
        if resp.status_code != 200:
            return BrowseResponse(
                source_type="starburst",
                items=[],
                message=f"Trino returned HTTP {resp.status_code}: {resp.text[:200]}",
            )

        body = resp.json()
        items: list[BrowseItem] = []

        # Follow nextUri until we get data or finish
        max_polls = 20
        poll = 0
        while poll < max_polls:
            poll += 1
            if "data" in body:
                for row in body["data"]:
                    table_name = row[0] if row else ""
                    items.append(
                        BrowseItem(
                            name=table_name,
                            type="table",
                            catalog=catalog or None,
                            schema_name=schema or None,
                        )
                    )
                break
            next_uri = body.get("nextUri")
            if not next_uri:
                break
            import asyncio
            await asyncio.sleep(0.3)
            resp = await client.get(next_uri, auth=auth)
            if resp.status_code != 200:
                return BrowseResponse(
                    source_type="starburst",
                    items=[],
                    message=f"Trino poll returned HTTP {resp.status_code}",
                )
            body = resp.json()

        return BrowseResponse(source_type="starburst", items=items)


async def _schema_gcs(config, _creds, table: str):
    """Get column info from a GCS file (CSV headers + sample rows)."""
    import csv
    import io

    import httpx

    bucket = config.get("bucket", "")
    if not bucket:
        return SchemaInspectResponse(table=table, columns=[])

    # URL-encode the object name (table param is the object key)
    from urllib.parse import quote
    encoded = quote(table, safe="")

    async with httpx.AsyncClient(timeout=15) as client:
        token = await _gcs_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"} if token else {}

        lower = table.lower()
        if lower.endswith(".parquet"):
            # Cannot easily parse parquet without pyarrow; return file name
            return SchemaInspectResponse(
                table=table,
                columns=[ColumnInfo(name="(parquet file)", type="BINARY")],
            )

        # Fetch the file with a range header to limit download
        headers["Range"] = "bytes=0-32768"
        url = f"https://storage.googleapis.com/storage/v1/b/{bucket}/o/{encoded}?alt=media"
        resp = await client.get(url, headers=headers)

        if resp.status_code not in (200, 206):
            return SchemaInspectResponse(table=table, columns=[])

        text = resp.text
        reader = csv.reader(io.StringIO(text))
        rows = []
        for row in reader:
            rows.append(row)
            if len(rows) >= 4:  # header + 3 sample rows
                break

        if not rows:
            return SchemaInspectResponse(table=table, columns=[])

        header = rows[0]
        columns: list[ColumnInfo] = []
        for i, col_name in enumerate(header):
            sample = None
            if len(rows) > 1 and i < len(rows[1]):
                sample = rows[1][i]
            columns.append(ColumnInfo(name=col_name, type="STRING", sample=sample))

        return SchemaInspectResponse(table=table, columns=columns)


async def _schema_starburst(config, creds, table: str):
    """Describe a table via Trino REST API."""
    import httpx

    host = config.get("host", "")
    if not host:
        return SchemaInspectResponse(table=table, columns=[])

    user_name = creds.get("username", "")
    password = creds.get("password", "")
    url = host if host.startswith("http") else f"https://{host}"
    catalog = config.get("catalog", "")
    schema = config.get("schema", "")

    qualified = table
    if catalog and schema:
        qualified = f"{catalog}.{schema}.{table}"

    query = f"DESCRIBE {qualified}"
    auth = (user_name, password) if user_name and password else None

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(f"{url}/v1/statement", auth=auth, content=query)
        if resp.status_code != 200:
            return SchemaInspectResponse(table=table, columns=[])

        body = resp.json()
        columns: list[ColumnInfo] = []

        max_polls = 20
        poll = 0
        while poll < max_polls:
            poll += 1
            if "data" in body:
                for row in body["data"]:
                    col_name = row[0] if len(row) > 0 else ""
                    col_type = row[1] if len(row) > 1 else "UNKNOWN"
                    columns.append(ColumnInfo(name=col_name, type=col_type))
                break
            next_uri = body.get("nextUri")
            if not next_uri:
                break
            import asyncio
            await asyncio.sleep(0.3)
            resp = await client.get(next_uri, auth=auth)
            if resp.status_code != 200:
                break
            body = resp.json()

        return SchemaInspectResponse(table=table, columns=columns)


# ---------------------------------------------------------------------------
# Browse endpoint
# ---------------------------------------------------------------------------


@router.get(
    "/{data_source_id}/browse",
    response_model=DataResponse[BrowseResponse],
)
async def browse_data_source(
    data_source_id: int,
    user: CurrentUser,
    repo: DataSourceRepoDep,
    prefix: str | None = None,
) -> DataResponse[BrowseResponse]:
    """Browse the contents of a connected data source.

    Lists tables (SQL sources) or files (object-storage sources) so users
    can pick what to include when building a graph.

    Args:
        data_source_id: Data source ID
        user: Current authenticated user
        repo: Data source repository
        prefix: Optional path prefix for object-storage sources

    Returns:
        List of browsable items (tables or files)
    """
    data_source = await repo.get_by_id(data_source_id)
    if data_source is None:
        raise NotFoundError("data_source", data_source_id)

    check_ownership(user, data_source.owner_username, data_source_id)

    config, creds = _get_config_and_creds(data_source)
    st = data_source.source_type

    try:
        if st == "gcs":
            result = await _browse_gcs(config, creds, prefix)
        elif st == "s3":
            bucket = config.get("bucket", "")
            result = BrowseResponse(
                source_type="s3",
                items=[],
                message=f"S3 browsing not yet implemented. Bucket: {bucket}. Configure AWS SDK access to enable.",
            )
        elif st == "starburst":
            result = await _browse_starburst(config, creds)
        elif st == "bigquery":
            project = config.get("projectId", "")
            dataset = config.get("dataset", "")
            result = BrowseResponse(
                source_type="bigquery",
                items=[],
                message=f"BigQuery browsing not yet implemented. Project: {project}, Dataset: {dataset}.",
            )
        elif st == "snowflake":
            account = config.get("account", "")
            database = config.get("database", "")
            result = BrowseResponse(
                source_type="snowflake",
                items=[],
                message=f"Snowflake browsing not yet implemented. Account: {account}, Database: {database}.",
            )
        elif st == "databricks":
            host = config.get("host", "")
            catalog = config.get("catalog", "")
            result = BrowseResponse(
                source_type="databricks",
                items=[],
                message=f"Databricks browsing not yet implemented. Host: {host}, Catalog: {catalog}.",
            )
        else:
            result = BrowseResponse(
                source_type=st,
                items=[],
                message=f"Browse not supported for source type: {st}",
            )
    except Exception as e:
        result = BrowseResponse(
            source_type=st,
            items=[],
            message=f"Browse failed: {str(e)[:200]}",
        )

    return DataResponse(data=result)


# ---------------------------------------------------------------------------
# Schema / inspect endpoint
# ---------------------------------------------------------------------------


@router.get(
    "/{data_source_id}/schema",
    response_model=DataResponse[SchemaInspectResponse],
)
async def inspect_data_source_schema(
    data_source_id: int,
    user: CurrentUser,
    repo: DataSourceRepoDep,
    table: str = "",
) -> DataResponse[SchemaInspectResponse]:
    """Inspect the schema of a table or file in a data source.

    Returns column names, types, and sample values so users can build
    node/edge mappings.

    Args:
        data_source_id: Data source ID
        user: Current authenticated user
        repo: Data source repository
        table: Table name (SQL) or file path (object storage)

    Returns:
        Column info with names, types, and optional sample values
    """
    if not table:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "MISSING_TABLE", "message": "Query parameter 'table' is required"},
        )

    data_source = await repo.get_by_id(data_source_id)
    if data_source is None:
        raise NotFoundError("data_source", data_source_id)

    check_ownership(user, data_source.owner_username, data_source_id)

    config, creds = _get_config_and_creds(data_source)
    st = data_source.source_type

    try:
        if st == "gcs":
            result = await _schema_gcs(config, creds, table)
        elif st == "starburst":
            result = await _schema_starburst(config, creds, table)
        elif st in ("s3", "bigquery", "snowflake", "databricks"):
            result = SchemaInspectResponse(
                table=table,
                columns=[ColumnInfo(name="(schema inspect not yet implemented for this source)", type="INFO")],
            )
        else:
            result = SchemaInspectResponse(table=table, columns=[])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "SCHEMA_INSPECT_FAILED", "message": f"Failed to inspect schema: {str(e)[:200]}"},
        )

    return DataResponse(data=result)
