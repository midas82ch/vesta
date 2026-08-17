import json
from contextvars import ContextVar

from vesta_api.ai.live_gateway import (
    _EXPLANATION_SCHEMA,
    _EXPLANATION_SYSTEM,
    _INTERPRETATION_SCHEMA,
    _INTERPRETATION_SYSTEM,
    _QUESTION_SCHEMA,
    _QUESTION_SYSTEM,
    _bundle_payload,
    _describe_catalog,
)
from vesta_api.ai.locales import ai_locale_name
from vesta_api.domain.ai_models import (
    AttributeProposal,
    ExplanationReason,
    ExplanationResult,
    GroundingBundle,
    InterpretationResult,
    QuestionOption,
    RenderedQuestion,
)
from vesta_api.domain.audit_models import AiExchange
from vesta_api.domain.dialogue_catalog import (
    AttributeDefinition,
    NeedDefinition,
    QuestionDefinition,
)


def _json_schema_format(name: str, schema: dict) -> dict:
    return {
        "type": "json_schema",
        "json_schema": {"name": name, "schema": schema, "strict": True},
    }


class OpenAiGateway:
    """Live implementation of the three AI ports via the OpenAI Chat
    Completions API (structured outputs). Reuses the exact same JSON
    schemas and system prompts as ``AnthropicGateway`` - the ports are
    provider-agnostic by design, so swapping the live backend never touches
    ``AiGateway``, the validators, or anything upstream of this file.
    """

    def __init__(self, *, api_key: str, model: str) -> None:
        import openai

        self._client = openai.OpenAI(api_key=api_key)
        self._model = model
        self._last_exchange: ContextVar[AiExchange | None] = ContextVar(
            f"openai_last_exchange_{id(self)}",
            default=None,
        )

    @property
    def last_exchange(self) -> AiExchange | None:
        return self._last_exchange.get()

    def _create(self, *, system: str, user: str, schema_name: str, schema: dict) -> dict:
        request_text = f"[system]\n{system}\n\n[user]\n{user}"
        self._last_exchange.set(AiExchange(request=request_text))
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format=_json_schema_format(schema_name, schema),
        )
        response_text = response.choices[0].message.content
        self._last_exchange.set(AiExchange(request=request_text, response=response_text))
        return json.loads(response_text)

    def interpret(
        self,
        *,
        free_text: str,
        locale: str,
        needs: tuple[NeedDefinition, ...],
        attributes: tuple[AttributeDefinition, ...],
    ) -> InterpretationResult:
        payload = self._create(
            system=_INTERPRETATION_SYSTEM,
            user=(
                f"Sprache: {ai_locale_name(locale)}\n\n"
                f"{_describe_catalog(needs, attributes)}\n\n"
                f"Freitext der Person: {free_text}"
            ),
            schema_name="interpretation_result",
            schema=_INTERPRETATION_SCHEMA,
        )
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
        payload = self._create(
            system=_QUESTION_SYSTEM,
            user=(
                f"Sprache: {ai_locale_name(locale)}\n"
                f"Kanonischer Text: {canonical['canonical_text']}\n"
                f"Hilfetext: {canonical.get('help_text', '')}\n"
                f"Erlaubte Antwortoptionen: {allowed_values}\n\n"
                "Formuliere nur die Frage verstaendlicher."
            ),
            schema_name="rendered_question",
            schema=_QUESTION_SCHEMA,
        )
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
        payload = self._create(
            system=_EXPLANATION_SYSTEM,
            user=(
                f"Sprache: {ai_locale_name(locale)}\n\n"
                f"Faktenpaket:\n{json.dumps(_bundle_payload(bundle), ensure_ascii=False)}"
            ),
            schema_name="explanation_result",
            schema=_EXPLANATION_SCHEMA,
        )
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
