AI_LOCALE_NAMES: dict[str, str] = {
    "de": "Deutsch (de-CH)",
    "fr": "Français (fr-CH)",
    "en": "English (en-GB)",
    "es": "Español (es-ES)",
    "pt": "Português europeu (pt-PT)",
    "ary": "الدارجة المغربية / Moroccan Darija (ary-MA)",
}


def ai_locale_name(locale: str) -> str:
    """Return an explicit language name for model prompts.

    Darija's ISO code is not reliably recognized by every model on its own,
    so prompts always carry both the native name and the BCP 47 locale.
    """

    return AI_LOCALE_NAMES.get(locale, locale)
