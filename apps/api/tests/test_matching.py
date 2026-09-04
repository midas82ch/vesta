import sys
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vesta_api.api.schemas import candidate_to_response  # noqa: E402
from vesta_api.domain.models import (  # noqa: E402
    AccessRules,
    Availability,
    GeoPoint,
    MatchQuery,
    Need,
    Offer,
    OfferText,
    RiskFlag,
    Source,
)
from vesta_api.services.matching import MatchingService, distance_in_meters  # noqa: E402

NOW = datetime(2026, 7, 25, tzinfo=UTC)


class InMemoryOfferRepository:
    def __init__(self, offers: tuple[Offer, ...]) -> None:
        self._offers = offers

    def list_offers(self) -> tuple[Offer, ...]:
        return self._offers


def offer(
    *,
    offer_id: str = "test-offer",
    name: str = "Testangebot",
    accepts_dogs: bool | None = True,
    requires_id: bool | None = False,
    accepted_genders: tuple[str, ...] = (),
    expires_at: datetime | None = None,
    availability: Availability = Availability.CALL_TO_CONFIRM,
    location: GeoPoint | None = None,
    minimum_age: int | None = None,
    maximum_age: int | None = None,
    localizations: dict[str, OfferText] | None = None,
    localization_required: bool = False,
) -> Offer:
    return Offer(
        id=offer_id,
        name=name,
        summary="Nur für automatisierte Tests.",
        needs=(Need.SLEEP_TONIGHT,),
        languages=("de", "fr"),
        access=AccessRules(
            accepts_dogs=accepts_dogs,
            identity_document_required=requires_id,
            accepted_genders=accepted_genders,
            minimum_age=minimum_age,
            maximum_age=maximum_age,
        ),
        availability=availability,
        contact_note="Test",
        source=Source(
            label="Testquelle",
            url=None,
            verified_at=NOW - timedelta(days=1),
            expires_at=expires_at or NOW + timedelta(days=1),
            verified_by="automated-test",
        ),
        location=location,
        published=True,
        is_demo=True,
        localizations=localizations or {},
        localization_required=localization_required,
    )


class MatchingServiceTest(unittest.TestCase):
    def test_adult_true_satisfies_minimum_age_18(self) -> None:
        service = MatchingService(InMemoryOfferRepository((offer(minimum_age=18),)))

        result = service.match(
            MatchQuery(
                need=Need.SLEEP_TONIGHT,
                language="de",
                is_adult=True,
                at=NOW,
            )
        )

        self.assertEqual(1, len(result.candidates))

    def test_adult_false_excludes_minimum_age_18(self) -> None:
        service = MatchingService(InMemoryOfferRepository((offer(minimum_age=18),)))

        result = service.match(
            MatchQuery(
                need=Need.SLEEP_TONIGHT,
                language="de",
                is_adult=False,
                at=NOW,
            )
        )

        self.assertEqual((), result.candidates)

    def test_unknown_adult_status_keeps_offer_with_uncertainty(self) -> None:
        service = MatchingService(InMemoryOfferRepository((offer(minimum_age=18),)))

        result = service.match(
            MatchQuery(
                need=Need.SLEEP_TONIGHT,
                language="de",
                unknown_attributes=("person.is_adult",),
                at=NOW,
            )
        )

        self.assertIn("adult_status_must_be_confirmed", result.candidates[0].uncertainties)

    def test_non_binary_age_rule_is_not_used_for_exclusion(self) -> None:
        service = MatchingService(InMemoryOfferRepository((offer(minimum_age=21),)))

        result = service.match(
            MatchQuery(
                need=Need.SLEEP_TONIGHT,
                language="de",
                is_adult=False,
                at=NOW,
            )
        )

        self.assertEqual(1, len(result.candidates))
        self.assertIn("age_rule_requires_contact", result.candidates[0].uncertainties)

    def test_uses_reviewed_locale_or_german_fallback(self) -> None:
        localized_offer = offer(
            localizations={
                "de": OfferText("Deutscher Name", "Beschreibung", "Kontakt"),
                "fr": OfferText("Nom français", "Description", "Contact"),
            },
            localization_required=True,
        )
        service = MatchingService(InMemoryOfferRepository((localized_offer,)))

        french = service.match(
            MatchQuery(need=Need.SLEEP_TONIGHT, language="fr", at=NOW)
        )
        spanish = service.match(
            MatchQuery(need=Need.SLEEP_TONIGHT, language="es", at=NOW)
        )

        self.assertEqual("Nom français", french.candidates[0].offer.name)
        self.assertFalse(french.candidates[0].offer.localization_fallback)
        self.assertEqual("Deutscher Name", spanish.candidates[0].offer.name)
        self.assertTrue(spanish.candidates[0].offer.localization_fallback)
    def test_returns_current_accessible_offer(self) -> None:
        service = MatchingService(InMemoryOfferRepository((offer(),)))

        result = service.match(
            MatchQuery(
                need=Need.SLEEP_TONIGHT,
                language="fr",
                dog=True,
                has_identity_document=False,
                at=NOW,
            )
        )

        self.assertEqual(1, len(result.candidates))
        self.assertFalse(result.human_handoff_required)
        self.assertIn("language_matches", result.candidates[0].reasons)

    def test_excludes_offer_with_hard_access_conflict(self) -> None:
        service = MatchingService(
            InMemoryOfferRepository((offer(accepts_dogs=False),))
        )

        result = service.match(
            MatchQuery(
                need=Need.SLEEP_TONIGHT,
                language="de",
                dog=True,
                at=NOW,
            )
        )

        self.assertEqual((), result.candidates)
        self.assertFalse(result.human_handoff_required)
        self.assertIsNone(result.handoff_reason)

    def test_excludes_expired_information(self) -> None:
        service = MatchingService(
            InMemoryOfferRepository((offer(expires_at=NOW - timedelta(seconds=1)),))
        )

        result = service.match(
            MatchQuery(need=Need.SLEEP_TONIGHT, language="de", at=NOW)
        )

        self.assertEqual((), result.candidates)

    def test_marks_unknown_target_group_as_uncertain(self) -> None:
        service = MatchingService(
            InMemoryOfferRepository((offer(accepted_genders=("finta",)),))
        )

        result = service.match(
            MatchQuery(need=Need.SLEEP_TONIGHT, language="de", at=NOW)
        )

        self.assertEqual(1, len(result.candidates))
        self.assertIn(
            "target_group_must_be_confirmed",
            result.candidates[0].uncertainties,
        )

    def test_excludes_offer_for_different_target_group(self) -> None:
        service = MatchingService(
            InMemoryOfferRepository((offer(accepted_genders=("finta",)),))
        )

        result = service.match(
            MatchQuery(
                need=Need.SLEEP_TONIGHT,
                language="de",
                gender="other",
                at=NOW,
            )
        )

        self.assertEqual((), result.candidates)

    def test_safety_rule_short_circuits_matching(self) -> None:
        service = MatchingService(InMemoryOfferRepository((offer(),)))

        result = service.match(
            MatchQuery(
                need=Need.SLEEP_TONIGHT,
                language="de",
                at=NOW,
                risk_flags=(RiskFlag.SEVERE_INJURY,),
            )
        )

        self.assertEqual((), result.candidates)
        self.assertTrue(result.human_handoff_required)
        self.assertEqual("safety_rule_triggered", result.handoff_reason)

    def test_calculates_great_circle_distance(self) -> None:
        distance = distance_in_meters(
            GeoPoint(latitude=46.948, longitude=7.447),
            GeoPoint(latitude=46.944359, longitude=7.459041),
        )

        self.assertGreater(distance, 950)
        self.assertLess(distance, 1_100)

    def test_distance_breaks_tie_after_suitability(self) -> None:
        repository = InMemoryOfferRepository(
            (
                offer(
                    offer_id="far",
                    name="Weiter entfernt",
                    location=GeoPoint(latitude=46.944359, longitude=7.459041),
                ),
                offer(
                    offer_id="near",
                    name="Näher",
                    location=GeoPoint(latitude=46.949615, longitude=7.440293),
                ),
            )
        )
        service = MatchingService(repository)

        result = service.match(
            MatchQuery(
                need=Need.SLEEP_TONIGHT,
                language="de",
                at=NOW,
                user_location=GeoPoint(latitude=46.95, longitude=7.44),
            )
        )

        self.assertEqual(("near", "far"), tuple(c.offer.id for c in result.candidates))
        self.assertLess(
            result.candidates[0].distance_meters,
            result.candidates[1].distance_meters,
        )

    def test_suitability_remains_more_important_than_distance(self) -> None:
        service = MatchingService(
            InMemoryOfferRepository(
                (
                    offer(
                        offer_id="near",
                        name="Nah, aber abklären",
                        location=GeoPoint(latitude=46.95, longitude=7.44),
                    ),
                    offer(
                        offer_id="far",
                        name="Weiter, aber bestätigt",
                        availability=Availability.CONFIRMED,
                        location=GeoPoint(latitude=46.944359, longitude=7.459041),
                    ),
                )
            )
        )

        result = service.match(
            MatchQuery(
                need=Need.SLEEP_TONIGHT,
                language="de",
                at=NOW,
                user_location=GeoPoint(latitude=46.95, longitude=7.44),
            )
        )

        self.assertEqual(("far", "near"), tuple(c.offer.id for c in result.candidates))

    def test_offer_without_location_remains_visible_after_located_tie(self) -> None:
        service = MatchingService(
            InMemoryOfferRepository(
                (
                    offer(offer_id="unknown", name="Ohne Standort"),
                    offer(
                        offer_id="located",
                        name="Mit Standort",
                        location=GeoPoint(latitude=46.95, longitude=7.44),
                    ),
                )
            )
        )

        result = service.match(
            MatchQuery(
                need=Need.SLEEP_TONIGHT,
                language="de",
                at=NOW,
                user_location=GeoPoint(latitude=46.95, longitude=7.44),
            )
        )

        self.assertEqual(("located", "unknown"), tuple(c.offer.id for c in result.candidates))
        self.assertIsNone(result.candidates[1].distance_meters)

    def test_response_has_destination_only_directions_link(self) -> None:
        service = MatchingService(
            InMemoryOfferRepository(
                (
                    offer(
                        location=GeoPoint(
                            latitude=46.944359,
                            longitude=7.459041,
                            address="Muristrasse 6, 3006 Bern",
                        )
                    ),
                )
            )
        )
        result = service.match(
            MatchQuery(
                need=Need.SLEEP_TONIGHT,
                language="de",
                at=NOW,
                user_location=GeoPoint(latitude=46.948, longitude=7.447),
            )
        )

        response = candidate_to_response(result.candidates[0])

        self.assertEqual("Muristrasse 6, 3006 Bern", response.offer.address)
        assert response.offer.directions_url is not None
        self.assertIn("destination=46.944359%2C7.459041", response.offer.directions_url)
        self.assertIn("travelmode=walking", response.offer.directions_url)
        self.assertNotIn("origin=", response.offer.directions_url)

    def test_records_a_deterministic_exclusion_reason(self) -> None:
        adults_only = offer(minimum_age=18)
        service = MatchingService(InMemoryOfferRepository((adults_only,)))

        result = service.match(
            MatchQuery(
                need=Need.SLEEP_TONIGHT,
                language="de",
                at=NOW,
                is_adult=False,
            )
        )

        self.assertEqual((), result.candidates)
        self.assertEqual(1, len(result.excluded_offers))
        self.assertEqual("adults_only", result.excluded_offers[0].reason)


if __name__ == "__main__":
    unittest.main()
