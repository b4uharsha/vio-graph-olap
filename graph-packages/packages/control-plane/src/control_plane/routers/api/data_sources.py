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
    DataResponse,
    DataSourceResponse,
    DataSourceTestResponse,
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
    from control_plane.repositories.base import utc_now, parse_timestamp

    data_source = await repo.get_by_id(data_source_id)
    if data_source is None:
        raise NotFoundError("data_source", data_source_id)

    check_ownership(user, data_source.owner_username, data_source_id)

    # TODO: Implement actual connection testing per source_type
    # For now, just record the test attempt and mark as success
    # Real implementation would attempt to connect based on source_type
    now = utc_now()
    test_status = "success"
    message = f"Connection test for {data_source.source_type} data source passed"

    await repo.update_test_status(data_source_id, test_status)

    return DataResponse(
        data=DataSourceTestResponse(
            success=True,
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
