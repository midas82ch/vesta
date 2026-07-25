from typing import Protocol

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


class InterpretationPort(Protocol):
    """Translates free text into a confirmable proposal. Never returns a
    confirmed value — every proposed field requires explicit user
    confirmation before it may enter a MatchQuery (see
    domain.dialogue_models.AttributeState)."""

    def interpret(
        self,
        *,
        free_text: str,
        locale: str,
        needs: tuple[NeedDefinition, ...],
        attributes: tuple[AttributeDefinition, ...],
    ) -> InterpretationResult: ...


class QuestionRendererPort(Protocol):
    """Rephrases an already-selected, catalog-defined question. May not
    change its meaning, answer options, or ask about anything not in
    ``question``/``attribute``."""

    def render_question(
        self,
        *,
        question: QuestionDefinition,
        attribute: AttributeDefinition,
        locale: str,
    ) -> RenderedQuestion: ...


class ResultExplainerPort(Protocol):
    """Simplifies an already-computed, source-backed result. May only state
    what ``bundle`` supports; every claim must be traceable to a fact id."""

    def explain(self, *, bundle: GroundingBundle, locale: str) -> ExplanationResult: ...
