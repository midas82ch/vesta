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
from vesta_api.domain.audit_models import AiOutcome, AiPort, NewAiAuditEntry
from vesta_api.domain.dialogue_catalog import (
    AttributeDefinition,
    NeedDefinition,
    QuestionDefinition,
)
from vesta_api.repositories.ai_audit_log import AiAuditLogRepository

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

    def __init__(
        self,
        *,
        enabled: bool,
        live: LiveGateway | None = None,
        provider: str = "",
        model: str = "",
        audit_log: AiAuditLogRepository | None = None,
    ) -> None:
        self._enabled = enabled
        self._live = live
        self._template = TemplateGateway()
        self._provider = provider
        self._model = model
        self._audit_log = audit_log

    @property
    def mode(self) -> str:
        return "live" if self._enabled and self._live is not None else "template"

    def _record_attempt(
        self,
        *,
        port: AiPort,
        session_id: str | None,
        outcome: AiOutcome,
        violations: tuple[str, ...] = (),
        error_detail: str | None = None,
    ) -> None:
        if self._audit_log is None:
            return
        try:
            exchange = getattr(self._live, "last_exchange", None)
            self._audit_log.record(
                NewAiAuditEntry(
                    port=port,
                    provider=self._provider,
                    model=self._model,
                    outcome=outcome,
                    request_text=exchange.request if exchange is not None else "",
                    response_text=exchange.response if exchange is not None else None,
                    session_id=session_id,
                    violations=violations,
                    error_detail=error_detail,
                )
            )
        except Exception:
            logger.exception(
                "ai_audit_record_failed: port=%s outcome=%s session_id=%s",
                port,
                outcome,
                session_id,
            )

    def interpret(
        self,
        *,
        free_text: str,
        locale: str,
        needs: tuple[NeedDefinition, ...],
        attributes: tuple[AttributeDefinition, ...],
        session_id: str | None = None,
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
                    self._record_attempt(
                        port="interpret", session_id=session_id, outcome="ai"
                    )
                    return result
                logger.warning("interpretation_validation_failed: %s", violations)
                self._record_attempt(
                    port="interpret",
                    session_id=session_id,
                    outcome="fallback_validation",
                    violations=violations,
                )
            except Exception as error:
                logger.exception("interpretation_live_call_failed")
                self._record_attempt(
                    port="interpret",
                    session_id=session_id,
                    outcome="fallback_error",
                    error_detail=f"{type(error).__name__}: {error}",
                )
        return self._template.interpret(
            free_text=free_text, locale=locale, needs=needs, attributes=attributes
        )

    def render_question(
        self,
        *,
        question: QuestionDefinition,
        attribute: AttributeDefinition,
        locale: str,
        session_id: str | None = None,
    ) -> RenderedQuestion:
        if self._enabled and self._live is not None:
            try:
                result = self._live.render_question(
                    question=question, attribute=attribute, locale=locale
                )
                violations = validate_rendered_question(result, attribute=attribute)
                if not violations:
                    self._record_attempt(
                        port="render_question", session_id=session_id, outcome="ai"
                    )
                    return result
                logger.warning("question_render_validation_failed: %s", violations)
                self._record_attempt(
                    port="render_question",
                    session_id=session_id,
                    outcome="fallback_validation",
                    violations=violations,
                )
            except Exception as error:
                logger.exception("question_render_live_call_failed")
                self._record_attempt(
                    port="render_question",
                    session_id=session_id,
                    outcome="fallback_error",
                    error_detail=f"{type(error).__name__}: {error}",
                )
        return self._template.render_question(
            question=question, attribute=attribute, locale=locale
        )

    def explain(
        self,
        *,
        bundle: GroundingBundle,
        locale: str,
        session_id: str | None = None,
    ) -> ExplanationResult:
        if self._enabled and self._live is not None:
            try:
                result = self._live.explain(bundle=bundle, locale=locale)
                violations = validate_explanation(result, bundle=bundle, locale=locale)
                if not violations:
                    self._record_attempt(
                        port="explain", session_id=session_id, outcome="ai"
                    )
                    return result
                logger.warning("explanation_validation_failed: %s", violations)
                self._record_attempt(
                    port="explain",
                    session_id=session_id,
                    outcome="fallback_validation",
                    violations=violations,
                )
            except Exception as error:
                logger.exception("explanation_live_call_failed")
                self._record_attempt(
                    port="explain",
                    session_id=session_id,
                    outcome="fallback_error",
                    error_detail=f"{type(error).__name__}: {error}",
                )
        return self._template.explain(bundle=bundle, locale=locale)
