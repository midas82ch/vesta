from vesta_api.domain.ai_models import (
    ExplanationResult,
    GroundingBundle,
    InterpretationResult,
    RenderedQuestion,
)
from vesta_api.domain.dialogue_catalog import AttributeDefinition

# Starter list, seeded from the concept discussion. Expand from the eval set
# in Etappe 4 as real over-claiming phrasings are observed per locale.
_FORBIDDEN_PHRASES: dict[str, tuple[str, ...]] = {
    "de": ("ist reserviert", "garantiert", "sicher einen platz", "ist zugesichert"),
    "fr": ("est réservé", "garanti", "une place assurée"),
    "en": ("is reserved", "guaranteed", "a place is assured"),
    "es": ("está reservada", "garantizado", "plaza asegurada", "plaza garantizada"),
    "pt": ("está reservado", "garantido", "lugar assegurado", "lugar garantido"),
    "ary": ("محجوزة", "مضمون", "البلاصة مضمونة", "بلاصة أكيدة"),
}


def validate_interpretation(
    result: InterpretationResult,
    *,
    known_need_keys: frozenset[str],
    known_attribute_keys: frozenset[str],
) -> tuple[str, ...]:
    violations: list[str] = []
    if result.need_key is not None and result.need_key not in known_need_keys:
        violations.append("unknown_need_key")

    proposal_keys = {proposal.key for proposal in result.proposals}
    for key in proposal_keys:
        if key not in known_attribute_keys:
            violations.append("unknown_attribute_key")

    for key in result.requires_confirmation:
        if key not in proposal_keys:
            violations.append("confirmation_without_proposal")

    if result.proposals and not result.requires_confirmation:
        violations.append("proposal_without_confirmation_requirement")

    return tuple(violations)


def validate_rendered_question(
    result: RenderedQuestion, *, attribute: AttributeDefinition
) -> tuple[str, ...]:
    violations: list[str] = []
    if not result.text.strip():
        violations.append("empty_question_text")

    expected_values = {option.value for option in attribute.options}
    actual_values = {option.value for option in result.options}
    if expected_values != actual_values:
        violations.append("answer_options_changed")

    return tuple(violations)


def validate_explanation(
    result: ExplanationResult, *, bundle: GroundingBundle, locale: str
) -> tuple[str, ...]:
    violations: list[str] = []
    fact_ids = {fact.id for fact in bundle.facts}

    for reason in result.reasons:
        if not reason.supported_by:
            violations.append("unsupported_reason")
        if any(fact_id not in fact_ids for fact_id in reason.supported_by):
            violations.append("unknown_fact_reference")

    if result.clarification is not None:
        if any(
            fact_id not in fact_ids for fact_id in result.clarification.supported_by
        ):
            violations.append("unknown_fact_reference")

    if (
        result.next_action is not None
        and result.next_action not in bundle.allowed_next_actions
    ):
        violations.append("disallowed_next_action")

    phrases = _FORBIDDEN_PHRASES.get(locale, _FORBIDDEN_PHRASES["de"])
    haystack = result.headline.lower()
    for reason in result.reasons:
        haystack += " " + reason.text.lower()
    if result.clarification is not None:
        haystack += " " + result.clarification.text.lower()
    for phrase in phrases:
        if phrase in haystack:
            violations.append("forbidden_claim_detected")

    return tuple(violations)
