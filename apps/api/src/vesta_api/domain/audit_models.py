from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from vesta_api.domain.audit_clock import monotonic_audit_time

AiPort = Literal["interpret", "render_question", "explain"]
AiOutcome = Literal["ai", "fallback_validation", "fallback_error"]


@dataclass(frozen=True)
class AiExchange:
    """The raw wire exchange with a live AI provider for a single call."""

    request: str
    response: str | None = None


@dataclass(frozen=True)
class NewAiAuditEntry:
    """An AI-gateway interaction about to be persisted."""

    port: AiPort
    provider: str
    model: str
    outcome: AiOutcome
    request_text: str
    session_id: str | None = None
    response_text: str | None = None
    violations: tuple[str, ...] = field(default_factory=tuple)
    error_detail: str | None = None
    created_at: datetime = field(default_factory=monotonic_audit_time)


@dataclass(frozen=True)
class AiAuditEntrySummary:
    """Listing row - no prompt/response text, kept lightweight for pagination."""

    id: str
    session_id: str | None
    port: AiPort
    provider: str
    model: str
    outcome: AiOutcome
    created_at: datetime


@dataclass(frozen=True)
class AiAuditEntryDetail:
    """Full record, including the raw prompt/response text."""

    id: str
    session_id: str | None
    port: AiPort
    provider: str
    model: str
    outcome: AiOutcome
    violations: tuple[str, ...]
    error_detail: str | None
    request_text: str
    response_text: str | None
    created_at: datetime
