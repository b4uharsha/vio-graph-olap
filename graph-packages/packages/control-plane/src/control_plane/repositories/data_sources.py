"""Data source repository for database operations."""

from typing import Any

from control_plane.models import DataSource
from control_plane.repositories.base import (
    BaseRepository,
    deserialize_json,
    parse_timestamp,
    serialize_json,
    utc_now,
)


class DataSourceRepository(BaseRepository):
    """Repository for data source database operations."""

    async def create(
        self,
        owner_username: str,
        name: str,
        source_type: str,
        config: dict[str, Any] | None = None,
        credentials: dict[str, Any] | None = None,
        is_default: bool = False,
    ) -> DataSource:
        """Create a new data source.

        Args:
            owner_username: Username of the owner
            name: Data source name
            source_type: Type of data source
            config: Connection configuration
            credentials: Authentication credentials
            is_default: Whether this is the default data source

        Returns:
            Created DataSource
        """
        now = utc_now()

        # If setting as default, clear existing defaults for this user
        if is_default:
            await self._clear_defaults(owner_username)

        sql = """
            INSERT INTO data_sources (owner_username, name, source_type,
                                      config, credentials, is_default,
                                      created_at, updated_at)
            VALUES (:owner_username, :name, :source_type,
                    :config, :credentials, :is_default,
                    :created_at, :updated_at)
            RETURNING id
        """
        data_source_id = await self._insert_returning_id(
            sql,
            {
                "owner_username": owner_username,
                "name": name,
                "source_type": source_type,
                "config": serialize_json(config or {}),
                "credentials": serialize_json(credentials or {}),
                "is_default": 1 if is_default else 0,
                "created_at": now,
                "updated_at": now,
            },
        )

        return DataSource(
            id=data_source_id,
            owner_username=owner_username,
            name=name,
            source_type=source_type,
            config=config or {},
            credentials=credentials or {},
            is_default=is_default,
            created_at=parse_timestamp(now),
            updated_at=parse_timestamp(now),
        )

    async def get_by_id(self, data_source_id: int) -> DataSource | None:
        """Get data source by ID.

        Args:
            data_source_id: Data source ID

        Returns:
            DataSource domain object or None if not found
        """
        sql = """
            SELECT id, owner_username, name, source_type,
                   config, credentials, is_default,
                   last_tested_at, test_status,
                   created_at, updated_at
            FROM data_sources
            WHERE id = :id
        """
        row = await self._fetch_one(sql, {"id": data_source_id})
        if row is None:
            return None
        return self._row_to_data_source(row)

    async def list_by_owner(
        self,
        owner_username: str,
        source_type: str | None = None,
    ) -> list[DataSource]:
        """List data sources for a user.

        Args:
            owner_username: Username of the owner
            source_type: Optional filter by source type

        Returns:
            List of DataSource objects
        """
        conditions = ["owner_username = :owner_username"]
        params: dict[str, Any] = {"owner_username": owner_username}

        if source_type:
            conditions.append("source_type = :source_type")
            params["source_type"] = source_type

        where_clause = " AND ".join(conditions)

        sql = f"""
            SELECT id, owner_username, name, source_type,
                   config, credentials, is_default,
                   last_tested_at, test_status,
                   created_at, updated_at
            FROM data_sources
            WHERE {where_clause}
            ORDER BY is_default DESC, created_at DESC
        """
        rows = await self._fetch_all(sql, params)
        return [self._row_to_data_source(row) for row in rows]

    async def update(
        self,
        data_source_id: int,
        name: str | None = None,
        source_type: str | None = None,
        config: dict[str, Any] | None = None,
        credentials: dict[str, Any] | None = None,
    ) -> DataSource | None:
        """Update a data source.

        Args:
            data_source_id: Data source ID
            name: New name (optional)
            source_type: New source type (optional)
            config: New config (optional)
            credentials: New credentials (optional)

        Returns:
            Updated DataSource or None if not found
        """
        now = utc_now()

        # Build dynamic update
        set_clauses = ["updated_at = :updated_at"]
        params: dict[str, Any] = {"id": data_source_id, "updated_at": now}

        if name is not None:
            set_clauses.append("name = :name")
            params["name"] = name

        if source_type is not None:
            set_clauses.append("source_type = :source_type")
            params["source_type"] = source_type

        if config is not None:
            set_clauses.append("config = :config")
            params["config"] = serialize_json(config)

        if credentials is not None:
            set_clauses.append("credentials = :credentials")
            params["credentials"] = serialize_json(credentials)

        sql = f"""
            UPDATE data_sources
            SET {', '.join(set_clauses)}
            WHERE id = :id
        """
        result = await self._execute(sql, params)
        if result.rowcount == 0:
            return None

        return await self.get_by_id(data_source_id)

    async def delete(self, data_source_id: int) -> bool:
        """Delete a data source.

        Args:
            data_source_id: Data source ID

        Returns:
            True if data source was deleted
        """
        sql = "DELETE FROM data_sources WHERE id = :id"
        result = await self._execute(sql, {"id": data_source_id})
        return result.rowcount > 0

    async def set_default(self, data_source_id: int, owner_username: str) -> DataSource | None:
        """Set a data source as the default for its owner.

        Clears the default flag on all other data sources for this owner first.

        Args:
            data_source_id: Data source ID to set as default
            owner_username: Owner username (for clearing other defaults)

        Returns:
            Updated DataSource or None if not found
        """
        now = utc_now()

        # Clear existing defaults for this owner
        await self._clear_defaults(owner_username)

        # Set new default
        sql = """
            UPDATE data_sources
            SET is_default = 1, updated_at = :updated_at
            WHERE id = :id AND owner_username = :owner_username
        """
        result = await self._execute(
            sql,
            {"id": data_source_id, "owner_username": owner_username, "updated_at": now},
        )
        if result.rowcount == 0:
            return None

        return await self.get_by_id(data_source_id)

    async def get_default(self, owner_username: str) -> DataSource | None:
        """Get the default data source for a user.

        Args:
            owner_username: Username

        Returns:
            Default DataSource or None if no default is set
        """
        sql = """
            SELECT id, owner_username, name, source_type,
                   config, credentials, is_default,
                   last_tested_at, test_status,
                   created_at, updated_at
            FROM data_sources
            WHERE owner_username = :owner_username AND is_default = 1
        """
        row = await self._fetch_one(sql, {"owner_username": owner_username})
        if row is None:
            return None
        return self._row_to_data_source(row)

    async def update_test_status(
        self,
        data_source_id: int,
        test_status: str,
    ) -> DataSource | None:
        """Update the test status of a data source.

        Args:
            data_source_id: Data source ID
            test_status: Test result status (success, failed)

        Returns:
            Updated DataSource or None if not found
        """
        now = utc_now()
        sql = """
            UPDATE data_sources
            SET last_tested_at = :now, test_status = :test_status, updated_at = :now
            WHERE id = :id
        """
        result = await self._execute(
            sql,
            {"id": data_source_id, "test_status": test_status, "now": now},
        )
        if result.rowcount == 0:
            return None

        return await self.get_by_id(data_source_id)

    async def _clear_defaults(self, owner_username: str) -> None:
        """Clear the default flag on all data sources for a user.

        Args:
            owner_username: Username
        """
        now = utc_now()
        sql = """
            UPDATE data_sources
            SET is_default = 0, updated_at = :updated_at
            WHERE owner_username = :owner_username AND is_default = 1
        """
        await self._execute(sql, {"owner_username": owner_username, "updated_at": now})

    def _row_to_data_source(self, row) -> DataSource:
        """Convert database row to DataSource domain object."""
        return DataSource(
            id=row.id,
            owner_username=row.owner_username,
            name=row.name,
            source_type=row.source_type,
            config=deserialize_json(row.config) or {},
            credentials=deserialize_json(row.credentials) or {},
            is_default=bool(row.is_default),
            last_tested_at=parse_timestamp(row.last_tested_at),
            test_status=row.test_status,
            created_at=parse_timestamp(row.created_at),
            updated_at=parse_timestamp(row.updated_at),
        )
