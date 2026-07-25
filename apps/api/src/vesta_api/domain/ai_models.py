from dataclasses import dataclass, field
from typing import Literal

Source = Literal["ai", "template"]


@dataclass(frozen=True)
class AttributeProposal:
    key: str
    value: object | None
    confidence: Literal["clear", "unclear"] = "clear"


@dataclass(frozen=True)
class InterpretationResult:
    need_key: str | None
    proposals: tuple[AttributeProposal, ...]
    requires_confirmation: tuple[str, ...]
    ambiguities: tuple[str, ...] = field(default_factory=tuple)
    source: Source = "template"


@dataclass(frozen=True)
class QuestionOption:
    value: str
    label: str


@dataclass(frozen=True)
class RenderedQuestion:
    text: str
    help_text: str | None
    unknown_label: str
    decline_label: str
    options: tuple[QuestionOption, ...] = field(default_factory=tuple)
    source: Source = "template"


@dataclass(frozen=True)
class GroundingFact:
    id: str
    type: str
    value: object


@dataclass(frozen=True)
class GroundingBundle:
    offer_id: str
    facts: tuple[GroundingFact, ...]
    match_reasons: tuple[str, ...]
    uncertainties: tuple[str, ...]
    allowed_next_actions: tuple[str, ...]
    forbidden_claims: tuple[str, ...] = field(
        default_factory=lambda: (
            "place_is_reserved",
            "admission_is_guaranteed",
        )
    )


@dataclass(frozen=True)
class ExplanationReason:
    text: str
    supported_by: tuple[str, ...]


@dataclass(frozen=True)
class ExplanationResult:
    headline: str
    reasons: tuple[ExplanationReason, ...]
    clarification: ExplanationReason | None
    next_action: str | None
    source: Source = "template"
