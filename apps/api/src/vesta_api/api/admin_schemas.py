from datetime import datetime

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
