import sys
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vesta_api.domain.models import (  # noqa: E402
    AccessRules,
    Availability,
    MatchQuery,
    Need,
    Offer,
    RiskFlag,
    Source,
)
from vesta_api.services.matching import MatchingService  # noqa: E402

NOW = datetime(2026, 7, 25, tzinfo=UTC)


class InMemoryOfferRepository:
    def __init__(self, offers: tuple[Offer, ...]) -> None:
        self._offers = offers

    def list_offers(self) -> tuple[Offer, ...]:
        return self._offers


def offer(
    *,
    accepts_dogs: bool | None = True,
    requires_id: bool | None = False,
    accepted_genders: tuple[str, ...] = (),
    expires_at: datetime | None = None,
) -> Offer:
    return Offer(
        id="test-offer",
        name="Testangebot",
        summary="Nur für automatisierte Tests.",
        needs=(Need.SLEEP_TONIGHT,),
        languages=("de", "fr"),
        access=AccessRules(
            accepts_dogs=accepts_dogs,
            identity_document_required=requires_id,
            accepted_genders=accepted_genders,
        ),
        availability=Availability.CALL_TO_CONFIRM,
        contact_note="Test",
        source=Source(
            label="Testquelle",
            url=None,
            verified_at=NOW - timedelta(days=1),
            expires_at=expires_at or NOW + timedelta(days=1),
            verified_by="automated-test",
        ),
        published=True,
        is_demo=True,
    )


class MatchingServiceTest(unittest.TestCase):
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
        self.assertEqual("no_verified_match", result.handoff_reason)

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


if __name__ == "__main__":
    unittest.main()
