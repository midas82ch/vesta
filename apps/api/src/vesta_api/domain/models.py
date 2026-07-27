from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

MINIMUM_PERSON_AGE = 6
MAXIMUM_PERSON_AGE = 120


class Need(StrEnum):
    SLEEP_TONIGHT = "sleep_tonight"
    BASIC_NEEDS = "basic_needs"
    COUNSELLING = "counselling"


class Availability(StrEnum):
    CONFIRMED = "confirmed"
    CALL_TO_CONFIRM = "call_to_confirm"
    UNKNOWN = "unknown"


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
class Offer:
    id: str
    name: str
    summary: str
    needs: tuple[Need, ...]
    languages: tuple[str, ...]
    access: AccessRules
    availability: Availability
    contact_note: str
    source: Source
    location: GeoPoint | None = None
    published: bool = False
    is_demo: bool = False


@dataclass(frozen=True)
class MatchQuery:
    need: Need
    language: str
    at: datetime
    dog: bool | None = None
    has_identity_document: bool | None = None
    gender: str | None = None
    age: int | None = None
    user_location: GeoPoint | None = None
    risk_flags: tuple[RiskFlag, ...] = ()

    def __post_init__(self) -> None:
        if self.age is None:
            return
        if isinstance(self.age, bool) or not isinstance(self.age, int):
            raise ValueError("age must be an integer")
        if not MINIMUM_PERSON_AGE <= self.age <= MAXIMUM_PERSON_AGE:
            raise ValueError(
                f"age must be between {MINIMUM_PERSON_AGE} and {MAXIMUM_PERSON_AGE}"
            )


@dataclass(frozen=True)
class Candidate:
    offer: Offer
    score: int
    reasons: tuple[str, ...]
    uncertainties: tuple[str, ...] = field(default_factory=tuple)
    distance_meters: int | None = None


@dataclass(frozen=True)
class MatchResult:
    candidates: tuple[Candidate, ...]
    human_handoff_required: bool
    handoff_reason: str | None = None
