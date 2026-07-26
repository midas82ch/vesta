import json
from collections.abc import Mapping
from typing import Any, Protocol
from uuid import uuid4

from sqlalchemy import Engine, text

from vesta_api.domain.audit_models import (
    AiAuditEntryDetail,
    AiAuditEntrySummary,
    NewAiAuditEntry,
)
from vesta_api.repositories.database import create_database_engine


class AiAuditLogRepository(Protocol):
    def record(self, entry: NewAiAuditEntry) -> None: ...

    def list_entries(
        self,
        *,
        limit: int,
        offset: int,
        port: str | None = None,
        outcome: str | None = None,
        session_id: str | None = None,
    ) -> tuple[AiAuditEntrySummary, ...]: ...

    def get_entry(self, entry_id: str) -> AiAuditEntryDetail | None: ...

    def healthcheck(self) -> None: ...

    def close(self) -> None: ...


def _matches(
    entry: AiAuditEntryDetail,
    *,
    port: str | None,
    outcome: str | None,
    session_id: str | None,
) -> bool:
    if port is not None and entry.port != port:
        return False
    if outcome is not None and entry.outcome != outcome:
        return False
    if session_id is not None and entry.session_id != session_id:
        return False
    return True


class InMemoryAiAuditLogRepository:
    """Used for local development/tests without a configured DATABASE_URL."""

    def __init__(self) -> None:
        self._entries: dict[str, AiAuditEntryDetail] = {}

    def record(self, entry: NewAiAuditEntry) -> None:
        entry_id = str(uuid4())
        self._entries[entry_id] = AiAuditEntryDetail(
            id=entry_id,
            session_id=entry.session_id,
            port=entry.port,
            provider=entry.provider,
            model=entry.model,
            outcome=entry.outcome,
            violations=entry.violations,
            error_detail=entry.error_detail,
            request_text=entry.request_text,
            response_text=entry.response_text,
            created_at=entry.created_at,
        )

    def list_entries(
        self,
        *,
        limit: int,
        offset: int,
        port: str | None = None,
        outcome: str | None = None,
        session_id: str | None = None,
    ) -> tuple[AiAuditEntrySummary, ...]:
        matching = [
            entry
            for entry in self._entries.values()
            if _matches(entry, port=port, outcome=outcome, session_id=session_id)
        ]
        matching.sort(key=lambda entry: entry.created_at, reverse=True)
        page = matching[offset : offset + limit]
        return tuple(
            AiAuditEntrySummary(
                id=entry.id,
                session_id=entry.session_id,
                port=entry.port,
                provider=entry.provider,
                model=entry.model,
                outcome=entry.outcome,
                created_at=entry.created_at,
            )
            for entry in page
        )

    def get_entry(self, entry_id: str) -> AiAuditEntryDetail | None:
        return self._entries.get(entry_id)

    def healthcheck(self) -> None:
        return None

    def close(self) -> None:
        return None


_RECORD = text(
    """
    INSERT INTO ai_interaction_log (
        id, session_id, port, provider, model, outcome,
        violations, error_detail, request_text, response_text, created_at
    )
    VALUES (
        :id, :session_id, :port, :provider, :model, :outcome,
        CAST(:violations AS jsonb), :error_detail, :request_text, :response_text,
        :created_at
    )
    """
)

_LIST_ENTRIES_BASE = """
    SELECT id::text AS id, session_id, port, provider, model, outcome, created_at
    FROM ai_interaction_log
    WHERE true
"""

_GET_ENTRY = text(
    """
    SELECT
        id::text AS id, session_id, port, provider, model, outcome,
        violations, error_detail, request_text, response_text, created_at
    FROM ai_interaction_log
    WHERE id = :id
    """
)


def _row_to_summary(row: Mapping[str, Any]) -> AiAuditEntrySummary:
    return AiAuditEntrySummary(
        id=row["id"],
        session_id=row["session_id"],
        port=row["port"],
        provider=row["provider"],
        model=row["model"],
        outcome=row["outcome"],
        created_at=row["created_at"],
    )


def _row_to_detail(row: Mapping[str, Any]) -> AiAuditEntryDetail:
    return AiAuditEntryDetail(
        id=row["id"],
        session_id=row["session_id"],
        port=row["port"],
        provider=row["provider"],
        model=row["model"],
        outcome=row["outcome"],
        violations=tuple(row["violations"] or []),
        error_detail=row["error_detail"],
        request_text=row["request_text"],
        response_text=row["response_text"],
        created_at=row["created_at"],
    )


class PostgresAiAuditLogRepository:
    def __init__(self, database_url: str, *, engine: Engine | None = None) -> None:
        self._engine = engine or create_database_engine(database_url)

    def record(self, entry: NewAiAuditEntry) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                _RECORD,
                {
                    "id": uuid4(),
                    "session_id": entry.session_id,
                    "port": entry.port,
                    "provider": entry.provider,
                    "model": entry.model,
                    "outcome": entry.outcome,
                    "violations": json.dumps(list(entry.violations)),
                    "error_detail": entry.error_detail,
                    "request_text": entry.request_text,
                    "response_text": entry.response_text,
                    "created_at": entry.created_at,
                },
            )

    def list_entries(
        self,
        *,
        limit: int,
        offset: int,
        port: str | None = None,
        outcome: str | None = None,
        session_id: str | None = None,
    ) -> tuple[AiAuditEntrySummary, ...]:
        clauses = []
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if port is not None:
            clauses.append("AND port = :port")
            params["port"] = port
        if outcome is not None:
            clauses.append("AND outcome = :outcome")
            params["outcome"] = outcome
        if session_id is not None:
            clauses.append("AND session_id = :session_id")
            params["session_id"] = session_id

        query = text(
            _LIST_ENTRIES_BASE
            + "\n".join(clauses)
            + "\n    ORDER BY created_at DESC\n    LIMIT :limit OFFSET :offset"
        )
        with self._engine.connect() as connection:
            rows = connection.execute(query, params).mappings().all()
        return tuple(_row_to_summary(row) for row in rows)

    def get_entry(self, entry_id: str) -> AiAuditEntryDetail | None:
        with self._engine.connect() as connection:
            row = connection.execute(_GET_ENTRY, {"id": entry_id}).mappings().first()
        return _row_to_detail(row) if row is not None else None

    def healthcheck(self) -> None:
        with self._engine.connect() as connection:
            connection.execute(text("SELECT 1"))

    def close(self) -> None:
        self._engine.dispose()
