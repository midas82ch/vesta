from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AdminLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=1, max_length=200)


class AiAuditEntrySummaryResponse(BaseModel):
    id: str
    session_id: str | None
    port: str
    provider: str
    model: str
    outcome: str
    created_at: datetime


class AiAuditLogListResponse(BaseModel):
    entries: list[AiAuditEntrySummaryResponse]


class AiAuditEntryDetailResponse(BaseModel):
    id: str
    session_id: str | None
    port: str
    provider: str
    model: str
    outcome: str
    violations: list[str]
    error_detail: str | None
    request_text: str
    response_text: str | None
    created_at: datetime


class WorkflowAuditSummaryResponse(BaseModel):
    workflow_id: str
    started_at: datetime
    updated_at: datetime
    input_preview: str
    event_count: int
    ai_call_count: int
    complete: bool
    has_fallback: bool


class WorkflowAuditListResponse(BaseModel):
    workflows: list[WorkflowAuditSummaryResponse]


class WorkflowAuditStepResponse(BaseModel):
    id: str
    kind: str
    event_type: str
    label: str
    summary: str
    created_at: datetime
    provider: str | None = None
    model: str | None = None
    outcome: str | None = None
    details: dict[str, Any]


class WorkflowAuditDetailResponse(BaseModel):
    workflow_id: str
    started_at: datetime
    updated_at: datetime
    complete: bool
    steps: list[WorkflowAuditStepResponse]


class IngestionRunResponse(BaseModel):
    id: str
    offer_slug: str
    source_url: str
    status: str
    http_status: int | None
    content_sha256: str | None
    missing_evidence: list[str]
    error: str | None
    checked_at: datetime


class IngestionRunListResponse(BaseModel):
    runs: list[IngestionRunResponse]
