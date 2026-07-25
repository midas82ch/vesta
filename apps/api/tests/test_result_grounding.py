import sys
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vesta_api.domain.models import (  # noqa: E402
    AccessRules,
    Availability,
    Candidate,
    Need,
    Offer,
    Source,
)
from vesta_api.services.result_grounding import build_grounding_bundle  # noqa: E402

NOW = datetime(2026, 7, 26, tzinfo=UTC)


def _candidate(reasons: tuple[str, ...], uncertainties: tuple[str, ...]) -> Candidate:
    offer = Offer(
        id="offer-1",
        name="Testangebot",
        summary="Nur für Tests.",
        needs=(Need.SLEEP_TONIGHT,),
        languages=("de",),
        access=AccessRules(),
        availability=Availability.CALL_TO_CONFIRM,
        contact_note="Test",
        source=Source(
            label="Testquelle",
            url=None,
            verified_at=NOW - timedelta(days=1),
            expires_at=NOW + timedelta(days=1),
            verified_by="automated-test",
        ),
        published=True,
        is_demo=True,
    )
    return Candidate(offer=offer, score=100, reasons=reasons, uncertainties=uncertainties)


class BuildGroundingBundleTest(unittest.TestCase):
    def test_every_reason_and_uncertainty_becomes_a_traceable_fact(self) -> None:
        candidate = _candidate(
            reasons=("need_matches", "language_matches"),
            uncertainties=("availability_requires_contact",),
        )

        bundle = build_grounding_bundle(candidate)

        self.assertEqual("offer-1", bundle.offer_id)
        self.assertEqual(3, len(bundle.facts))
        fact_ids = {fact.id for fact in bundle.facts}
        self.assertIn("reason:need_matches", fact_ids)
        self.assertIn("uncertainty:availability_requires_contact", fact_ids)

    def test_allows_call_when_contact_is_required(self) -> None:
        candidate = _candidate(
            reasons=("need_matches",), uncertainties=("availability_requires_contact",)
        )

        bundle = build_grounding_bundle(candidate)

        self.assertEqual(("call",), bundle.allowed_next_actions)

    def test_no_next_action_when_nothing_is_uncertain(self) -> None:
        candidate = _candidate(reasons=("need_matches",), uncertainties=())

        bundle = build_grounding_bundle(candidate)

        self.assertEqual((), bundle.allowed_next_actions)

    def test_never_allows_reservation_or_guarantee_claims(self) -> None:
        candidate = _candidate(reasons=("need_matches",), uncertainties=())

        bundle = build_grounding_bundle(candidate)

        self.assertIn("place_is_reserved", bundle.forbidden_claims)
        self.assertIn("admission_is_guaranteed", bundle.forbidden_claims)


if __name__ == "__main__":
    unittest.main()
