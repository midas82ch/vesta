from math import atan2, cos, radians, sin, sqrt

from vesta_api.domain.models import (
    Availability,
    Candidate,
    GeoPoint,
    MatchQuery,
    MatchResult,
    Offer,
)
from vesta_api.repositories.offers import OfferRepository

EARTH_RADIUS_METERS = 6_371_008.8


def distance_in_meters(origin: GeoPoint, destination: GeoPoint) -> int:
    """Return deterministic great-circle distance for the small MVP catalog."""

    latitude_delta = radians(destination.latitude - origin.latitude)
    longitude_delta = radians(destination.longitude - origin.longitude)
    origin_latitude = radians(origin.latitude)
    destination_latitude = radians(destination.latitude)

    haversine = (
        sin(latitude_delta / 2) ** 2
        + cos(origin_latitude)
        * cos(destination_latitude)
        * sin(longitude_delta / 2) ** 2
    )
    haversine = min(1.0, max(0.0, haversine))
    angular_distance = 2 * atan2(sqrt(haversine), sqrt(1 - haversine))
    return round(EARTH_RADIUS_METERS * angular_distance)


class MatchingService:
    def __init__(self, repository: OfferRepository) -> None:
        self._repository = repository

    def match(self, query: MatchQuery) -> MatchResult:
        if query.risk_flags:
            return MatchResult(
                candidates=(),
                human_handoff_required=True,
                handoff_reason="safety_rule_triggered",
            )

        candidates: list[Candidate] = []
        for offer in self._repository.list_offers():
            candidate = self._evaluate(offer, query)
            if candidate is not None:
                candidates.append(candidate)

        if query.user_location is None:
            candidates.sort(key=lambda candidate: (-candidate.score, candidate.offer.name))
        else:
            candidates.sort(
                key=lambda candidate: (
                    -candidate.score,
                    candidate.distance_meters is None,
                    candidate.distance_meters or 0,
                    candidate.offer.name,
                )
            )
        return MatchResult(
            candidates=tuple(candidates),
            human_handoff_required=False,
            handoff_reason=None,
        )

    @staticmethod
    def _evaluate(offer: Offer, query: MatchQuery) -> Candidate | None:
        if not offer.published or offer.source.expires_at <= query.at:
            return None
        if query.need not in offer.needs:
            return None

        access = offer.access
        if query.dog is True and access.accepts_dogs is False:
            return None
        if query.has_identity_document is False and access.identity_document_required is True:
            return None
        if query.gender and access.accepted_genders:
            if query.gender not in access.accepted_genders:
                return None
        target_group_unknown = not query.gender and bool(access.accepted_genders)
        if query.age is not None:
            if access.minimum_age is not None and query.age < access.minimum_age:
                return None
            if access.maximum_age is not None and query.age > access.maximum_age:
                return None

        score = 100
        reasons = ["need_matches", "source_is_current"]
        uncertainties: list[str] = []

        if query.language.lower() in offer.languages:
            score += 20
            reasons.append("language_matches")
        else:
            uncertainties.append("requested_language_not_listed")

        if offer.availability is Availability.CONFIRMED:
            score += 20
            reasons.append("availability_confirmed")
        elif offer.availability is Availability.CALL_TO_CONFIRM:
            score += 5
            uncertainties.append("availability_requires_contact")
        else:
            uncertainties.append("availability_unknown")

        if query.dog is True and access.accepts_dogs is None:
            uncertainties.append("dog_access_unknown")
        if (
            query.has_identity_document is False
            and access.identity_document_required is None
        ):
            uncertainties.append("identity_document_rule_unknown")
        if target_group_unknown:
            uncertainties.append("target_group_must_be_confirmed")

        distance_meters = (
            distance_in_meters(query.user_location, offer.location)
            if query.user_location is not None and offer.location is not None
            else None
        )

        return Candidate(
            offer=offer,
            score=score,
            reasons=tuple(reasons),
            uncertainties=tuple(uncertainties),
            distance_meters=distance_meters,
        )
