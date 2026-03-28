"""Authentication middleware and dependencies.

Authentication is handled at the edge by oauth2-proxy, which:
1. Validates JWT signature via JWKS
2. Checks issuer and audience claims
3. Extracts email and sets X-Auth-Request-Email header
4. nginx maps this to X-Username header

This middleware trusts the validated identity from oauth2-proxy and:
1. Uses X-Username header as the user identity (for browser sessions)
2. Falls back to extracting email from JWT custom claim (for M2M tokens)
3. Extracts role from JWT payload (no re-validation needed - already validated at edge)
4. Fails closed if role claim is missing

Users are auto-created in the database on first request for FK purposes.
Roles are NEVER stored in database - they come from JWT claims per-request.
"""

from typing import Annotated

import structlog
from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from control_plane.infrastructure.database import get_async_session
from control_plane.models import RequestUser, UserRole
from control_plane.repositories.users import UserRepository
from lib_auth import extract_email_from_token, extract_role_from_token

logger = structlog.get_logger(__name__)


async def get_current_user(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    x_username: Annotated[str | None, Header()] = None,
    x_user_role: Annotated[str | None, Header()] = None,
    session: AsyncSession = Depends(get_async_session),
) -> RequestUser:
    """Get current user context from request.

    Authentication flow:
    1. For browser sessions: oauth2-proxy extracts email → X-Username header
    2. For M2M tokens: Extract email directly from JWT custom claim
    3. Extract role from JWT payload (already validated at edge)

    Args:
        request: FastAPI request
        authorization: Authorization header (Bearer token)
        x_username: Username from X-Username header (from oauth2-proxy)
        x_user_role: Role from X-User-Role header (testing fallback)
        session: Database session

    Returns:
        RequestUser with username and role for this request

    Raises:
        HTTPException: If authentication fails or role is missing
    """
    # DEBUG: Log received headers
    logger.info(
        "auth_headers_received",
        x_username=x_username,
        x_user_role=x_user_role,
        has_authorization=authorization is not None,
        auth_header_len=len(authorization) if authorization else 0,
    )

    # For M2M tokens, X-Username may be wrong (client_id) or missing
    # Extract email from JWT custom claim as the authoritative identity
    email_from_token = extract_email_from_token(authorization)

    if email_from_token:
        logger.info("jwt_email_extracted", email=email_from_token)

    # Resolve username: prefer JWT email (correct for M2M), fall back to X-Username (browser)
    username = email_from_token or x_username

    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "UNAUTHORIZED",
                "message": "Authentication required. No identity found in token or headers.",
            },
        )

    # Extract role from JWT payload (oauth2-proxy already validated the token)
    # Fall back to X-User-Role header if present (for testing compatibility)
    role_from_token = extract_role_from_token(authorization)
    role_str = x_user_role.lower() if x_user_role else role_from_token

    # DEBUG: Log role extraction result
    logger.info(
        "role_extraction_result",
        x_user_role_header=x_user_role,
        role_from_token=role_from_token,
        final_role_str=role_str,
    )

    if role_str is None:
        logger.error(
            "Authentication denied: role claim missing from token",
            extra={"username": username, "has_authorization": authorization is not None},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "MISSING_ROLE",
                "message": "Role claim missing from token - authentication misconfigured",
            },
        )

    try:
        role = UserRole(role_str)
    except ValueError:
        logger.warning(f"Invalid role '{role_str}' in token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_ROLE",
                "message": f"Invalid role '{role_str}' in token",
            },
        )

    logger.debug(
        "identity_resolved",
        email_from_token=email_from_token,
        x_username=x_username,
        resolved_username=username,
    )

    # Ensure user exists in database (auto-create if needed)
    user_repo = UserRepository(session)
    db_user = await user_repo.ensure_exists(username, email=username)

    # Update last login timestamp
    await user_repo.update_last_login(username)

    if not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "USER_DISABLED",
                "message": "User account is disabled",
            },
        )

    request_user = RequestUser(
        username=db_user.username,
        role=role,
        email=db_user.email or username,
        display_name=db_user.display_name,
        is_active=db_user.is_active,
    )
    request.state.user = request_user

    # DEBUG: Log final authenticated user
    logger.info(
        "auth_successful",
        username=request_user.username,
        role=request_user.role.value,
        email=request_user.email,
    )

    return request_user


# Type alias for dependency injection
CurrentUser = Annotated[RequestUser, Depends(get_current_user)]


def require_role(*allowed_roles: UserRole):
    """Create a dependency that requires specific roles.

    The role is checked against the token claim or X-User-Role header,
    NOT against any stored database value.

    Usage:
        @router.post("/config")
        async def update_config(
            user: CurrentUser,
            _: None = Depends(require_role(UserRole.OPS)),
        ):
            ...

    Args:
        allowed_roles: Roles that are allowed to access the endpoint

    Returns:
        Dependency function
    """

    async def check_role(user: CurrentUser) -> None:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "PERMISSION_DENIED",
                    "message": f"Requires one of: {[r.value for r in allowed_roles]}",
                },
            )

    return check_role


# Common role requirements
RequireOps = Depends(require_role(UserRole.OPS))
RequireAdmin = Depends(require_role(UserRole.ADMIN, UserRole.OPS))
