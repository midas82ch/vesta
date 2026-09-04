from dataclasses import dataclass
from datetime import datetime
from typing import Literal

OfferImportStatus = Literal[
    "queued",
    "fetching",
    "extracting",
    "translating",
    "ready_for_review",
    "failed",
]


@dataclass(frozen=True)
class OfferImportJob:
    id: str
    source_url: str
    normalized_url: str
    status: OfferImportStatus
    requested_by: str
    offer_id: str | None
    source_language: str | None
    content_sha256: str | None
    extracted_data: dict[str, object] | None
    evidence: tuple[dict[str, str], ...]
    duplicate_offer_ids: tuple[str, ...]
    error_code: str | None
    error_detail: str | None
    attempts: int
    lease_expires_at: datetime | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    updated_at: datetime
