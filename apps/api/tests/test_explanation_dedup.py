import sys
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vesta_api.api.dialogue_routes import _explain_candidates  # noqa: E402
from vesta_api.domain.ai_models import (  # noqa: E402
    ExplanationReason,
    ExplanationResult,
)
from vesta_api.domain.models import (  # noqa: E402
    AccessRules,
    Availability,
    Candidate,
    MatchResult,
    Offer,
    Source,
)

NOW = datetime(2026, 9, 2, tzinfo=UTC)


class CountingGateway:
    def __init__(self) -> None:
        self.calls = 0

    def explain(self, **_kwargs: object) -> ExplanationResult:
        self.calls += 1
        return ExplanationResult(
            headline="Passendes Angebot.",
            reasons=(
                ExplanationReason(
                    text="Der Bedarf passt.",
                    supported_by=("reason:need_matches",),
                ),
            ),
            clarification=None,
            next_action=None,
            source="template",
        )


def candidate(index: int) -> Candidate:
    offer = Offer(
        id=f"offer-{index}",
        name=f"Angebot {index}",
        summary="Beschreibung",
        needs=("counselling",),
        languages=("de",),
        access=AccessRules(),
        availability=Availability.CONFIRMED,
        contact_note="Kontakt",
        source=Source(
            label="Quelle",
            url=None,
            verified_at=NOW,
            expires_at=NOW + timedelta(days=1),
            verified_by="test",
        ),
        published=True,
    )
    return Candidate(offer=offer, score=100, reasons=("need_matches",))


class ExplanationDeduplicationTest(unittest.TestCase):
    def test_five_identical_fact_bundles_use_one_ai_call_and_keep_order(self) -> None:
        gateway = CountingGateway()
        match_result = MatchResult(
            candidates=tuple(candidate(index) for index in range(5)),
            human_handoff_required=False,
        )

        explained = _explain_candidates(
            match_result,
            gateway=gateway,  # type: ignore[arg-type]
            locale="de",
            session_id="session-1",
        )

        self.assertEqual(1, gateway.calls)
        self.assertEqual(
            [f"offer-{index}" for index in range(5)],
            [item.candidate.offer.id for item in explained],
        )


if __name__ == "__main__":
    unittest.main()
