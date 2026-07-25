import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vesta_api.ai.live_gateway import (  # noqa: E402
    _EXPLANATION_SCHEMA,
    _INTERPRETATION_SCHEMA,
    _INTERPRETATION_SYSTEM,
    _QUESTION_SCHEMA,
    _bundle_payload,
    _describe_catalog,
)
from vesta_api.domain.ai_models import GroundingBundle, GroundingFact  # noqa: E402
from vesta_api.domain.dialogue_catalog import (  # noqa: E402
    AttributeDefinition,
    AttributeOption,
    NeedDefinition,
)


class DescribeCatalogTest(unittest.TestCase):
    def test_lists_need_and_attribute_keys_with_enum_values(self) -> None:
        needs = (NeedDefinition(key="sleep_tonight", sort_order=1, localizations={}),)
        attributes = (
            AttributeDefinition(
                key="person.gender",
                value_type="enum",
                confirmation_required=True,
                skippable=True,
                options=(
                    AttributeOption(value="finta", sort_order=1, localizations={}),
                    AttributeOption(value="other", sort_order=2, localizations={}),
                ),
            ),
        )

        description = _describe_catalog(needs, attributes)

        self.assertIn("sleep_tonight", description)
        self.assertIn("person.gender", description)
        self.assertIn("finta", description)
        self.assertIn("other", description)


class BundlePayloadTest(unittest.TestCase):
    def test_serializes_all_bundle_fields(self) -> None:
        bundle = GroundingBundle(
            offer_id="offer-1",
            facts=(GroundingFact(id="reason:need_matches", type="need_matches", value=True),),
            match_reasons=("need_matches",),
            uncertainties=(),
            allowed_next_actions=("call",),
        )

        payload = _bundle_payload(bundle)

        self.assertEqual(1, len(payload["facts"]))
        self.assertEqual(["need_matches"], payload["match_reasons"])
        self.assertEqual(["call"], payload["allowed_next_actions"])
        self.assertIn("place_is_reserved", payload["forbidden_claims"])


class SchemaShapeTest(unittest.TestCase):
    def test_schemas_are_closed_objects(self) -> None:
        for schema in (_INTERPRETATION_SCHEMA, _QUESTION_SCHEMA, _EXPLANATION_SCHEMA):
            self.assertEqual("object", schema["type"])
            self.assertFalse(schema["additionalProperties"])
            self.assertEqual(set(schema["properties"]), set(schema["required"]))


class InterpretationPromptTest(unittest.TestCase):
    def test_separates_need_from_attribute_confirmations(self) -> None:
        self.assertIn("need_key gehoert nie in requires_confirmation", _INTERPRETATION_SYSTEM)
        self.assertIn("exakt die Schluessel aus proposals", _INTERPRETATION_SYSTEM)
        self.assertIn("ausdruecklich genannt", _INTERPRETATION_SYSTEM)


if __name__ == "__main__":
    unittest.main()
