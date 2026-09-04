from datetime import datetime
from typing import Literal
from urllib.parse import urlencode

from pydantic import BaseModel, Field, StrictBool, field_validator

from vesta_api.domain.models import (
    Availability,
    Candidate,
    GeoPoint,
    RiskFlag,
    ServiceTopic,
)


class UserLocationInput(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    @field_validator("latitude", "longitude")
    @classmethod
    def reduce_precision(cls, value: float) -> float:
        return round(value, 3)

    def to_domain(self) -> GeoPoint:
        return GeoPoint(latitude=self.latitude, longitude=self.longitude)


class MatchRequest(BaseModel):
    need: str = Field(pattern=r"^[a-z0-9_-]+$", min_length=1, max_length=100)
    language: str = Field(default="de", min_length=2, max_length=12)
    dog: bool | None = None
    has_identity_document: bool | None = None
    gender: str | None = Field(default=None, max_length=40)
    is_adult: StrictBool | None = None
    user_location: UserLocationInput | None = None
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    service_topics: list[ServiceTopic] = Field(default_factory=list, max_length=9)


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
    address: str | None
    directions_url: str | None
    source: OfferSourceResponse
    is_demo: bool
    content_language: str
    localization_fallback: bool


class CandidateResponse(BaseModel):
    offer: OfferResponse
    reasons: list[str]
    uncertainties: list[str]
    distance_meters: int | None


class MatchResponse(BaseModel):
    candidates: list[CandidateResponse]
    outcome: Literal["matches", "no_match", "handoff"]
    human_handoff_required: bool
    handoff_reason: str | None
    disclaimer: str


class PublicCategoryResponse(BaseModel):
    key: str
    title: str
    description: str
    icon: str


class PublicCategoryListResponse(BaseModel):
    categories: list[PublicCategoryResponse]


def candidate_to_response(candidate: Candidate) -> CandidateResponse:
    directions_url = None
    if candidate.offer.location is not None:
        destination = (
            f"{candidate.offer.location.latitude:.6f},"
            f"{candidate.offer.location.longitude:.6f}"
        )
        directions_url = (
            "https://www.google.com/maps/dir/?"
            + urlencode(
                {
                    "api": "1",
                    "destination": destination,
                    "travelmode": "walking",
                }
            )
        )

    return CandidateResponse(
        offer=OfferResponse(
            id=candidate.offer.id,
            name=candidate.offer.name,
            summary=candidate.offer.summary,
            languages=list(candidate.offer.languages),
            availability=candidate.offer.availability,
            contact_note=candidate.offer.contact_note,
            address=(
                candidate.offer.location.address
                if candidate.offer.location is not None
                else None
            ),
            directions_url=directions_url,
            source=OfferSourceResponse(
                label=candidate.offer.source.label,
                url=candidate.offer.source.url,
                verified_at=candidate.offer.source.verified_at,
                expires_at=candidate.offer.source.expires_at,
                verified_by=candidate.offer.source.verified_by,
            ),
            is_demo=candidate.offer.is_demo,
            content_language=candidate.offer.content_language,
            localization_fallback=candidate.offer.localization_fallback,
        ),
        reasons=list(candidate.reasons),
        uncertainties=list(candidate.uncertainties),
        distance_meters=candidate.distance_meters,
    )
