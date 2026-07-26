import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vesta_api.ai.gateway import AiGateway  # noqa: E402
from vesta_api.domain.ai_models import (  # noqa: E402
    ExplanationReason,
    ExplanationResult,
    GroundingBundle,
    GroundingFact,
)


def _bundle() -> GroundingBundle:
    return GroundingBundle(
        offer_id="offer-1",
        facts=(GroundingFact(id="reason:need_matches", type="need_matches", value=True),),
        match_reasons=("need_matches",),
        uncertainties=(),
        allowed_next_actions=("call",),
    )


class RaisingLive:
    def explain(self, *, bundle: GroundingBundle, locale: str) -> ExplanationResult:
        raise RuntimeError("model_unavailable")


class InvalidLive:
    def explain(self, *, bundle: GroundingBundle, locale: str) -> ExplanationResult:
        return ExplanationResult(
            headline="Der Platz ist garantiert.",
            reasons=(ExplanationReason(text="x", supported_by=("reason:need_matches",)),),
            clarification=None,
            next_action=None,
            source="ai",
        )


class ValidLive:
    def explain(self, *, bundle: GroundingBundle, locale: str) -> ExplanationResult:
        return ExplanationResult(
            headline="Dieses Angebot könnte passen.",
            reasons=(ExplanationReason(text="Grund", supported_by=("reason:need_matches",)),),
            clarification=None,
            next_action="call",
            source="ai",
        )


class FailingAuditLog:
    def record(self, entry: object) -> None:
        del entry
        raise RuntimeError("audit_database_unavailable")


class AiGatewayTest(unittest.TestCase):
    def test_disabled_gateway_uses_template_even_with_live_configured(self) -> None:
        gateway = AiGateway(enabled=False, live=ValidLive())

        self.assertEqual("template", gateway.mode)
        result = gateway.explain(bundle=_bundle(), locale="de")
        self.assertEqual("template", result.source)

    def test_live_exception_falls_back_to_template(self) -> None:
        gateway = AiGateway(enabled=True, live=RaisingLive())

        result = gateway.explain(bundle=_bundle(), locale="de")

        self.assertEqual("template", result.source)

    def test_live_contract_violation_falls_back_to_template(self) -> None:
        gateway = AiGateway(enabled=True, live=InvalidLive())

        result = gateway.explain(bundle=_bundle(), locale="de")

        self.assertEqual("template", result.source)

    def test_valid_live_result_is_used(self) -> None:
        gateway = AiGateway(enabled=True, live=ValidLive())

        self.assertEqual("live", gateway.mode)
        result = gateway.explain(bundle=_bundle(), locale="de")
        self.assertEqual("ai", result.source)

    def test_audit_failure_does_not_replace_valid_live_result(self) -> None:
        gateway = AiGateway(
            enabled=True,
            live=ValidLive(),
            provider="openai",
            model="test-model",
            audit_log=FailingAuditLog(),  # type: ignore[arg-type]
        )

        result = gateway.explain(bundle=_bundle(), locale="de")

        self.assertEqual("ai", result.source)

    def test_audit_failure_does_not_break_validation_fallback(self) -> None:
        gateway = AiGateway(
            enabled=True,
            live=InvalidLive(),
            provider="openai",
            model="test-model",
            audit_log=FailingAuditLog(),  # type: ignore[arg-type]
        )

        result = gateway.explain(bundle=_bundle(), locale="de")

        self.assertEqual("template", result.source)

    def test_audit_failure_does_not_break_error_fallback(self) -> None:
        gateway = AiGateway(
            enabled=True,
            live=RaisingLive(),
            provider="openai",
            model="test-model",
            audit_log=FailingAuditLog(),  # type: ignore[arg-type]
        )

        result = gateway.explain(bundle=_bundle(), locale="de")

        self.assertEqual("template", result.source)


if __name__ == "__main__":
    unittest.main()
