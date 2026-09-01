from dataclasses import dataclass
from datetime import datetime
from typing import Literal

IngestionStatus = Literal[
    "imported", "evidence_missing", "fetch_failed", "skipped_disabled"
]


@dataclass(frozen=True)
class IngestionRun:
    """A past automated offer-source check, read back for the admin area."""

    id: str
    offer_slug: str
    source_url: str
    status: IngestionStatus
    http_status: int | None
    content_sha256: str | None
    missing_evidence: tuple[str, ...]
    error: str | None
    checked_at: datetime
