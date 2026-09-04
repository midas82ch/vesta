_DISCLAIMERS: dict[str, str] = {
    "de": "Bitte nimm direkt Kontakt auf. Vesta reserviert keinen Platz.",
    "fr": "Prends directement contact avec le service. Vesta ne réserve pas de place.",
    "en": "Please contact the service directly. Vesta does not reserve places.",
    "es": "Contacta directamente con el servicio. Vesta no reserva plazas.",
    "pt": "Contacta diretamente o serviço. A Vesta não reserva lugares.",
    "ary": "تاصل مباشرة بالخدمة. فيستا ما كتحجز حتى بلاصة.",
}


def disclaimer_for(locale: str) -> str:
    """Return the public safety disclaimer in the requested supported locale."""

    normalized = "ary" if locale == "ar" or locale.startswith("ar-") else locale
    return _DISCLAIMERS.get(normalized, _DISCLAIMERS["de"])
