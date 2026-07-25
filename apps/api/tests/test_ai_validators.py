import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vesta_api.ai.validators import (  # noqa: E402
    validate_explanation,
    validate_interpretation,
    validate_rendered_question,
)
from vesta_api.domain.ai_models import (  # noqa: E402
    AttributeProposal,
    ExplanationReason,
    ExplanationResult,
    GroundingBundle,
    GroundingFact,
    InterpretationResult,
    QuestionOption,
    RenderedQuestion,
)
from vesta_api.domain.dialogue_catalog import (  # noqa: E402
    AttributeDefinition,
    AttributeOption,
)


class ValidateInterpretationTest(unittest.TestCase):
    def test_accepts_a_well_formed_result(self) -> None:
        result = InterpretationResult(
            need_key="sleep_tonight",
            proposals=(AttributeProposal(key="person.has_dog", value=True),),
            requires_confirmation=("person.has_dog",),
        )

        violations = validate_interpretation(
            result,
            known_need_keys=frozenset({"sleep_tonight"}),
            known_attribute_keys=frozenset({"person.has_dog"}),
        )

        self.assertEqual((), violations)

    def test_rejects_unknown_need(self) -> None:
        result = InterpretationResult(
            need_key="does_not_exist", proposals=(), requires_confirmation=()
        )

        violations = validate_interpretation(
            result, known_need_keys=frozenset(), known_attribute_keys=frozenset()
        )

        self.assertIn("unknown_need_key", violations)

    def test_rejects_proposal_without_confirmation_requirement(self) -> None:
        result = InterpretationResult(
            need_key=None,
            proposals=(AttributeProposal(key="person.has_dog", value=True),),
            requires_confirmation=(),
        )

        violations = validate_interpretation(
            result,
            known_need_keys=frozenset(),
            known_attribute_keys=frozenset({"person.has_dog"}),
        )

        self.assertIn("proposal_without_confirmation_requirement", violations)

    def test_rejects_confirmation_key_without_matching_proposal(self) -> None:
        result = InterpretationResult(
            need_key=None,
            proposals=(),
            requires_confirmation=("person.has_dog",),
        )

        violations = validate_interpretation(
            result,
            known_need_keys=frozenset(),
            known_attribute_keys=frozenset({"person.has_dog"}),
        )

        self.assertIn("confirmation_without_proposal", violations)


class ValidateRenderedQuestionTest(unittest.TestCase):
    def test_rejects_changed_answer_options(self) -> None:
        attribute = AttributeDefinition(
            key="person.gender",
            value_type="enum",
            confirmation_required=True,
            skippable=True,
            options=(
                AttributeOption(value="finta", sort_order=1, localizations={}),
                AttributeOption(value="other", sort_order=2, localizations={}),
            ),
        )
        rendered = RenderedQuestion(
            text="Welche Zielgruppe?",
            help_text=None,
            unknown_label="?",
            decline_label="-",
            options=(QuestionOption(value="finta", label="FINTA"),),
        )

        violations = validate_rendered_question(rendered, attribute=attribute)

        self.assertIn("answer_options_changed", violations)

    def test_rejects_empty_text(self) -> None:
        attribute = AttributeDefinition(
            key="person.has_dog",
            value_type="boolean",
            confirmation_required=True,
            skippable=True,
        )
        rendered = RenderedQuestion(
            text="   ", help_text=None, unknown_label="?", decline_label="-"
        )

        violations = validate_rendered_question(rendered, attribute=attribute)

        self.assertIn("empty_question_text", violations)


class ValidateExplanationTest(unittest.TestCase):
    def _bundle(self) -> GroundingBundle:
        return GroundingBundle(
            offer_id="offer-1",
            facts=(GroundingFact(id="reason:need_matches", type="need_matches", value=True),),
            match_reasons=("need_matches",),
            uncertainties=(),
            allowed_next_actions=("call",),
        )

    def test_rejects_unknown_fact_reference(self) -> None:
        result = ExplanationResult(
            headline="Passt.",
            reasons=(ExplanationReason(text="x", supported_by=("does-not-exist",)),),
            clarification=None,
            next_action=None,
        )

        violations = validate_explanation(result, bundle=self._bundle(), locale="de")

        self.assertIn("unknown_fact_reference", violations)

    def test_rejects_disallowed_next_action(self) -> None:
        result = ExplanationResult(
            headline="Passt.",
            reasons=(ExplanationReason(text="x", supported_by=("reason:need_matches",)),),
            clarification=None,
            next_action="book_now",
        )

        violations = validate_explanation(result, bundle=self._bundle(), locale="de")

        self.assertIn("disallowed_next_action", violations)

    def test_rejects_forbidden_claim(self) -> None:
        result = ExplanationResult(
            headline="Der Platz ist reserviert für dich.",
            reasons=(ExplanationReason(text="x", supported_by=("reason:need_matches",)),),
            clarification=None,
            next_action=None,
        )

        violations = validate_explanation(result, bundle=self._bundle(), locale="de")

        self.assertIn("forbidden_claim_detected", violations)

    def test_accepts_well_formed_explanation(self) -> None:
        result = ExplanationResult(
            headline="Dieses Angebot könnte passen.",
            reasons=(ExplanationReason(text="x", supported_by=("reason:need_matches",)),),
            clarification=None,
            next_action="call",
        )

        violations = validate_explanation(result, bundle=self._bundle(), locale="de")

        self.assertEqual((), violations)


if __name__ == "__main__":
    unittest.main()
