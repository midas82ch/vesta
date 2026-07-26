import json
from collections.abc import Mapping
from typing import Any, Protocol
from uuid import uuid4

from sqlalchemy import Engine, text

from vesta_api.domain.workflow_audit_models import (
    NewWorkflowAuditEvent,
    WorkflowAuditEvent,
    WorkflowAuditSummary,
)
from vesta_api.repositories.database import create_database_engine


class WorkflowAuditLogRepository(Protocol):
    def record(self, event: NewWorkflowAuditEvent) -> None: ...

    def list_workflows(
        self, *, limit: int, offset: int
    ) -> tuple[WorkflowAuditSummary, ...]: ...

    def list_events(self, workflow_id: str) -> tuple[WorkflowAuditEvent, ...]: ...

    def healthcheck(self) -> None: ...

    def close(self) -> None: ...


class InMemoryWorkflowAuditLogRepository:
    def __init__(self) -> None:
        self._events: dict[str, WorkflowAuditEvent] = {}

    def record(self, event: NewWorkflowAuditEvent) -> None:
        event_id = str(uuid4())
        self._events[event_id] = WorkflowAuditEvent(
            id=event_id,
            workflow_id=event.workflow_id,
            stage=event.stage,
            event_type=event.event_type,
            summary=event.summary,
            payload=event.payload,
            created_at=event.created_at,
        )

    def list_workflows(
        self, *, limit: int, offset: int
    ) -> tuple[WorkflowAuditSummary, ...]:
        grouped: dict[str, list[WorkflowAuditEvent]] = {}
        for event in self._events.values():
            grouped.setdefault(event.workflow_id, []).append(event)

        summaries = []
        for workflow_id, events in grouped.items():
            events.sort(key=lambda event: event.created_at)
            first_input = next(
                (event.summary for event in events if event.stage == "input"),
                "Workflow ohne erfasste Eingabe",
            )
            stages = {event.stage for event in events}
            summaries.append(
                WorkflowAuditSummary(
                    workflow_id=workflow_id,
                    started_at=events[0].created_at,
                    updated_at=events[-1].created_at,
                    input_preview=first_input,
                    event_count=len(events),
                    has_input="input" in stages,
                    has_system="system" in stages,
                    has_output="output" in stages,
                )
            )
        summaries.sort(key=lambda summary: summary.updated_at, reverse=True)
        return tuple(summaries[offset : offset + limit])

    def list_events(self, workflow_id: str) -> tuple[WorkflowAuditEvent, ...]:
        events = [
            event for event in self._events.values() if event.workflow_id == workflow_id
        ]
        events.sort(key=lambda event: event.created_at)
        return tuple(events)

    def healthcheck(self) -> None:
        return None

    def close(self) -> None:
        return None


_RECORD = text(
    """
    INSERT INTO dialogue_workflow_log (
        id, workflow_id, stage, event_type, summary, payload, created_at
    )
    VALUES (
        :id, :workflow_id, :stage, :event_type, :summary,
        CAST(:payload AS jsonb), :created_at
    )
    """
)

_LIST_WORKFLOWS = text(
    """
    SELECT
        workflow_id,
        MIN(created_at) AS started_at,
        MAX(created_at) AS updated_at,
        COALESCE(
            (ARRAY_AGG(summary ORDER BY created_at)
                FILTER (WHERE stage = 'input'))[1],
            'Workflow ohne erfasste Eingabe'
        ) AS input_preview,
        COUNT(*)::int AS event_count,
        BOOL_OR(stage = 'input') AS has_input,
        BOOL_OR(stage = 'system') AS has_system,
        BOOL_OR(stage = 'output') AS has_output
    FROM dialogue_workflow_log
    GROUP BY workflow_id
    ORDER BY updated_at DESC
    LIMIT :limit OFFSET :offset
    """
)

_LIST_EVENTS = text(
    """
    SELECT
        id::text AS id, workflow_id, stage, event_type, summary, payload, created_at
    FROM dialogue_workflow_log
    WHERE workflow_id = :workflow_id
    ORDER BY created_at, id
    """
)


def _row_to_summary(row: Mapping[str, Any]) -> WorkflowAuditSummary:
    return WorkflowAuditSummary(
        workflow_id=row["workflow_id"],
        started_at=row["started_at"],
        updated_at=row["updated_at"],
        input_preview=row["input_preview"],
        event_count=int(row["event_count"]),
        has_input=bool(row["has_input"]),
        has_system=bool(row["has_system"]),
        has_output=bool(row["has_output"]),
    )


def _row_to_event(row: Mapping[str, Any]) -> WorkflowAuditEvent:
    return WorkflowAuditEvent(
        id=row["id"],
        workflow_id=row["workflow_id"],
        stage=row["stage"],
        event_type=row["event_type"],
        summary=row["summary"],
        payload=dict(row["payload"] or {}),
        created_at=row["created_at"],
    )


class PostgresWorkflowAuditLogRepository:
    def __init__(self, database_url: str, *, engine: Engine | None = None) -> None:
        self._engine = engine or create_database_engine(database_url)

    def record(self, event: NewWorkflowAuditEvent) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                _RECORD,
                {
                    "id": uuid4(),
                    "workflow_id": event.workflow_id,
                    "stage": event.stage,
                    "event_type": event.event_type,
                    "summary": event.summary,
                    "payload": json.dumps(event.payload, ensure_ascii=False),
                    "created_at": event.created_at,
                },
            )

    def list_workflows(
        self, *, limit: int, offset: int
    ) -> tuple[WorkflowAuditSummary, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                _LIST_WORKFLOWS, {"limit": limit, "offset": offset}
            ).mappings().all()
        return tuple(_row_to_summary(row) for row in rows)

    def list_events(self, workflow_id: str) -> tuple[WorkflowAuditEvent, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                _LIST_EVENTS, {"workflow_id": workflow_id}
            ).mappings().all()
        return tuple(_row_to_event(row) for row in rows)

    def healthcheck(self) -> None:
        with self._engine.connect() as connection:
            connection.execute(text("SELECT 1"))

    def close(self) -> None:
        self._engine.dispose()
