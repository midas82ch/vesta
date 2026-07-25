import logging
from typing import Protocol

from vesta_api.ai.fallback import TemplateGateway
from vesta_api.ai.ports import InterpretationPort, QuestionRendererPort, ResultExplainerPort
from vesta_api.ai.validators import (
    validate_explanation,
    validate_interpretation,
    validate_rendered_question,
)
from vesta_api.domain.ai_models import (
    ExplanationResult,
    GroundingBundle,
    InterpretationResult,
    RenderedQuestion,
)
from vesta_api.domain.dialogue_catalog import (
    AttributeDefinition,
    NeedDefinition,
    QuestionDefinition,
)

logger = logging.getLogger(__name__)


class LiveGateway(InterpretationPort, QuestionRendererPort, ResultExplainerPort, Protocol):
    """Structural type for a live AI backend implementing all three ports."""


class AiGateway:
    """Single entry point the rest of the API talks to.

    Chooses between a live backend and the template fallback, and always
    validates a live result before trusting it. Any exception or contract
    violation from the live path falls back to the template - the pipeline
    never surfaces an unvalidated AI output (ADR 0002).
    """

    def __init__(self, *, enabled: bool, live: LiveGateway | None = None) -> None:
        self._enabled = enabled
        self._live = live
        self._template = TemplateGateway()

    @property
    def mode(self) -> str:
        return "live" if self._enabled and self._live is not None else "template"

    def interpret(
        self,
        *,
        free_text: str,
        locale: str,
        needs: tuple[NeedDefinition, ...],
        attributes: tuple[AttributeDefinition, ...],
    ) -> InterpretationResult:
        if self._enabled and self._live is not None:
            try:
                result = self._live.interpret(
                    free_text=free_text, locale=locale, needs=needs, attributes=attributes
                )
                violations = validate_interpretation(
                    result,
                    known_need_keys=frozenset(need.key for need in needs),
                    known_attribute_keys=frozenset(
                        attribute.key for attribute in attributes
                    ),
                )
                if not violations:
                    return result
                logger.warning("interpretation_validation_failed: %s", violations)
            except Exception:
                logger.exception("interpretation_live_call_failed")
        return self._template.interpret(
            free_text=free_text, locale=locale, needs=needs, attributes=attributes
        )

    def render_question(
        self,
        *,
        question: QuestionDefinition,
        attribute: AttributeDefinition,
        locale: str,
    ) -> RenderedQuestion:
        if self._enabled and self._live is not None:
            try:
                result = self._live.render_question(
                    question=question, attribute=attribute, locale=locale
                )
                violations = validate_rendered_question(result, attribute=attribute)
                if not violations:
                    return result
                logger.warning("question_render_validation_failed: %s", violations)
            except Exception:
                logger.exception("question_render_live_call_failed")
        return self._template.render_question(
            question=question, attribute=attribute, locale=locale
        )

    def explain(self, *, bundle: GroundingBundle, locale: str) -> ExplanationResult:
        if self._enabled and self._live is not None:
            try:
                result = self._live.explain(bundle=bundle, locale=locale)
                violations = validate_explanation(result, bundle=bundle, locale=locale)
                if not violations:
                    return result
                logger.warning("explanation_validation_failed: %s", violations)
            except Exception:
                logger.exception("explanation_live_call_failed")
        return self._template.explain(bundle=bundle, locale=locale)
