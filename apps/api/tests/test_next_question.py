import sys
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vesta_api.domain.dialogue_catalog import QuestionDefinition  # noqa: E402
from vesta_api.domain.dialogue_models import AttributeState, DialogueState  # noqa: E402
from vesta_api.domain.models import (  # noqa: E402
    AccessRules,
    Availability,
    Candidate,
    Need,
    Offer,
    Source,
)
from vesta_api.services.next_question import NextQuestionPolicy  # noqa: E402

NOW = datetime(2026, 7, 26, tzinfo=UTC)

QUESTIONS = (
    QuestionDefinition(
        key="sleep.has_dog",
        attribute_key="person.has_dog",
        answer_type="yes_no_unknown",
        priority=10,
        ai_rephrasing_allowed=True,
        localizations={"de": {"canonical_text": "Hund?"}},
    ),
    QuestionDefinition(
        key="sleep.has_identity_document",
        attribute_key="person.has_identity_document",
        answer_type="yes_no_unknown",
        priority=20,
        ai_rephrasing_allowed=True,
        localizations={"de": {"canonical_text": "Ausweis?"}},
    ),
    QuestionDefinition(
        key="sleep.gender",
        attribute_key="person.gender",
        answer_type="single_choice",
        priority=30,
        ai_rephrasing_allowed=True,
        localizations={"de": {"canonical_text": "Zielgruppe?"}},
    ),
)


def _candidate(
    *,
    accepts_dogs: bool | None = None,
    requires_id: bool | None = None,
    accepted_genders: tuple[str, ...] = (),
) -> Candidate:
    offer = Offer(
        id="test-offer",
        name="Testangebot",
        summary="Nur für Tests.",
        needs=(Need.SLEEP_TONIGHT,),
        languages=("de",),
        access=AccessRules(
            accepts_dogs=accepts_dogs,
            identity_document_required=requires_id,
            accepted_genders=accepted_genders,
        ),
        availability=Availability.CONFIRMED,
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
    return Candidate(offer=offer, score=100, reasons=("need_matches",))


def _state(**kwargs: object) -> DialogueState:
    defaults: dict[str, object] = {
        "session_id": "s1",
        "locale": "de",
        "created_at": NOW,
        "expires_at": NOW + timedelta(minutes=45),
    }
    defaults.update(kwargs)
    return DialogueState(**defaults)  # type: ignore[arg-type]


class NextQuestionPolicyTest(unittest.TestCase):
    def test_picks_lowest_priority_relevant_question(self) -> None:
        policy = NextQuestionPolicy(QUESTIONS)
        candidates = (_candidate(accepts_dogs=False, requires_id=True),)

        question = policy.next_question(_state(), candidates)

        assert question is not None
        self.assertEqual("sleep.has_dog", question.key)

    def test_skips_attribute_with_no_opinion_among_candidates(self) -> None:
        policy = NextQuestionPolicy(QUESTIONS)
        candidates = (_candidate(requires_id=True),)  # accepts_dogs stays None

        question = policy.next_question(_state(), candidates)

        assert question is not None
        self.assertEqual("sleep.has_identity_document", question.key)

    def test_skips_already_answered_attribute(self) -> None:
        policy = NextQuestionPolicy(QUESTIONS)
        candidates = (_candidate(accepts_dogs=False, requires_id=True),)
        state = _state().with_attribute(
            AttributeState(key="person.has_dog", value=True, status="confirmed", source="user")
        )

        question = policy.next_question(state, candidates)

        assert question is not None
        self.assertEqual("sleep.has_identity_document", question.key)

    def test_skips_declined_question(self) -> None:
        policy = NextQuestionPolicy(QUESTIONS)
        candidates = (_candidate(accepts_dogs=False, requires_id=True),)
        state = _state(declined_question_keys=("sleep.has_dog",))

        question = policy.next_question(state, candidates)

        assert question is not None
        self.assertEqual("sleep.has_identity_document", question.key)

    def test_returns_none_when_no_candidates(self) -> None:
        policy = NextQuestionPolicy(QUESTIONS)

        self.assertIsNone(policy.next_question(_state(), ()))

    def test_returns_none_when_nothing_left_to_ask(self) -> None:
        policy = NextQuestionPolicy(QUESTIONS)
        candidates = (_candidate(),)  # no access opinions at all

        self.assertIsNone(policy.next_question(_state(), candidates))


if __name__ == "__main__":
    unittest.main()
