"""Request identity resolution and role-based authorization (HSBC pattern).

Resolves the caller's identity from X-Username header and looks up their
role from the database (ADR-104). No tokens, no JWT, no passwords.

Unknown users are rejected with 403 USER_NOT_PROVISIONED (no auto-create).
Users must be pre-provisioned via POST /api/users/bootstrap or POST /api/users.

Note: This is the HSBC deployment pattern. For oauth2-proxy/JWT-based auth,
see middleware/auth.py instead.
"""

from typing import Annotated

import structlog
from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from control_plane.infrastructure.database import get_async_session
from control_plane.models import RequestUser, UserRole
from control_plane.repositories.users import UserRepository

logger = structlog.get_logger(__name__)


async def get_request_user(
    request: Request,
    x_username: Annotated[str | None, Header()] = None,
    x_use_case_id: Annotated[str | None, Header()] = None,
    session: AsyncSession = Depends(get_async_session),
) -> RequestUser:
    """Resolve request identity from X-Username header and database.

    Flow:
    1. Read X-Username header (401 if missing)
    2. Look up user in database (403 if not provisioned)
    3. Check user is active (403 if disabled)
    4. Return RequestUser with role from database
    """
    if not x_username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "UNAUTHORIZED",
                "message": "X-Username header required.",
            },
        )

    user_repo = UserRepository(session)
    db_user = await user_repo.get_by_username(x_username)

    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "USER_NOT_PROVISIONED",
                "message": f"User '{x_username}' is not provisioned. Use POST /api/users/bootstrap or POST /api/users to create.",
            },
        )

    if not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "USER_DISABLED",
                "message": "User account is disabled",
            },
        )

    await user_repo.update_last_login(x_username)

    request_user = RequestUser(
        username=db_user.username,
        role=db_user.role if hasattr(db_user, "role") else UserRole.ANALYST,
        email=db_user.email or x_username,
        display_name=db_user.display_name,
        is_active=db_user.is_active,
    )
    request.state.user = request_user

    logger.info(
        "identity_resolved",
        username=request_user.username,
        role=request_user.role.value,
    )

    return request_user


# Type alias for dependency injection
IdentityUser = Annotated[RequestUser, Depends(get_request_user)]
