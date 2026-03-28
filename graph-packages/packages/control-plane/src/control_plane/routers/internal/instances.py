"""Internal API for instance status updates from wrapper pods."""

import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from graph_olap_schemas import InstanceMappingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from control_plane.infrastructure.database import get_async_session
from control_plane.models import InstanceErrorCode, InstanceStatus
from control_plane.models.errors import NotFoundError
from control_plane.models.requests import (
    UpdateInstanceMetricsRequest,
    UpdateInstanceProgressRequest,
    UpdateInstanceStatusRequest,
)
from control_plane.models.responses import DataResponse, InstanceResponse, UpdatedResponse
from control_plane.repositories.config import GlobalConfigRepository
from control_plane.repositories.instances import InstanceRepository
from control_plane.repositories.mappings import MappingRepository
from control_plane.repositories.snapshots import SnapshotRepository
from control_plane.services.instance_service import InstanceService

router = APIRouter(prefix="/api/internal/instances", tags=["Internal - Instances"])


def verify_internal_api_key(
    request: Request,
    x_internal_api_key: Annotated[str | None, Header()] = None,
) -> None:
    """Verify internal API key for service-to-service calls.

    Uses constant-time comparison to prevent timing attacks.
    """
    settings = request.app.state.settings
    if settings.internal_api_key:
        # Use constant-time comparison to prevent timing attacks
        if not x_internal_api_key or not secrets.compare_digest(
            x_internal_api_key.encode(), settings.internal_api_key.encode()
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "UNAUTHORIZED", "message": "Invalid internal API key"},
            )


InternalAuth = Depends(verify_internal_api_key)


def get_instance_service(
    session: AsyncSession = Depends(get_async_session),
) -> InstanceService:
    """Dependency to get instance service."""
    from control_plane.repositories.favorites import FavoritesRepository

    return InstanceService(
        instance_repo=InstanceRepository(session),
        snapshot_repo=SnapshotRepository(session),
        config_repo=GlobalConfigRepository(session),
        favorites_repo=FavoritesRepository(session),
    )


def get_instance_repo(
    session: AsyncSession = Depends(get_async_session),
) -> InstanceRepository:
    """Dependency to get instance repository."""
    return InstanceRepository(session)


InstanceServiceDep = Annotated[InstanceService, Depends(get_instance_service)]
InstanceRepoDep = Annotated[InstanceRepository, Depends(get_instance_repo)]


def instance_to_response(instance) -> InstanceResponse:
    """Convert domain Instance to response model."""
    return InstanceResponse(
        id=instance.id,
        snapshot_id=instance.snapshot_id,
        owner_username=instance.owner_username,
        wrapper_type=instance.wrapper_type,
        name=instance.name,
        description=instance.description,
        status=instance.status.value,
        instance_url=instance.instance_url,
        pod_name=instance.pod_name,
        progress=instance.progress,
        error_code=instance.error_code.value if instance.error_code else None,
        error_message=instance.error_message,
        stack_trace=instance.stack_trace,
        created_at=instance.created_at,
        updated_at=instance.updated_at,
        started_at=instance.started_at,
        last_activity_at=instance.last_activity_at,
        expires_at=instance.expires_at,
        ttl=instance.ttl,
        inactivity_timeout=instance.inactivity_timeout,
        memory_usage_bytes=instance.memory_usage_bytes,
        disk_usage_bytes=instance.disk_usage_bytes,
    )


@router.patch(
    "/{instance_id}/status",
    response_model=DataResponse[InstanceResponse],
    dependencies=[InternalAuth],
)
async def update_instance_status(
    instance_id: int,
    request: UpdateInstanceStatusRequest,
    service: InstanceServiceDep,
) -> DataResponse[InstanceResponse]:
    """Update instance status from wrapper pod.

    Called by wrapper pods to report progress and status changes.

    Args:
        instance_id: Instance ID
        request: Status update request
        service: Instance service

    Returns:
        Updated instance
    """
    # Convert error_code string to enum if provided
    error_code = None
    if request.error_code:
        error_code = InstanceErrorCode(request.error_code)

    instance = await service.update_status(
        instance_id=instance_id,
        status=InstanceStatus(request.status),
        error_message=request.error_message,
        error_code=error_code,
        stack_trace=request.stack_trace,
        pod_name=request.pod_name,
        pod_ip=request.pod_ip,
        instance_url=request.instance_url,
        progress=request.progress,
    )
    return DataResponse(data=instance_to_response(instance))


@router.post(
    "/{instance_id}/activity",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[InternalAuth],
)
async def update_instance_activity(
    instance_id: int,
    service: InstanceServiceDep,
) -> None:
    """Update instance activity timestamp.

    Called by wrapper pods when a query or algorithm is executed.

    Args:
        instance_id: Instance ID
        service: Instance service
    """
    await service.update_activity(instance_id)


@router.put(
    "/{instance_id}/metrics",
    response_model=DataResponse[UpdatedResponse],
    dependencies=[InternalAuth],
)
async def update_instance_metrics(
    instance_id: int,
    request: UpdateInstanceMetricsRequest,
    repo: InstanceRepoDep,
) -> DataResponse[UpdatedResponse]:
    """Update instance resource usage metrics.

    Called periodically by wrapper pods to report resource usage.

    Args:
        instance_id: Instance ID
        request: Metrics update request
        repo: Instance repository

    Returns:
        Confirmation of update

    Raises:
        404: Instance not found
    """
    updated = await repo.update_resource_usage(
        instance_id=instance_id,
        memory_usage_bytes=request.memory_usage_bytes,
        disk_usage_bytes=request.disk_usage_bytes,
        last_activity_at=request.last_activity_at,
    )
    if not updated:
        raise NotFoundError("instance", instance_id)
    return DataResponse(data=UpdatedResponse())


@router.put(
    "/{instance_id}/progress",
    response_model=DataResponse[UpdatedResponse],
    dependencies=[InternalAuth],
)
async def update_instance_progress(
    instance_id: int,
    request: UpdateInstanceProgressRequest,
    repo: InstanceRepoDep,
) -> DataResponse[UpdatedResponse]:
    """Update instance loading progress.

    Called during instance startup to report loading progress.

    Args:
        instance_id: Instance ID
        request: Progress update request
        repo: Instance repository

    Returns:
        Confirmation of update

    Raises:
        404: Instance not found
    """
    steps = [step.model_dump() for step in request.steps]
    total_steps = len(steps)
    completed_steps = sum(1 for s in steps if s.get("status") == "completed")
    progress_percent = int((completed_steps / total_steps) * 100) if total_steps > 0 else 0

    progress = {
        "phase": request.phase,
        "steps": steps,
        "progress_percent": progress_percent,
    }
    updated = await repo.update_progress(instance_id, progress)
    if not updated:
        raise NotFoundError("instance", instance_id)
    return DataResponse(data=UpdatedResponse())


@router.get(
    "/{instance_id}/mapping",
    dependencies=[InternalAuth],
    response_model=InstanceMappingResponse,
)
async def get_instance_mapping(
    instance_id: int,
    session: AsyncSession = Depends(get_async_session),
) -> InstanceMappingResponse:
    """Get mapping definition for an instance.

    Returns the mapping associated with the instance's snapshot,
    using the shared InstanceMappingResponse schema for API contract compliance.

    Args:
        instance_id: Instance ID
        session: Database session

    Returns:
        InstanceMappingResponse with snapshot_id, mapping_id, gcs_path, and definitions

    Raises:
        404: Instance, snapshot, or mapping not found
    """
    instance_repo = InstanceRepository(session)
    snapshot_repo = SnapshotRepository(session)
    mapping_repo = MappingRepository(session)

    # Get instance
    instance = await instance_repo.get_by_id(instance_id)
    if not instance:
        raise NotFoundError("instance", instance_id)

    # Get snapshot
    snapshot = await snapshot_repo.get_by_id(instance.snapshot_id)
    if not snapshot:
        raise NotFoundError("snapshot", instance.snapshot_id)

    # Get mapping at the version used by the snapshot
    mapping = await mapping_repo.get_by_id(snapshot.mapping_id)
    if not mapping:
        raise NotFoundError("mapping", snapshot.mapping_id)

    # Return using shared InstanceMappingResponse schema
    return InstanceMappingResponse(
        snapshot_id=snapshot.id,
        mapping_id=mapping.id,
        mapping_version=snapshot.mapping_version,
        gcs_path=snapshot.gcs_path,
        node_definitions=[
            {
                "label": node.label,
                "sql": node.sql,
                "primary_key": {
                    "name": node.primary_key.name,
                    "type": node.primary_key.type,
                },
                "properties": [{"name": prop.name, "type": prop.type} for prop in node.properties],
            }
            for node in mapping.node_definitions
        ],
        edge_definitions=[
            {
                "type": edge.type,
                "sql": edge.sql,
                "from_node": edge.from_node,
                "to_node": edge.to_node,
                "from_key": edge.from_key,
                "to_key": edge.to_key,
                "properties": [{"name": prop.name, "type": prop.type} for prop in edge.properties],
            }
            for edge in mapping.edge_definitions
        ],
    )
