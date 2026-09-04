from vesta_api.domain.dialogue_catalog import QuestionDefinition
from vesta_api.domain.dialogue_models import DialogueState
from vesta_api.domain.models import Candidate


class NextQuestionPolicy:
    """Picks the next question to ask, derived from data rather than a stored
    decision tree.

    Simplification documented on purpose: relevance is "does at least one
    currently viable offer have an opinion on this attribute", ordered by
    ``question_definitions.priority``. There is no information-gain ranking —
    with today's five attributes that would be over-engineering; revisit if
    the attribute catalog grows substantially.
    """

    def __init__(self, questions: tuple[QuestionDefinition, ...]) -> None:
        self._questions = tuple(sorted(questions, key=lambda q: q.priority))

    def next_question(
        self,
        dialogue_state: DialogueState,
        candidates: tuple[Candidate, ...],
    ) -> QuestionDefinition | None:
        asked_or_declined = set(dialogue_state.asked_question_keys) | set(
            dialogue_state.declined_question_keys
        )
        answered_attribute_keys = {
            attribute.key
            for attribute in dialogue_state.attributes
            if attribute.status in ("confirmed", "unknown", "declined")
        }

        for question in self._questions:
            if question.need_keys and dialogue_state.need not in question.need_keys:
                continue
            if question.key in asked_or_declined:
                continue
            if question.attribute_key in answered_attribute_keys:
                continue
            if self._attribute_is_relevant(question.attribute_key, candidates):
                return question
        return None

    @staticmethod
    def _attribute_is_relevant(
        attribute_key: str, candidates: tuple[Candidate, ...]
    ) -> bool:
        for candidate in candidates:
            access = candidate.offer.access
            if attribute_key == "person.has_dog" and access.accepts_dogs is not None:
                return True
            if (
                attribute_key == "person.has_identity_document"
                and access.identity_document_required is True
            ):
                return True
            if attribute_key == "person.gender" and access.accepted_genders:
                return True
            if attribute_key == "person.is_adult" and (
                access.minimum_age is not None or access.maximum_age is not None
            ):
                return True
        return False
