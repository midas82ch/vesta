import json
import logging

from vesta_api.domain.ai_models import (
    AttributeProposal,
    ExplanationReason,
    ExplanationResult,
    GroundingBundle,
    InterpretationResult,
    QuestionOption,
    RenderedQuestion,
)
from vesta_api.domain.dialogue_catalog import (
    AttributeDefinition,
    NeedDefinition,
    QuestionDefinition,
)

logger = logging.getLogger(__name__)

_INTERPRETATION_SCHEMA = {
    "type": "object",
    "properties": {
        "need_key": {"type": ["string", "null"]},
        "proposals": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                    "value": {"type": ["boolean", "integer", "string"]},
                    "confidence": {"type": "string", "enum": ["clear", "unclear"]},
                },
                "required": ["key", "value", "confidence"],
                "additionalProperties": False,
            },
        },
        "requires_confirmation": {"type": "array", "items": {"type": "string"}},
        "ambiguities": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["need_key", "proposals", "requires_confirmation", "ambiguities"],
    "additionalProperties": False,
}

_QUESTION_SCHEMA = {
    "type": "object",
    "properties": {
        "text": {"type": "string"},
        "help_text": {"type": ["string", "null"]},
        "unknown_label": {"type": "string"},
        "decline_label": {"type": "string"},
        "options": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "value": {"type": "string"},
                    "label": {"type": "string"},
                },
                "required": ["value", "label"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["text", "help_text", "unknown_label", "decline_label", "options"],
    "additionalProperties": False,
}

_EXPLANATION_REASON_SCHEMA = {
    "type": "object",
    "properties": {
        "text": {"type": "string"},
        "supported_by": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["text", "supported_by"],
    "additionalProperties": False,
}

_EXPLANATION_SCHEMA = {
    "type": "object",
    "properties": {
        "headline": {"type": "string"},
        "reasons": {"type": "array", "items": _EXPLANATION_REASON_SCHEMA},
        "clarification": {"anyOf": [{"type": "null"}, _EXPLANATION_REASON_SCHEMA]},
        "next_action": {"type": ["string", "null"]},
    },
    "required": ["headline", "reasons", "clarification", "next_action"],
    "additionalProperties": False,
}

_INTERPRETATION_SYSTEM = (
    "Du ordnest einen Freitext ausschliesslich den vorgegebenen Bedarfs- und "
    "Merkmalsschluesseln zu. need_key darf nur ein Bedarfschluessel oder null "
    "sein. requires_confirmation enthaelt ausschliesslich und exakt die "
    "Schluessel aus proposals; need_key gehoert nie in requires_confirmation. "
    "Erzeuge proposals nur fuer Merkmale, deren Wert im Freitext ausdruecklich "
    "genannt ist; nicht erwaehnte Merkmale bleiben weg. Kein Raten. Jeder "
    "proposal-Schluessel muss in requires_confirmation stehen. Verwende keine "
    "unbekannten Schluessel. Bei Mehrdeutigkeit ambiguities statt raten."
)

_QUESTION_SYSTEM = (
    "Du formulierst eine bereits fachlich freigegebene Frage des Vesta-Sozial-Lotsen "
    "verstaendlicher. Bedeutung und Antwortoptionen duerfen sich nicht aendern. "
    "Frage nicht nach zusaetzlichen Informationen. Antworte in der angegebenen Sprache."
)

_EXPLANATION_SYSTEM = (
    "Du erklaerst ein bereits berechnetes Vermittlungsergebnis des Vesta-Sozial-Lotsen "
    "anhand eines begrenzten Faktenpakets. Du darfst ausschliesslich Aussagen treffen, "
    "die durch eine Fakten-ID im Paket belegt sind - jede reasons/clarification-Aussage "
    "braucht mindestens eine unterstuetzende Fakten-ID. next_action muss entweder null "
    "sein oder eine der erlaubten Aktionen. Behaupte niemals einen reservierten oder "
    "garantierten Platz."
)


def _describe_catalog(
    needs: tuple[NeedDefinition, ...], attributes: tuple[AttributeDefinition, ...]
) -> str:
    need_lines = [f"- {need.key}" for need in needs]
    attribute_lines = []
    for attribute in attributes:
        options = (
            f" (Werte: {', '.join(o.value for o in attribute.options)})"
            if attribute.options
            else ""
        )
        attribute_lines.append(f"- {attribute.key} [{attribute.value_type}]{options}")
    return "Bedarfe:\n" + "\n".join(need_lines) + "\n\nMerkmale:\n" + "\n".join(
        attribute_lines
    )


def _bundle_payload(bundle: GroundingBundle) -> dict[str, object]:
    return {
        "facts": [
            {"id": fact.id, "type": fact.type, "value": fact.value} for fact in bundle.facts
        ],
        "match_reasons": list(bundle.match_reasons),
        "uncertainties": list(bundle.uncertainties),
        "allowed_next_actions": list(bundle.allowed_next_actions),
        "forbidden_claims": list(bundle.forbidden_claims),
    }


class AnthropicGateway:
    """Live implementation of the three AI ports via the Anthropic Messages API.

    Every call requests schema-constrained JSON output
    (``output_config.format``) so the response always parses; ``AiGateway``
    still re-validates the *content* against the domain rules (grounding,
    unchanged answer options, confirmation requirement) before trusting it.
    """

    def __init__(self, *, api_key: str, model: str) -> None:
        import anthropic

        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def interpret(
        self,
        *,
        free_text: str,
        locale: str,
        needs: tuple[NeedDefinition, ...],
        attributes: tuple[AttributeDefinition, ...],
    ) -> InterpretationResult:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=_INTERPRETATION_SYSTEM,
            output_config={
                "format": {"type": "json_schema", "schema": _INTERPRETATION_SCHEMA}
            },
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Sprache: {locale}\n\n"
                        f"{_describe_catalog(needs, attributes)}\n\n"
                        f"Freitext der Person: {free_text}"
                    ),
                }
            ],
        )
        payload = json.loads(response.content[0].text)
        return InterpretationResult(
            need_key=payload["need_key"],
            proposals=tuple(
                AttributeProposal(key=p["key"], value=p["value"], confidence=p["confidence"])
                for p in payload["proposals"]
            ),
            requires_confirmation=tuple(payload["requires_confirmation"]),
            ambiguities=tuple(payload["ambiguities"]),
            source="ai",
        )

    def render_question(
        self,
        *,
        question: QuestionDefinition,
        attribute: AttributeDefinition,
        locale: str,
    ) -> RenderedQuestion:
        canonical = question.localizations.get(locale) or question.localizations["de"]
        allowed_values = (
            ", ".join(o.value for o in attribute.options)
            if attribute.options
            else "ja / nein / weiss nicht"
        )
        response = self._client.messages.create(
            model=self._model,
            max_tokens=512,
            system=_QUESTION_SYSTEM,
            output_config={"format": {"type": "json_schema", "schema": _QUESTION_SCHEMA}},
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Sprache: {locale}\n"
                        f"Kanonischer Text: {canonical['canonical_text']}\n"
                        f"Hilfetext: {canonical.get('help_text', '')}\n"
                        f"Erlaubte Antwortoptionen: {allowed_values}\n\n"
                        "Formuliere nur die Frage verstaendlicher."
                    ),
                }
            ],
        )
        payload = json.loads(response.content[0].text)
        return RenderedQuestion(
            text=payload["text"],
            help_text=payload["help_text"],
            unknown_label=payload["unknown_label"],
            decline_label=payload["decline_label"],
            options=tuple(
                QuestionOption(value=o["value"], label=o["label"]) for o in payload["options"]
            ),
            source="ai",
        )

    def explain(self, *, bundle: GroundingBundle, locale: str) -> ExplanationResult:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=768,
            system=_EXPLANATION_SYSTEM,
            output_config={"format": {"type": "json_schema", "schema": _EXPLANATION_SCHEMA}},
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Sprache: {locale}\n\n"
                        f"Faktenpaket:\n{json.dumps(_bundle_payload(bundle), ensure_ascii=False)}"
                    ),
                }
            ],
        )
        payload = json.loads(response.content[0].text)
        clarification_payload = payload["clarification"]
        clarification = (
            ExplanationReason(
                text=clarification_payload["text"],
                supported_by=tuple(clarification_payload["supported_by"]),
            )
            if clarification_payload is not None
            else None
        )
        return ExplanationResult(
            headline=payload["headline"],
            reasons=tuple(
                ExplanationReason(text=r["text"], supported_by=tuple(r["supported_by"]))
                for r in payload["reasons"]
            ),
            clarification=clarification,
            next_action=payload["next_action"],
            source="ai",
        )
