from collections.abc import Mapping
from typing import Any, Protocol

from sqlalchemy import Engine, text

from vesta_api.domain.ingestion_models import IngestionRun
from vesta_api.repositories.database import create_database_engine


class IngestionRunRepository(Protocol):
    def list_runs(
        self,
        *,
        limit: int,
        offset: int,
        status: str | None = None,
    ) -> tuple[IngestionRun, ...]: ...

    def healthcheck(self) -> None: ...

    def close(self) -> None: ...


class InMemoryIngestionRunRepository:
    """Used for local development/tests without a configured DATABASE_URL."""

    def __init__(self, runs: tuple[IngestionRun, ...] = ()) -> None:
        self._runs = list(runs)

    def add(self, run: IngestionRun) -> None:
        self._runs.append(run)

    def list_runs(
        self,
        *,
        limit: int,
        offset: int,
        status: str | None = None,
    ) -> tuple[IngestionRun, ...]:
        matching = [run for run in self._runs if status is None or run.status == status]
        matching.sort(key=lambda run: run.checked_at, reverse=True)
        return tuple(matching[offset : offset + limit])

    def healthcheck(self) -> None:
        return None

    def close(self) -> None:
        return None


_LIST_RUNS_BASE = """
    SELECT
        id::text AS id, offer_slug, source_url, status, http_status,
        content_sha256, missing_evidence, error, checked_at
    FROM offer_ingestion_runs
    WHERE true
"""


def _row_to_run(row: Mapping[str, Any]) -> IngestionRun:
    return IngestionRun(
        id=row["id"],
        offer_slug=row["offer_slug"],
        source_url=row["source_url"],
        status=row["status"],
        http_status=row["http_status"],
        content_sha256=row["content_sha256"],
        missing_evidence=tuple(row["missing_evidence"] or []),
        error=row["error"],
        checked_at=row["checked_at"],
    )


class PostgresIngestionRunRepository:
    def __init__(self, database_url: str, *, engine: Engine | None = None) -> None:
        self._engine = engine or create_database_engine(database_url)

    def list_runs(
        self,
        *,
        limit: int,
        offset: int,
        status: str | None = None,
    ) -> tuple[IngestionRun, ...]:
        clauses = []
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if status is not None:
            clauses.append("AND status = :status")
            params["status"] = status

        query = text(
            _LIST_RUNS_BASE
            + "\n".join(clauses)
            + "\n    ORDER BY checked_at DESC\n    LIMIT :limit OFFSET :offset"
        )
        with self._engine.connect() as connection:
            rows = connection.execute(query, params).mappings().all()
        return tuple(_row_to_run(row) for row in rows)

    def healthcheck(self) -> None:
        with self._engine.connect() as connection:
            connection.execute(text("SELECT 1"))

    def close(self) -> None:
        self._engine.dispose()
