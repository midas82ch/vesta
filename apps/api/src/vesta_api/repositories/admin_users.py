from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import uuid4

from sqlalchemy import Engine, text

from vesta_api.domain.admin_models import AdminUser
from vesta_api.repositories.database import create_database_engine


class AdminUserRepository(Protocol):
    def get_by_username(self, username: str) -> AdminUser | None: ...

    def create(self, *, username: str, password_hash: str) -> AdminUser: ...

    def healthcheck(self) -> None: ...

    def close(self) -> None: ...


class InMemoryAdminUserRepository:
    """Used for local development/tests without a configured DATABASE_URL."""

    def __init__(self) -> None:
        self._users: dict[str, AdminUser] = {}

    def get_by_username(self, username: str) -> AdminUser | None:
        return self._users.get(username)

    def create(self, *, username: str, password_hash: str) -> AdminUser:
        if username in self._users:
            raise ValueError(f"admin user already exists: {username}")
        user = AdminUser(
            id=str(uuid4()),
            username=username,
            password_hash=password_hash,
            is_active=True,
            created_at=datetime.now(UTC),
        )
        self._users[username] = user
        return user

    def healthcheck(self) -> None:
        return None

    def close(self) -> None:
        return None


_GET_BY_USERNAME = text(
    """
    SELECT id::text AS id, username, password_hash, is_active, created_at
    FROM admin_users
    WHERE username = :username
    """
)

_INSERT_ADMIN_USER = text(
    """
    INSERT INTO admin_users (id, username, password_hash)
    VALUES (:id, :username, :password_hash)
    RETURNING id::text AS id, username, password_hash, is_active, created_at
    """
)


def _row_to_admin_user(row: Mapping[str, Any]) -> AdminUser:
    return AdminUser(
        id=row["id"],
        username=row["username"],
        password_hash=row["password_hash"],
        is_active=bool(row["is_active"]),
        created_at=row["created_at"],
    )


class PostgresAdminUserRepository:
    def __init__(self, database_url: str, *, engine: Engine | None = None) -> None:
        self._engine = engine or create_database_engine(database_url)

    def get_by_username(self, username: str) -> AdminUser | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                _GET_BY_USERNAME, {"username": username}
            ).mappings().first()
        return _row_to_admin_user(row) if row is not None else None

    def create(self, *, username: str, password_hash: str) -> AdminUser:
        with self._engine.begin() as connection:
            row = connection.execute(
                _INSERT_ADMIN_USER,
                {"id": uuid4(), "username": username, "password_hash": password_hash},
            ).mappings().one()
        return _row_to_admin_user(row)

    def healthcheck(self) -> None:
        with self._engine.connect() as connection:
            connection.execute(text("SELECT 1"))

    def close(self) -> None:
        self._engine.dispose()
