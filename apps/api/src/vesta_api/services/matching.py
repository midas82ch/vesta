from dataclasses import replace
from math import atan2, cos, radians, sin, sqrt

from vesta_api.domain.models import (
    Availability,
    Candidate,
    ExcludedOffer,
    GeoPoint,
    MatchQuery,
    MatchResult,
    Offer,
)
from vesta_api.repositories.offers import OfferRepository
from vesta_api.services.service_topics import detect_service_topics

EARTH_RADIUS_METERS = 6_371_008.8
PUBLIC_RESULT_LIMIT = 3
EXPLICIT_ACCESS_MATCH_SCORE = 25
AGE_ACCESS_MATCH_SCORE = 20
SERVICE_TOPIC_MATCH_SCORE = 40


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
        excluded_offers: list[ExcludedOffer] = []
        for offer in self._repository.list_offers():
            localized = self._localize_offer(offer, query.language)
            if localized is None:
                excluded_offers.append(
                    ExcludedOffer(offer.id, offer.name, "reviewed_localization_missing")
                )
                continue
            exclusion_reason = self._exclusion_reason(localized, query)
            if exclusion_reason is not None:
                excluded_offers.append(
                    ExcludedOffer(localized.id, localized.name, exclusion_reason)
                )
                continue
            candidate = self._evaluate(localized, query)
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
            excluded_offers=tuple(excluded_offers),
        )

    @staticmethod
    def _exclusion_reason(offer: Offer, query: MatchQuery) -> str | None:
        if not offer.published:
            return "offer_not_published"
        if offer.source.expires_at <= query.at:
            return "source_verification_expired"
        if query.need not in offer.needs:
            return "need_does_not_match"
        access = offer.access
        if query.dog is True and access.accepts_dogs is False:
            return "dog_not_accepted"
        if query.has_identity_document is False and access.identity_document_required is True:
            return "identity_document_required"
        if query.gender and access.accepted_genders and query.gender not in access.accepted_genders:
            return "target_group_not_accepted"
        if access.minimum_age == 18 and query.is_adult is False:
            return "adults_only"
        if access.maximum_age == 17 and query.is_adult is True:
            return "minors_only"
        return None

    @staticmethod
    def _localize_offer(offer: Offer, locale: str) -> Offer | None:
        requested = locale.lower()
        localization = offer.localizations.get(requested)
        fallback = False
        content_language = requested
        if localization is None:
            localization = offer.localizations.get("de")
            fallback = requested != "de"
            content_language = "de"
        if localization is None:
            if offer.localization_required:
                return None
            return replace(
                offer,
                content_language="de",
                localization_fallback=requested != "de",
            )
        return replace(
            offer,
            name=localization.name,
            summary=localization.summary,
            contact_note=localization.contact_note,
            content_language=content_language,
            localization_fallback=fallback,
        )

    @staticmethod
    def _evaluate(offer: Offer, query: MatchQuery) -> Candidate:
        access = offer.access
        target_group_unknown = not query.gender and bool(access.accepted_genders)

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

        if query.service_topics:
            offer_text = " ".join(
                part
                for part in (
                    offer.name,
                    offer.summary,
                    offer.contact_note,
                    offer.organization_name,
                )
                if part
            )
            offer_topics = detect_service_topics(offer_text, offer.content_language)
            matching_topics = tuple(
                topic for topic in query.service_topics if topic in offer_topics
            )
            if matching_topics:
                score += SERVICE_TOPIC_MATCH_SCORE * len(matching_topics)
                reasons.extend(
                    f"service_topic_matches:{topic}" for topic in matching_topics
                )
            else:
                uncertainties.append("requested_topic_not_explicitly_matched")

        if query.dog is True:
            if access.accepts_dogs is True:
                score += EXPLICIT_ACCESS_MATCH_SCORE
                reasons.append("dog_access_confirmed")
            elif access.accepts_dogs is None:
                uncertainties.append("dog_access_unknown")
        if (
            query.has_identity_document is False
            and access.identity_document_required is False
        ):
            score += EXPLICIT_ACCESS_MATCH_SCORE
            reasons.append("identity_document_not_required")
        elif (
            query.has_identity_document is False
            and access.identity_document_required is None
        ):
            uncertainties.append("identity_document_rule_unknown")
        if query.gender and access.accepted_genders:
            score += EXPLICIT_ACCESS_MATCH_SCORE
            reasons.append("target_group_matches")
        if target_group_unknown:
            uncertainties.append("target_group_must_be_confirmed")
        if (
            "person.has_identity_document" in query.unknown_attributes
            and access.identity_document_required is True
        ):
            uncertainties.append("identity_document_must_be_confirmed")
        has_age_rule = access.minimum_age is not None or access.maximum_age is not None
        if "person.is_adult" in query.unknown_attributes and has_age_rule:
            uncertainties.append("adult_status_must_be_confirmed")
        if query.is_adult is not None and has_age_rule:
            exactly_resolved = access.minimum_age in (None, 18) and access.maximum_age in (
                None,
                17,
            )
            if not exactly_resolved:
                uncertainties.append("age_rule_requires_contact")
            elif query.is_adult is True and access.minimum_age == 18:
                score += AGE_ACCESS_MATCH_SCORE
                reasons.append("adult_access_matches")
            elif query.is_adult is False and access.maximum_age == 17:
                score += AGE_ACCESS_MATCH_SCORE
                reasons.append("minor_access_matches")

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


def shortlist_match_result(
    result: MatchResult,
    *,
    limit: int = PUBLIC_RESULT_LIMIT,
) -> MatchResult:
    """Return a manageable public selection while retaining audit traceability."""

    if limit < 1:
        raise ValueError("limit_must_be_positive")
    if len(result.candidates) <= limit:
        return result

    selected = result.candidates[:limit]
    lower_ranked = tuple(
        ExcludedOffer(candidate.offer.id, candidate.offer.name, "lower_relevance_rank")
        for candidate in result.candidates[limit:]
    )
    return MatchResult(
        candidates=selected,
        human_handoff_required=result.human_handoff_required,
        handoff_reason=result.handoff_reason,
        excluded_offers=result.excluded_offers + lower_ranked,
    )
