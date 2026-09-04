import json
import sys
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextvars import ContextVar
from pathlib import Path
from threading import Barrier
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vesta_api.ai.live_gateway import (  # noqa: E402
    _EXPLANATION_SCHEMA,
    _INTERPRETATION_SCHEMA,
    _INTERPRETATION_SYSTEM,
    _QUESTION_SCHEMA,
    _bundle_payload,
    _describe_catalog,
)
from vesta_api.ai.openai_gateway import OpenAiGateway  # noqa: E402
from vesta_api.domain.ai_models import GroundingBundle, GroundingFact  # noqa: E402
from vesta_api.domain.audit_models import AiExchange  # noqa: E402
from vesta_api.domain.dialogue_catalog import (  # noqa: E402
    AttributeDefinition,
    AttributeOption,
    NeedDefinition,
    QuestionDefinition,
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


class _ConcurrentFakeCompletions:
    def __init__(self, barrier: Barrier) -> None:
        self._barrier = barrier

    def create(self, **kwargs: object) -> SimpleNamespace:
        messages = kwargs["messages"]
        assert isinstance(messages, list)
        user_text = messages[1]["content"]
        self._barrier.wait()
        response_text = json.dumps({"user": user_text})
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=response_text))]
        )


class OpenAiExchangeContextTest(unittest.TestCase):
    def test_parallel_calls_keep_request_and_response_in_their_own_context(self) -> None:
        gateway = object.__new__(OpenAiGateway)
        gateway._client = SimpleNamespace(  # type: ignore[attr-defined]
            chat=SimpleNamespace(completions=_ConcurrentFakeCompletions(Barrier(2)))
        )
        gateway._model = "test-model"  # type: ignore[attr-defined]
        gateway._last_exchange = ContextVar(  # type: ignore[attr-defined]
            "test_openai_last_exchange",
            default=None,
        )

        def call(label: str) -> AiExchange:
            gateway._create(  # type: ignore[attr-defined]
                system="system",
                user=label,
                schema_name="test",
                schema={"type": "object"},
            )
            exchange = gateway.last_exchange
            assert exchange is not None
            return exchange

        with ThreadPoolExecutor(max_workers=2) as executor:
            first = executor.submit(call, "alpha")
            second = executor.submit(call, "beta")
            exchanges = (first.result(), second.result())

        by_label = {
            "alpha": next(
                exchange for exchange in exchanges if "[user]\nalpha" in exchange.request
            ),
            "beta": next(exchange for exchange in exchanges if "[user]\nbeta" in exchange.request),
        }
        self.assertIn("alpha", by_label["alpha"].response or "")
        self.assertNotIn("beta", by_label["alpha"].response or "")
        self.assertIn("beta", by_label["beta"].response or "")
        self.assertNotIn("alpha", by_label["beta"].response or "")


class QuestionRenderingContractTest(unittest.TestCase):
    def test_ai_only_changes_text_and_catalog_keeps_controls(self) -> None:
        gateway = object.__new__(OpenAiGateway)
        gateway._create = lambda **_kwargs: {  # type: ignore[attr-defined,method-assign]
            "text": "AI question",
            "help_text": "AI help",
        }
        attribute = AttributeDefinition(
            key="person.is_adult",
            value_type="boolean",
            confirmation_required=True,
            skippable=True,
            options=(
                AttributeOption(
                    value="true",
                    sort_order=1,
                    localizations={"de": {"label": "Ja"}},
                ),
                AttributeOption(
                    value="false",
                    sort_order=2,
                    localizations={"de": {"label": "Nein"}},
                ),
            ),
        )
        question = QuestionDefinition(
            key="access.is_adult",
            attribute_key="person.is_adult",
            answer_type="yes_no_unknown",
            priority=40,
            ai_rephrasing_allowed=True,
            localizations={
                "de": {
                    "canonical_text": "18 oder älter?",
                    "help_text": "Zugangsregel",
                    "unknown_label": "Weiss ich nicht",
                    "decline_label": "Keine Angabe",
                }
            },
        )

        rendered = gateway.render_question(
            question=question,
            attribute=attribute,
            locale="de",
        )

        self.assertEqual("AI question", rendered.text)
        self.assertEqual(("true", "false"), tuple(option.value for option in rendered.options))
        self.assertEqual("Weiss ich nicht", rendered.unknown_label)
        self.assertEqual("Keine Angabe", rendered.decline_label)


if __name__ == "__main__":
    unittest.main()
