"""Export jobs API router with role-scoped access.

Analysts see only their own export jobs (via snapshot ownership).
Admin and Ops see all export jobs.
"""

from fastapi import APIRouter, Depends, Query
from graph_olap_schemas import ExportJobsListResponse, ExportJobSummary
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from control_plane.infrastructure import tables
from control_plane.infrastructure.database import get_async_session
from control_plane.middleware.auth import CurrentUser
from control_plane.models import UserRole
from control_plane.models.responses import DataResponse

router = APIRouter(prefix="/api/export-jobs", tags=["Export Jobs"])


@router.get("", response_model=DataResponse[ExportJobsListResponse])
async def get_export_jobs(
    user: CurrentUser,
    session: AsyncSession = Depends(get_async_session),
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, le=200),
) -> DataResponse[ExportJobsListResponse]:
    """Get export jobs with role-scoped access.

    - Analyst: sees only export jobs for snapshots they own
    - Admin/Ops: sees all export jobs

    Args:
        status: Filter by status (pending, claimed, submitted, completed, failed)
        limit: Max jobs to return (default 50, max 200)
    """
    if user.role == UserRole.ANALYST:
        # Join to snapshots to filter by owner
        query = (
            select(tables.export_jobs)
            .join(tables.snapshots, tables.export_jobs.c.snapshot_id == tables.snapshots.c.id)
            .where(tables.snapshots.c.owner_username == user.username)
        )
    else:
        query = select(tables.export_jobs)

    if status_filter:
        query = query.where(tables.export_jobs.c.status == status_filter)

    query = query.limit(limit).order_by(tables.export_jobs.c.created_at.desc())

    result = await session.execute(query)
    rows = result.all()

    jobs_response = [
        ExportJobSummary(
            id=row.id,
            snapshot_id=row.snapshot_id,
            entity_type=row.job_type,
            entity_name=row.entity_name,
            status=row.status,
            claimed_at=row.claimed_at,
            claimed_by=row.claimed_by,
            attempts=row.poll_count,
            error_message=row.error_message,
        )
        for row in rows
    ]

    return DataResponse(data=ExportJobsListResponse(jobs=jobs_response))
