from datetime import datetime

from pydantic import BaseModel, Field

from vesta_api.domain.models import Availability, Need, RiskFlag


class MatchRequest(BaseModel):
    need: Need
    language: str = Field(default="de", min_length=2, max_length=12)
    dog: bool | None = None
    has_identity_document: bool | None = None
    gender: str | None = Field(default=None, max_length=40)
    age: int | None = Field(default=None, ge=0, le=120)
    risk_flags: list[RiskFlag] = Field(default_factory=list)


class OfferSourceResponse(BaseModel):
    label: str
    url: str | None
    verified_at: datetime
    expires_at: datetime
    verified_by: str


class OfferResponse(BaseModel):
    id: str
    name: str
    summary: str
    languages: list[str]
    availability: Availability
    contact_note: str
    source: OfferSourceResponse
    is_demo: bool


class CandidateResponse(BaseModel):
    offer: OfferResponse
    reasons: list[str]
    uncertainties: list[str]


class MatchResponse(BaseModel):
    candidates: list[CandidateResponse]
    human_handoff_required: bool
    handoff_reason: str | None
    disclaimer: str
