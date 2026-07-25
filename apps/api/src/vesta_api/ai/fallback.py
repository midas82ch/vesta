from vesta_api.domain.ai_models import (
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

DEFAULT_LOCALE = "de"

# Fixed, fachlich freigegebene Texte pro reasons-/uncertainties-Code aus
# services/matching.py. Dies ist der produktive Rückfalltext, nicht nur ein
# Demo-Platzhalter - er läuft auch, wenn ai_enabled=False oder das Modell
# ausfällt.
_REASON_TEXTS: dict[str, dict[str, str]] = {
    "need_matches": {
        "de": "Dieses Angebot passt zu deiner Suche.",
        "fr": "Cette offre correspond à votre recherche.",
        "en": "This offer matches your search.",
        "ar": "يتوافق هذا العرض مع بحثك.",
    },
    "source_is_current": {
        "de": "Die Angaben sind aktuell geprüft.",
        "fr": "Les informations sont vérifiées et à jour.",
        "en": "The information is currently verified.",
        "ar": "تم التحقق من المعلومات وهي محدثة.",
    },
    "language_matches": {
        "de": "Das Angebot ist in deiner Sprache verfügbar.",
        "fr": "L'offre est disponible dans votre langue.",
        "en": "The offer is available in your language.",
        "ar": "العرض متوفر بلغتك.",
    },
    "availability_confirmed": {
        "de": "Der Status ist bestätigt.",
        "fr": "Le statut est confirmé.",
        "en": "Availability is confirmed.",
        "ar": "الحالة مؤكدة.",
    },
}

_UNCERTAINTY_TEXTS: dict[str, dict[str, str]] = {
    "requested_language_not_listed": {
        "de": "Deine Sprache ist nicht ausdrücklich gelistet.",
        "fr": "Votre langue n'est pas explicitement mentionnée.",
        "en": "Your language is not explicitly listed.",
        "ar": "لغتك غير مدرجة صراحة.",
    },
    "availability_requires_contact": {
        "de": "Ruf vorher an und frage, ob aktuell ein Platz frei ist.",
        "fr": "Appelez avant et demandez si une place est disponible.",
        "en": "Call ahead and ask whether a place is currently free.",
        "ar": "اتصل مسبقًا واسأل عما إذا كان هناك مكان متاح حاليًا.",
    },
    "availability_unknown": {
        "de": "Der aktuelle Status ist unbekannt.",
        "fr": "Le statut actuel est inconnu.",
        "en": "Current availability is unknown.",
        "ar": "الحالة الحالية غير معروفة.",
    },
    "dog_access_unknown": {
        "de": "Ob Hunde erlaubt sind, ist unklar. Bitte vor Ort abklären.",
        "fr": "On ne sait pas si les chiens sont admis. À clarifier sur place.",
        "en": "Whether dogs are allowed is unclear. Please check on site.",
        "ar": "غير واضح ما إذا كانت الكلاب مسموحة. يرجى التأكد في الموقع.",
    },
    "identity_document_rule_unknown": {
        "de": "Ob ein Ausweis nötig ist, ist unklar. Bitte vor Ort abklären.",
        "fr": "On ne sait pas si une pièce d'identité est requise.",
        "en": "Whether an ID is required is unclear. Please check on site.",
        "ar": "غير واضح ما إذا كانت الهوية مطلوبة. يرجى التأكد في الموقع.",
    },
    "target_group_must_be_confirmed": {
        "de": "Die Zielgruppe muss vor Ort bestätigt werden.",
        "fr": "Le groupe cible doit être confirmé sur place.",
        "en": "The target group must be confirmed on site.",
        "ar": "يجب تأكيد الفئة المستهدفة في الموقع.",
    },
}


def _localized(localizations: dict[str, dict[str, str]], locale: str) -> dict[str, str]:
    return localizations.get(locale) or localizations.get(DEFAULT_LOCALE) or {}


def _text_for_code(table: dict[str, dict[str, str]], code: str, locale: str) -> str:
    entry = table.get(code, {})
    return entry.get(locale) or entry.get(DEFAULT_LOCALE) or code


class TemplateGateway:
    """Implements all three AI ports using only fixed, catalog-derived
    texts - no model call. This is both the production fallback (ADR 0002:
    "ohne AI bleibt alles funktionsfähig") and the first working state of the
    prototype before a live model is wired in."""

    def interpret(
        self,
        *,
        free_text: str,
        locale: str,
        needs: tuple[NeedDefinition, ...],
        attributes: tuple[AttributeDefinition, ...],
    ) -> InterpretationResult:
        # Free-text understanding is exactly the capability this port exists
        # to add; without a model there is nothing to propose. The caller
        # falls back to the structured need/attribute pickers, which work
        # without AI by design.
        return InterpretationResult(
            need_key=None,
            proposals=(),
            requires_confirmation=(),
            ambiguities=("free_text_interpretation_unavailable",),
            source="template",
        )

    def render_question(
        self,
        *,
        question: QuestionDefinition,
        attribute: AttributeDefinition,
        locale: str,
    ) -> RenderedQuestion:
        texts = _localized(question.localizations, locale)
        options = tuple(
            QuestionOption(
                value=option.value,
                label=_localized(option.localizations, locale).get(
                    "label", option.value
                ),
            )
            for option in attribute.options
        )
        return RenderedQuestion(
            text=texts.get("canonical_text", question.key),
            help_text=texts.get("help_text"),
            unknown_label=texts.get("unknown_label", "?"),
            decline_label=texts.get("decline_label", "-"),
            options=options,
            source="template",
        )

    def explain(self, *, bundle: GroundingBundle, locale: str) -> ExplanationResult:
        reasons = tuple(
            ExplanationReason(
                text=_text_for_code(_REASON_TEXTS, code, locale),
                supported_by=tuple(
                    fact.id for fact in bundle.facts if fact.type == code
                ),
            )
            for code in bundle.match_reasons
        )
        clarification = None
        if bundle.uncertainties:
            first = bundle.uncertainties[0]
            clarification = ExplanationReason(
                text=_text_for_code(_UNCERTAINTY_TEXTS, first, locale),
                supported_by=tuple(
                    fact.id for fact in bundle.facts if fact.type == first
                ),
            )
        next_action = (
            bundle.allowed_next_actions[0] if bundle.allowed_next_actions else None
        )
        headline_key = "need_matches" if "need_matches" in bundle.match_reasons else None
        headline = (
            _text_for_code(_REASON_TEXTS, headline_key, locale)
            if headline_key
            else _text_for_code(_REASON_TEXTS, "need_matches", locale)
        )
        return ExplanationResult(
            headline=headline,
            reasons=reasons,
            clarification=clarification,
            next_action=next_action,
            source="template",
        )
