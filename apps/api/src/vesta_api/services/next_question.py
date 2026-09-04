from vesta_api.domain.dialogue_catalog import QuestionDefinition
from vesta_api.domain.dialogue_models import DialogueState
from vesta_api.domain.models import Candidate


class NextQuestionPolicy:
    """Picks the next question to ask, derived from data rather than a stored
    decision tree.

    A question is relevant only when its answer can exclude an offer or
    resolve an access condition among the currently viable candidates. This
    keeps the public dialogue short and avoids collecting details that cannot
    change the result.
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
        if attribute_key == "person.has_dog":
            dog_rules = {candidate.offer.access.accepts_dogs for candidate in candidates}
            return False in dog_rules or (True in dog_rules and None in dog_rules)

        for candidate in candidates:
            access = candidate.offer.access
            if (
                attribute_key == "person.has_identity_document"
                and access.identity_document_required is True
            ):
                return True
            if attribute_key == "person.gender" and access.accepted_genders:
                return True
            if attribute_key == "person.is_adult" and (
                access.minimum_age == 18 or access.maximum_age == 17
            ):
                return True
        return False
