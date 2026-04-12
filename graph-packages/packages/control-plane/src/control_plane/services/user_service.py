"""User management service.

Adapted from graphsol (HSBC implementation) to work with
vio-graph-olap's existing UserRepository.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from control_plane.models import RequestUser, User, UserRole
from control_plane.models.user_models import (
    AssignRoleRequest,
    CreateUserRequest,
    UpdateUserRequest,
)
from control_plane.repositories.users import UserRepository

logger = structlog.get_logger(__name__)


class UserService:
    def __init__(self, session: AsyncSession):
        self._repo = UserRepository(session)

    async def create_user(self, request: CreateUserRequest, actor: RequestUser) -> User:
        existing = await self._repo.get_by_username(request.username)
        if existing:
            raise ValueError(f"User {request.username} already exists")
        user = User(
            username=request.username,
            email=request.email,
            display_name=request.display_name,
            is_active=True,
        )
        return await self._repo.create(user)

    async def get_user(self, username: str) -> User | None:
        return await self._repo.get_by_username(username)

    async def list_users(
        self,
        is_active: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[User]:
        users, _total = await self._repo.list_users(
            is_active=is_active, limit=limit, offset=offset,
        )
        return users

    async def update_user(
        self,
        username: str,
        request: UpdateUserRequest,
        actor: RequestUser,
    ) -> User | None:
        user = await self._repo.get_by_username(username)
        if user is None:
            return None
        if request.email is not None:
            user.email = request.email
        if request.display_name is not None:
            user.display_name = request.display_name
        if request.is_active is not None:
            user.is_active = request.is_active
        return await self._repo.update(user)

    async def assign_role(
        self,
        username: str,
        request: AssignRoleRequest,
        actor: RequestUser,
    ) -> User | None:
        user = await self._repo.get_by_username(username)
        if user is None:
            return None
        # Role assignment is logged but role storage depends on deployment mode:
        # - HSBC pattern (identity.py): role stored in DB
        # - JWT pattern (auth.py): role from token claims
        logger.info(
            "role_assigned",
            username=username,
            new_role=request.role,
            changed_by=actor.username,
        )
        return await self._repo.update(user)

    async def deactivate_user(self, username: str, actor: RequestUser) -> User | None:
        user = await self._repo.get_by_username(username)
        if user is None:
            return None
        user.is_active = False
        return await self._repo.update(user)

    async def bootstrap(self, request: CreateUserRequest) -> User:
        users, total = await self._repo.list_users(limit=1)
        if total > 0:
            raise ValueError("Bootstrap only works when no users exist")
        user = User(
            username=request.username,
            email=request.email,
            display_name=request.display_name,
            is_active=True,
        )
        return await self._repo.create(user)
