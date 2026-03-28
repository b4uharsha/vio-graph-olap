"""FastAPI dependency injection providers.

Provides dependency functions for injecting services and configuration
into route handlers. Uses the proper FastAPI pattern with app.state.

See ADR-095 for M2M token handling via JWT claim extraction.
"""

from __future__ import annotations

import structlog
from typing import TYPE_CHECKING, Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from lib_auth import extract_email_from_token, extract_role_from_token

from wrapper.config import Settings, get_settings

logger = structlog.get_logger(__name__)

if TYPE_CHECKING:
    from wrapper.clients.control_plane import ControlPlaneClient
    from wrapper.services.algorithm import AlgorithmService
    from wrapper.services.database import DatabaseService
    from wrapper.services.lock import LockService


# =============================================================================
# Configuration Dependencies
# =============================================================================


def get_app_settings() -> Settings:
    """Get application settings.

    Returns cached singleton Settings instance.
    """
    return get_settings()


# =============================================================================
# Service Dependencies
# =============================================================================


def get_database_service(request: Request) -> DatabaseService:
    """Get the database service from app state.

    Args:
        request: FastAPI request object.

    Returns:
        DatabaseService instance.

    Raises:
        HTTPException: If service not initialized.
    """
    service = getattr(request.app.state, "db_service", None)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service not initialized",
        )
    return service


def get_lock_service(request: Request) -> LockService:
    """Get the lock service from app state.

    Args:
        request: FastAPI request object.

    Returns:
        LockService instance.

    Raises:
        HTTPException: If service not initialized.
    """
    service = getattr(request.app.state, "lock_service", None)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Lock service not initialized",
        )
    return service


def get_control_plane_client(request: Request) -> ControlPlaneClient:
    """Get the Control Plane client from app state.

    Args:
        request: FastAPI request object.

    Returns:
        ControlPlaneClient instance.

    Raises:
        HTTPException: If client not initialized.
    """
    client = getattr(request.app.state, "control_plane_client", None)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Control Plane client not initialized",
        )
    return client


def get_algorithm_service(request: Request) -> AlgorithmService:
    """Get the algorithm service from app state.

    Args:
        request: FastAPI request object.

    Returns:
        AlgorithmService instance.

    Raises:
        HTTPException: If service not initialized.
    """
    service = getattr(request.app.state, "algorithm_service", None)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Algorithm service not initialized",
        )
    return service


# =============================================================================
# User Context Dependencies
# =============================================================================


def get_user_id(
    x_user_id: Annotated[str | None, Header()] = None,
) -> str:
    """Extract user ID from request header.

    Args:
        x_user_id: User ID from X-User-ID header.

    Returns:
        User ID or "anonymous" if not provided.
    """
    return x_user_id or "anonymous"


def get_user_name(
    x_user_name: Annotated[str | None, Header()] = None,
) -> str:
    """Extract username from request header.

    Args:
        x_user_name: Username from X-User-Name header.

    Returns:
        Username or "anonymous" if not provided.
    """
    return x_user_name or "anonymous"


def get_user_role(
    x_user_role: Annotated[str | None, Header()] = None,
) -> str:
    """Extract user role from request header.

    Args:
        x_user_role: User role from X-User-Role header.

    Returns:
        User role or "analyst" if not provided (default to least privilege).
    """
    return x_user_role or "analyst"


# =============================================================================
# Authorization Dependencies
# =============================================================================


def require_algorithm_permission(
    x_user_id: Annotated[str | None, Header()] = None,
    x_username: Annotated[str | None, Header()] = None,
    x_user_role: Annotated[str | None, Header()] = None,
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    """Verify user has permission to execute algorithms on this instance.

    Authorization rules:
    - Admin and Ops roles can execute algorithms on any instance
    - Analyst role can only execute algorithms on instances they own

    For M2M tokens, X-Username may contain the client_id instead of the user email.
    We extract the email from the JWT custom claim as the authoritative identity.
    See ADR-095 for details.

    Args:
        x_user_id: User ID from X-User-ID header.
        x_username: Username from X-Username header (may be wrong for M2M).
        x_user_role: User role from X-User-Role header.
        authorization: Bearer token (for extracting email and role).

    Returns:
        User ID if authorized.

    Raises:
        HTTPException: 401 if role missing, 403 if not authorized.
    """
    # For M2M tokens, extract email from JWT custom claim (authoritative identity)
    # Falls back to headers for browser sessions where oauth2-proxy sets X-Username correctly
    email_from_token = extract_email_from_token(authorization)
    user_id = email_from_token or x_user_id or x_username or "anonymous"

    # Get role from header, or extract from JWT if not set
    # Security: fail closed - if role cannot be determined, deny access
    role = x_user_role.lower() if x_user_role else extract_role_from_token(authorization)

    if role is None:
        logger.error(
            "Algorithm execution denied: role claim missing from token",
            user_id=user_id,
            has_authorization=authorization is not None,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Role claim missing from token - authentication misconfigured",
        )

    # Admin and Ops can execute algorithms on any instance
    if role in ("admin", "ops"):
        return user_id

    # For analysts, check instance ownership
    settings = get_settings()
    owner_id = settings.wrapper.owner_id

    if user_id != owner_id:
        logger.warning(
            "Algorithm execution denied: user is not instance owner",
            user_id=user_id,
            user_role=role,
            owner_id=owner_id,
            instance_id=settings.wrapper.instance_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: only instance owner or admin/ops can execute algorithms",
        )

    return user_id


# =============================================================================
# Type Aliases for Common Dependencies
# =============================================================================

SettingsDep = Annotated[Settings, Depends(get_app_settings)]
DatabaseServiceDep = Annotated["DatabaseService", Depends(get_database_service)]
LockServiceDep = Annotated["LockService", Depends(get_lock_service)]
ControlPlaneClientDep = Annotated["ControlPlaneClient", Depends(get_control_plane_client)]
AlgorithmServiceDep = Annotated["AlgorithmService", Depends(get_algorithm_service)]
UserIdDep = Annotated[str, Depends(get_user_id)]
UserNameDep = Annotated[str, Depends(get_user_name)]
UserRoleDep = Annotated[str, Depends(get_user_role)]
AlgorithmPermissionDep = Annotated[str, Depends(require_algorithm_permission)]
