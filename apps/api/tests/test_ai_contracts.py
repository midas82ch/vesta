import importlib.util
import json
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vesta_api.ai.fallback import TemplateGateway  # noqa: E402
from vesta_api.ai.validators import (  # noqa: E402
    validate_explanation,
    validate_interpretation,
)
from vesta_api.domain.ai_models import (  # noqa: E402
    AttributeProposal,
    GroundingBundle,
    GroundingFact,
    InterpretationResult,
)
from vesta_api.repositories.dialogue_catalog import (  # noqa: E402
    JsonDialogueCatalogRepository,
)

EVALS_DIR = Path(__file__).resolve().parents[1] / "evals"
CATALOG_PATH = (
    Path(__file__).resolve().parents[3] / "data" / "seed" / "dialogue_catalog.json"
)

ANTHROPIC_AVAILABLE = importlib.util.find_spec("anthropic") is not None
HAS_API_KEY = bool(os.environ.get("ANTHROPIC_API_KEY"))


def _load(name: str) -> dict:
    return json.loads((EVALS_DIR / name).read_text(encoding="utf-8"))


class FakeInterpretationGateway:
    """Deterministic stand-in for the live model, driven by each eval case's
    own expectations. It exists to exercise the validator and the
    proposed/confirmed invariant against realistic payload shapes - it does
    not test language understanding. Language understanding is only proven
    by the manual live smoke test below (gated on a real API key)."""

    def interpret_case(self, case: dict) -> InterpretationResult:
        proposals = tuple(
            AttributeProposal(key=key, value=True) for key in case["expected_attribute_keys"]
        )
        return InterpretationResult(
            need_key=case["expected_need_key"],
            proposals=proposals,
            requires_confirmation=tuple(p.key for p in proposals),
            ambiguities=("simulated_ambiguity",) if case.get("expects_ambiguity") else (),
            source="ai",
        )


class InterpretationEvalSetTest(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = JsonDialogueCatalogRepository(CATALOG_PATH)
        self.known_needs = frozenset(n.key for n in self.catalog.list_needs())
        self.known_attributes = frozenset(a.key for a in self.catalog.list_attributes())
        self.gateway = FakeInterpretationGateway()

    def test_every_case_produces_a_valid_contract(self) -> None:
        cases = _load("interpretation_cases.json")["cases"]
        self.assertGreaterEqual(len(cases), 10)

        for case in cases:
            with self.subTest(case=case["id"]):
                result = self.gateway.interpret_case(case)
                violations = validate_interpretation(
                    result,
                    known_need_keys=self.known_needs,
                    known_attribute_keys=self.known_attributes,
                )
                self.assertEqual((), violations, f"{case['id']}: {violations}")

    def test_ambiguous_cases_never_claim_a_confident_need(self) -> None:
        cases = _load("interpretation_cases.json")["cases"]
        for case in cases:
            if case.get("expects_ambiguity"):
                with self.subTest(case=case["id"]):
                    result = self.gateway.interpret_case(case)
                    self.assertTrue(result.ambiguities)


class ExplanationEvalSetTest(unittest.TestCase):
    def setUp(self) -> None:
        self.gateway = TemplateGateway()

    def _bundle(self, case: dict) -> GroundingBundle:
        payload = case["bundle"]
        return GroundingBundle(
            offer_id=payload["offer_id"],
            facts=tuple(
                GroundingFact(id=f["id"], type=f["type"], value=f["value"])
                for f in payload["facts"]
            ),
            match_reasons=tuple(payload["match_reasons"]),
            uncertainties=tuple(payload["uncertainties"]),
            allowed_next_actions=tuple(payload["allowed_next_actions"]),
        )

    def test_every_case_produces_a_grounded_explanation(self) -> None:
        cases = _load("explanation_cases.json")["cases"]
        self.assertGreaterEqual(len(cases), 6)

        for case in cases:
            with self.subTest(case=case["id"]):
                bundle = self._bundle(case)
                result = self.gateway.explain(bundle=bundle, locale=case["locale"])
                violations = validate_explanation(result, bundle=bundle, locale=case["locale"])
                self.assertEqual((), violations, f"{case['id']}: {violations}")


@unittest.skipUnless(
    ANTHROPIC_AVAILABLE and HAS_API_KEY,
    "manual smoke test: requires `pip install -e '.[ai]'` and ANTHROPIC_API_KEY",
)
class LiveSmokeTest(unittest.TestCase):
    def test_live_explanation_passes_validation(self) -> None:
        from vesta_api.ai.live_gateway import AnthropicGateway

        gateway = AnthropicGateway(
            api_key=os.environ["ANTHROPIC_API_KEY"], model="claude-haiku-4-5"
        )
        bundle = GroundingBundle(
            offer_id="offer-1",
            facts=(GroundingFact(id="reason:need_matches", type="need_matches", value=True),),
            match_reasons=("need_matches",),
            uncertainties=(),
            allowed_next_actions=(),
        )

        result = gateway.explain(bundle=bundle, locale="de")

        violations = validate_explanation(result, bundle=bundle, locale="de")
        self.assertEqual((), violations)


if __name__ == "__main__":
    unittest.main()
