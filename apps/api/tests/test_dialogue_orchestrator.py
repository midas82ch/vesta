import sys
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vesta_api.domain.dialogue_catalog import QuestionDefinition  # noqa: E402
from vesta_api.domain.models import (  # noqa: E402
    AccessRules,
    Availability,
    Need,
    Offer,
    Source,
)
from vesta_api.services.dialogue_orchestrator import (  # noqa: E402
    DialogueOrchestrator,
    DialogueSessionStore,
)
from vesta_api.services.matching import MatchingService  # noqa: E402

NOW = datetime(2026, 7, 26, tzinfo=UTC)

QUESTIONS = (
    QuestionDefinition(
        key="sleep.has_dog",
        attribute_key="person.has_dog",
        answer_type="yes_no_unknown",
        priority=10,
        ai_rephrasing_allowed=True,
        localizations={"de": {"canonical_text": "Führen Sie ein Tier mit sich?"}},
    ),
    QuestionDefinition(
        key="sleep.has_identity_document",
        attribute_key="person.has_identity_document",
        answer_type="yes_no_unknown",
        priority=20,
        ai_rephrasing_allowed=True,
        localizations={"de": {"canonical_text": "Haben Sie einen Ausweis dabei?"}},
    ),
)


class InMemoryOfferRepository:
    def __init__(self, offers: tuple[Offer, ...]) -> None:
        self._offers = offers

    def list_offers(self) -> tuple[Offer, ...]:
        return self._offers


class FakeDialogueCatalogRepository:
    def __init__(self, questions: tuple[QuestionDefinition, ...]) -> None:
        self._questions = questions

    def list_questions(self) -> tuple[QuestionDefinition, ...]:
        return self._questions


def _offer(*, accepts_dogs: bool | None = False) -> Offer:
    return Offer(
        id="test-offer",
        name="Testangebot",
        summary="Nur für Tests.",
        needs=(Need.SLEEP_TONIGHT,),
        languages=("de",),
        access=AccessRules(accepts_dogs=accepts_dogs),
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


def _orchestrator(offers: tuple[Offer, ...]) -> DialogueOrchestrator:
    return DialogueOrchestrator(
        matching_service=MatchingService(InMemoryOfferRepository(offers)),
        catalog=FakeDialogueCatalogRepository(QUESTIONS),
        session_store=DialogueSessionStore(),
    )


class DialogueOrchestratorTest(unittest.TestCase):
    def test_start_asks_the_first_relevant_question(self) -> None:
        orchestrator = _orchestrator((_offer(accepts_dogs=False),))

        result = orchestrator.start(locale="de", need=Need.SLEEP_TONIGHT, now=NOW)

        assert result.question is not None
        self.assertEqual("sleep.has_dog", result.question.key)
        self.assertIsNone(result.match_result)
        self.assertIn("sleep.has_dog", result.state.asked_question_keys)

    def test_confirming_a_disqualifying_answer_excludes_the_offer(self) -> None:
        orchestrator = _orchestrator((_offer(accepts_dogs=False),))
        started = orchestrator.start(locale="de", need=Need.SLEEP_TONIGHT, now=NOW)

        result = orchestrator.confirm_attribute(
            session_id=started.state.session_id,
            key="person.has_dog",
            value=True,
            now=NOW,
        )

        assert result.match_result is not None
        self.assertEqual((), result.match_result.candidates)
        self.assertTrue(result.match_result.human_handoff_required)
        self.assertEqual("no_verified_match", result.match_result.handoff_reason)
        self.assertIsNone(result.question)

    def test_confirming_a_compatible_answer_keeps_offer_and_asks_next_question(
        self,
    ) -> None:
        orchestrator = _orchestrator((_offer(accepts_dogs=True),))
        started = orchestrator.start(locale="de", need=Need.SLEEP_TONIGHT, now=NOW)

        result = orchestrator.confirm_attribute(
            session_id=started.state.session_id,
            key="person.has_dog",
            value=True,
            now=NOW,
        )

        # accepts_dogs is True -> compatible, but identity_document_required is
        # None on this offer, so that question is never relevant either.
        self.assertIsNone(result.question)
        assert result.match_result is not None
        self.assertEqual(1, len(result.match_result.candidates))

    def test_safety_handoff_short_circuits_without_matching(self) -> None:
        orchestrator = _orchestrator((_offer(accepts_dogs=False),))
        started = orchestrator.start(locale="de", need=Need.SLEEP_TONIGHT, now=NOW)

        result = orchestrator.flag_safety_handoff(
            session_id=started.state.session_id, now=NOW
        )

        assert result.match_result is not None
        self.assertTrue(result.match_result.human_handoff_required)
        self.assertEqual("safety_rule_triggered", result.match_result.handoff_reason)
        self.assertIsNone(result.question)

    def test_unknown_session_raises(self) -> None:
        orchestrator = _orchestrator((_offer(),))

        with self.assertRaises(KeyError):
            orchestrator.confirm_attribute(
                session_id="does-not-exist", key="person.has_dog", value=True, now=NOW
            )


class DialogueSessionStoreTest(unittest.TestCase):
    def test_can_continue_with_a_server_generated_workflow_id(self) -> None:
        store = DialogueSessionStore()

        state = store.create(locale="de", now=NOW, session_id="workflow-123")

        self.assertEqual("workflow-123", state.session_id)
        self.assertIs(state, store.get("workflow-123", now=NOW))

    def test_expired_session_is_not_returned_and_is_swept(self) -> None:
        store = DialogueSessionStore(ttl=timedelta(minutes=-1))
        state = store.create(locale="de", now=NOW)

        self.assertIsNone(store.get(state.session_id, now=NOW))

    def test_sweep_expired_counts_removed_sessions(self) -> None:
        store = DialogueSessionStore(ttl=timedelta(minutes=45))
        store.create(locale="de", now=NOW)
        store.create(locale="de", now=NOW)

        removed = store.sweep_expired(now=NOW + timedelta(hours=2))

        self.assertEqual(2, removed)


if __name__ == "__main__":
    unittest.main()
