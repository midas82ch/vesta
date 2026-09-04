import sys
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vesta_api.domain.dialogue_models import (  # noqa: E402
    AttributeState,
    DialogueState,
)

NOW = datetime(2026, 7, 26, tzinfo=UTC)


class AttributeStateTest(unittest.TestCase):
    def test_ai_source_cannot_be_created_as_confirmed(self) -> None:
        with self.assertRaises(ValueError):
            AttributeState(key="person.has_dog", value=True, status="confirmed", source="ai")

    def test_ai_source_can_be_proposed(self) -> None:
        attribute = AttributeState(
            key="person.has_dog", value=True, status="proposed", source="ai"
        )
        self.assertEqual("proposed", attribute.status)

    def test_user_source_can_be_confirmed_directly(self) -> None:
        attribute = AttributeState(
            key="person.has_dog", value=True, status="confirmed", source="user"
        )
        self.assertEqual("confirmed", attribute.status)


class DialogueStateTest(unittest.TestCase):
    def _state(self) -> DialogueState:
        return DialogueState(
            session_id="s1", locale="de", created_at=NOW, expires_at=NOW + timedelta(minutes=45)
        )

    def test_with_attribute_replaces_existing_key(self) -> None:
        state = self._state()
        proposed = AttributeState(
            key="person.has_dog", value=True, status="proposed", source="ai"
        )
        state = state.with_attribute(proposed)
        self.assertEqual("proposed", state.attribute("person.has_dog").status)

        confirmed = AttributeState(
            key="person.has_dog", value=True, status="confirmed", source="user"
        )
        state = state.with_attribute(confirmed)

        self.assertEqual(1, len(state.attributes))
        self.assertEqual("confirmed", state.attribute("person.has_dog").status)

    def test_confirmed_values_excludes_proposed_and_unknown(self) -> None:
        state = self._state()
        state = state.with_attribute(
            AttributeState(key="person.has_dog", value=True, status="proposed", source="ai")
        )
        state = state.with_attribute(
            AttributeState(
                key="person.has_identity_document",
                value=False,
                status="confirmed",
                source="user",
            )
        )

        self.assertEqual({"person.has_identity_document": False}, state.confirmed_values())

    def test_is_expired(self) -> None:
        state = self._state()
        self.assertFalse(state.is_expired(NOW))
        self.assertTrue(state.is_expired(NOW + timedelta(hours=1)))

    def test_with_question_asked_is_idempotent(self) -> None:
        state = DialogueState(
            session_id="s1",
            locale="de",
            created_at=NOW,
            expires_at=NOW + timedelta(minutes=45),
            service_topics=("housing",),
        )
        state = state.with_question_asked("sleep.has_dog")
        state = state.with_question_asked("sleep.has_dog")
        self.assertEqual(("sleep.has_dog",), state.asked_question_keys)
        self.assertEqual(("housing",), state.service_topics)


if __name__ == "__main__":
    unittest.main()
