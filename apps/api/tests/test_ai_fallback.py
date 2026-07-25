import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vesta_api.ai.fallback import TemplateGateway  # noqa: E402
from vesta_api.domain.ai_models import GroundingBundle, GroundingFact  # noqa: E402
from vesta_api.repositories.dialogue_catalog import (  # noqa: E402
    JsonDialogueCatalogRepository,
)

CATALOG_PATH = (
    Path(__file__).resolve().parents[3] / "data" / "seed" / "dialogue_catalog.json"
)


class TemplateGatewayTest(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = JsonDialogueCatalogRepository(CATALOG_PATH)
        self.gateway = TemplateGateway()

    def test_interpret_never_fabricates_proposals(self) -> None:
        result = self.gateway.interpret(
            free_text="Ich brauche heute einen Schlafplatz mit meinem Hund",
            locale="de",
            needs=self.catalog.list_needs(),
            attributes=self.catalog.list_attributes(),
        )

        self.assertEqual((), result.proposals)
        self.assertIn("free_text_interpretation_unavailable", result.ambiguities)
        self.assertEqual("template", result.source)

    def test_render_question_uses_catalog_text_and_options(self) -> None:
        question = next(
            q for q in self.catalog.list_questions() if q.key == "sleep.gender"
        )
        attribute = self.catalog.get_attribute("person.gender")
        assert attribute is not None

        rendered = self.gateway.render_question(
            question=question, attribute=attribute, locale="fr"
        )

        self.assertEqual("Quel groupe cible vous correspond ?", rendered.text)
        self.assertEqual({"finta", "other"}, {o.value for o in rendered.options})
        finta = next(o for o in rendered.options if o.value == "finta")
        self.assertEqual("Femme / FINTA", finta.label)
        self.assertEqual("template", rendered.source)

    def test_render_question_falls_back_to_german_for_unknown_locale(self) -> None:
        question = next(
            q for q in self.catalog.list_questions() if q.key == "sleep.has_dog"
        )
        attribute = self.catalog.get_attribute("person.has_dog")
        assert attribute is not None

        rendered = self.gateway.render_question(
            question=question, attribute=attribute, locale="it"
        )

        self.assertEqual("Führen Sie ein Tier mit sich?", rendered.text)

    def test_explain_only_states_what_the_bundle_supports(self) -> None:
        bundle = GroundingBundle(
            offer_id="offer-1",
            facts=(
                GroundingFact(id="reason:need_matches", type="need_matches", value=True),
                GroundingFact(
                    id="uncertainty:availability_requires_contact",
                    type="availability_requires_contact",
                    value=True,
                ),
            ),
            match_reasons=("need_matches",),
            uncertainties=("availability_requires_contact",),
            allowed_next_actions=("call",),
        )

        result = self.gateway.explain(bundle=bundle, locale="en")

        self.assertEqual(1, len(result.reasons))
        self.assertEqual(("reason:need_matches",), result.reasons[0].supported_by)
        assert result.clarification is not None
        self.assertEqual(
            ("uncertainty:availability_requires_contact",),
            result.clarification.supported_by,
        )
        self.assertEqual("call", result.next_action)
        self.assertEqual("template", result.source)


if __name__ == "__main__":
    unittest.main()
