from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

from vesta_api.domain.audit_clock import monotonic_audit_time

WorkflowStage = Literal["input", "system", "output"]


@dataclass(frozen=True)
class NewWorkflowAuditEvent:
    workflow_id: str
    stage: WorkflowStage
    event_type: str
    summary: str
    payload: dict[str, Any]
    created_at: datetime = field(default_factory=monotonic_audit_time)


@dataclass(frozen=True)
class WorkflowAuditEvent:
    id: str
    workflow_id: str
    stage: WorkflowStage
    event_type: str
    summary: str
    payload: dict[str, Any]
    created_at: datetime


@dataclass(frozen=True)
class WorkflowAuditSummary:
    workflow_id: str
    started_at: datetime
    updated_at: datetime
    input_preview: str
    event_count: int
    has_input: bool
    has_system: bool
    has_output: bool
