from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class Need(StrEnum):
    SLEEP_TONIGHT = "sleep_tonight"
    BASIC_NEEDS = "basic_needs"
    COUNSELLING = "counselling"
    VICTIM_SUPPORT = "victim_support"


class Availability(StrEnum):
    CONFIRMED = "confirmed"
    CALL_TO_CONFIRM = "call_to_confirm"
    UNKNOWN = "unknown"


class ServiceTopic(StrEnum):
    FOOD = "food"
    HYGIENE = "hygiene"
    MEDICAL = "medical"
    ADDICTION = "addiction"
    HOUSING = "housing"
    FINANCES = "finances"
    LEGAL = "legal"
    MENTAL_HEALTH = "mental_health"
    VIOLENCE = "violence"


class RiskFlag(StrEnum):
    UNCONSCIOUS_OR_NOT_BREATHING = "unconscious_or_not_breathing"
    POSSIBLE_OVERDOSE = "possible_overdose"
    SEVERE_INJURY = "severe_injury"
    IMMEDIATE_VIOLENCE = "immediate_violence"
    EXPOSURE_RISK = "exposure_risk"
    ACUTE_SELF_HARM = "acute_self_harm"
    MINOR_IN_DANGER = "minor_in_danger"


@dataclass(frozen=True)
class AccessRules:
    accepts_dogs: bool | None = None
    identity_document_required: bool | None = None
    accepted_genders: tuple[str, ...] = ()
    minimum_age: int | None = None
    maximum_age: int | None = None


@dataclass(frozen=True)
class Source:
    label: str
    url: str | None
    verified_at: datetime
    expires_at: datetime
    verified_by: str


@dataclass(frozen=True)
class GeoPoint:
    latitude: float
    longitude: float
    address: str | None = None


@dataclass(frozen=True)
class OfferText:
    name: str
    summary: str
    contact_note: str


@dataclass(frozen=True)
class Offer:
    id: str
    name: str
    summary: str
    needs: tuple[str, ...]
    languages: tuple[str, ...]
    access: AccessRules
    availability: Availability
    contact_note: str
    source: Source
    location: GeoPoint | None = None
    published: bool = False
    is_demo: bool = False
    slug: str | None = None
    organization_name: str | None = None
    updated_at: datetime | None = None
    localizations: dict[str, OfferText] = field(default_factory=dict)
    localization_required: bool = False
    content_language: str = "de"
    localization_fallback: bool = False


@dataclass(frozen=True)
class MatchQuery:
    need: str
    language: str
    at: datetime
    dog: bool | None = None
    has_identity_document: bool | None = None
    gender: str | None = None
    is_adult: bool | None = None
    user_location: GeoPoint | None = None
    risk_flags: tuple[RiskFlag, ...] = ()
    unknown_attributes: tuple[str, ...] = ()
    service_topics: tuple[ServiceTopic, ...] = ()


@dataclass(frozen=True)
class Candidate:
    offer: Offer
    score: int
    reasons: tuple[str, ...]
    uncertainties: tuple[str, ...] = field(default_factory=tuple)
    distance_meters: int | None = None


@dataclass(frozen=True)
class ExcludedOffer:
    offer_id: str
    offer_name: str
    reason: str


@dataclass(frozen=True)
class MatchResult:
    candidates: tuple[Candidate, ...]
    human_handoff_required: bool
    handoff_reason: str | None = None
    excluded_offers: tuple[ExcludedOffer, ...] = ()
