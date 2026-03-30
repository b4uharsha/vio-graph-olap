"""Internal API for data source credential retrieval by export worker."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from control_plane.infrastructure.database import get_async_session
from control_plane.models import DataSource
from control_plane.models.errors import NotFoundError
from control_plane.models.responses import (
    DataResponse,
    DataSourceInternalResponse,
)
from control_plane.repositories.data_sources import DataSourceRepository
from control_plane.routers.internal.snapshots import InternalAuth

router = APIRouter(prefix="/api/internal", tags=["Internal - Data Sources"])


def get_data_source_repo(
    session: AsyncSession = Depends(get_async_session),
) -> DataSourceRepository:
    """Dependency to get data source repository."""
    return DataSourceRepository(session)


DataSourceRepoDep = Annotated[DataSourceRepository, Depends(get_data_source_repo)]


def data_source_to_internal_response(ds: DataSource) -> DataSourceInternalResponse:
    """Convert domain DataSource to internal response model with credentials."""
    return DataSourceInternalResponse(
        id=ds.id,
        owner_username=ds.owner_username,
        name=ds.name,
        source_type=ds.source_type,
        config=ds.config,
        credentials=ds.credentials,
        is_default=ds.is_default,
        last_tested_at=ds.last_tested_at,
        test_status=ds.test_status,
        created_at=ds.created_at,
        updated_at=ds.updated_at,
    )


@router.get(
    "/data-sources/{data_source_id}",
    response_model=DataResponse[DataSourceInternalResponse],
    dependencies=[InternalAuth],
)
async def get_data_source_internal(
    data_source_id: int,
    repo: DataSourceRepoDep,
) -> DataResponse[DataSourceInternalResponse]:
    """Get a data source with decrypted credentials.

    Internal endpoint for export worker to retrieve full connection
    details including credentials for executing queries.

    Args:
        data_source_id: Data source ID
        repo: Data source repository

    Returns:
        Data source with full credentials

    Raises:
        404: Data source not found
    """
    data_source = await repo.get_by_id(data_source_id)
    if data_source is None:
        raise NotFoundError("data_source", data_source_id)

    return DataResponse(data=data_source_to_internal_response(data_source))
