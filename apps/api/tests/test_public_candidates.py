import sys
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vesta_api.api.dialogue_routes import _public_candidates  # noqa: E402
from vesta_api.domain.models import (  # noqa: E402
    AccessRules,
    Availability,
    Candidate,
    MatchResult,
    Offer,
    Source,
)

NOW = datetime(2026, 9, 4, tzinfo=UTC)


def candidate(index: int) -> Candidate:
    offer = Offer(
        id=f"offer-{index}",
        name=f"Angebot {index}",
        summary=f"Verständliche Beschreibung {index}",
        needs=("counselling",),
        languages=("de",),
        access=AccessRules(),
        availability=Availability.CONFIRMED,
        contact_note="Direkt Kontakt aufnehmen.",
        source=Source(
            label="Angebotsseite",
            url="https://example.org/angebot",
            verified_at=NOW,
            expires_at=NOW + timedelta(days=1),
            verified_by="test",
        ),
        published=True,
    )
    return Candidate(
        offer=offer,
        score=140,
        reasons=("need_matches", "source_is_current"),
    )


class PublicCandidatesTest(unittest.TestCase):
    def test_serializes_offers_without_customer_facing_ai_explanations(self) -> None:
        match_result = MatchResult(
            candidates=tuple(candidate(index) for index in range(2)),
            human_handoff_required=False,
        )

        public_candidates = _public_candidates(match_result)

        self.assertEqual(
            ["offer-0", "offer-1"],
            [item.candidate.offer.id for item in public_candidates],
        )
        self.assertTrue(all(item.explanation is None for item in public_candidates))
        self.assertEqual(
            "Verständliche Beschreibung 0",
            public_candidates[0].candidate.offer.summary,
        )


if __name__ == "__main__":
    unittest.main()
