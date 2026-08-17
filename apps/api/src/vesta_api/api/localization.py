_DISCLAIMERS: dict[str, str] = {
    "de": (
        "Angebote werden nicht automatisch reserviert. "
        "Aktualität und Kontaktangaben vor Ort bestätigen."
    ),
    "fr": (
        "Les offres ne sont pas réservées automatiquement. "
        "Confirmer sur place leur actualité et les coordonnées."
    ),
    "en": (
        "Services are not reserved automatically. "
        "Confirm current details and contact information directly."
    ),
    "es": (
        "Los servicios no se reservan automáticamente. Confirma directamente "
        "que la información y los datos de contacto estén actualizados."
    ),
    "pt": (
        "Os serviços não são reservados automaticamente. Confirma diretamente "
        "se as informações e os contactos estão atualizados."
    ),
    "ary": (
        "الخدمات ما كيتحجزوش أوتوماتيكياً. تأكد مباشرة باللي المعلومات "
        "وبيانات الاتصال مازال صحيحة."
    ),
}


def disclaimer_for(locale: str) -> str:
    """Return the public safety disclaimer in the requested supported locale."""

    normalized = "ary" if locale == "ar" or locale.startswith("ar-") else locale
    return _DISCLAIMERS.get(normalized, _DISCLAIMERS["de"])
