import re
import unicodedata

from vesta_api.domain.models import ServiceTopic

SERVICE_TOPICS = tuple(ServiceTopic)

_TOPIC_STEMS: dict[str, dict[str, tuple[str, ...]]] = {
    "de": {
        "food": ("essen", "mahlzeit", "nahrung", "lebensmittel", "suppe"),
        "hygiene": ("dusche", "duschen", "hygiene", "wasch"),
        "medical": ("medizin", "arzt", "ärzt", "gesundheit", "verletz", "erste hilfe"),
        "addiction": ("sucht", "droge", "alkohol", "substanz", "entzug"),
        "housing": ("wohn", "wohnung", "obdach", "unterkunft", "miete"),
        "finances": ("geld", "schulden", "schuldner", "finanz", "budget", "rechnung"),
        "legal": ("recht", "anwalt", "jurist", "gesetz"),
        "mental_health": ("psych", "krise", "depress", "angst", "seel"),
        "violence": ("gewalt", "bedroh", "opfer", "missbrauch", "häuslich"),
    },
    "fr": {
        "food": ("manger", "repas", "nourriture", "aliment", "soupe"),
        "hygiene": ("douche", "hygiène", "laver"),
        "medical": ("médic", "médecin", "santé", "bless", "premiers secours"),
        "addiction": ("addict", "dépendance", "drogue", "alcool", "sevrage"),
        "housing": ("logement", "habitat", "sans-abri", "hébergement", "loyer"),
        "finances": ("argent", "dette", "financ", "budget", "facture"),
        "legal": ("jurid", "droit", "avocat", "loi"),
        "mental_health": ("psych", "crise", "dépress", "angoisse", "mental"),
        "violence": ("violence", "menace", "victime", "abus", "conjugal"),
    },
    "en": {
        "food": ("food", "meal", "eat", "grocer", "soup"),
        "hygiene": ("shower", "hygiene", "wash"),
        "medical": ("medical", "doctor", "health", "injur", "first aid"),
        "addiction": ("addict", "drug", "alcohol", "substance", "withdrawal"),
        "housing": ("housing", "homeless", "shelter", "rent", "accommodation"),
        "finances": ("money", "debt", "financ", "budget", "bill"),
        "legal": ("legal", "lawyer", "law", "rights"),
        "mental_health": ("mental", "psych", "crisis", "depress", "anxiety"),
        "violence": ("violence", "threat", "victim", "abuse", "domestic"),
    },
    "es": {
        "food": ("comida", "comer", "alimento", "sopa"),
        "hygiene": ("ducha", "higiene", "lavar"),
        "medical": ("médic", "doctor", "salud", "herid", "primeros auxilios"),
        "addiction": ("adicci", "droga", "alcohol", "sustancia", "abstinencia"),
        "housing": ("vivienda", "hogar", "albergue", "alojamiento", "alquiler"),
        "finances": ("dinero", "deuda", "finanz", "presupuesto", "factura"),
        "legal": ("juríd", "derecho", "abogad", "ley"),
        "mental_health": ("mental", "psic", "crisis", "depres", "ansiedad"),
        "violence": ("violencia", "amenaza", "víctima", "abuso", "doméstic"),
    },
    "pt": {
        "food": ("comida", "comer", "alimento", "sopa"),
        "hygiene": ("duche", "banho", "higiene", "lavar"),
        "medical": ("médic", "saúde", "ferid", "primeiros socorros"),
        "addiction": ("dependência", "adicção", "droga", "álcool", "substância"),
        "housing": ("habitação", "casa", "sem-abrigo", "alojamento", "renda"),
        "finances": ("dinheiro", "dívida", "finanç", "orçamento", "fatura"),
        "legal": ("juríd", "direito", "advogad", "lei"),
        "mental_health": ("mental", "psic", "crise", "depress", "ansiedade"),
        "violence": ("violência", "ameaça", "vítima", "abuso", "doméstic"),
    },
    "ary": {
        "food": ("ماكلة", "الماكلة", "ناكل", "طعام"),
        "hygiene": ("دوش", "نغسل", "النظافة"),
        "medical": ("طبيب", "صحة", "جرح", "إسعاف"),
        "addiction": ("إدمان", "مخدرات", "كحول"),
        "housing": ("سكن", "دار", "كرا", "بلاصة ننعس"),
        "finances": ("فلوس", "دين", "ديون", "فاتورة"),
        "legal": ("قانون", "محامي", "حقوق"),
        "mental_health": ("نفسي", "أزمة", "اكتئاب", "خوف"),
        "violence": ("عنف", "تهديد", "ضحية", "اعتداء"),
    },
}


def _normalized(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    return "".join(character for character in decomposed if not unicodedata.combining(character))


def detect_service_topics(text: str, locale: str) -> tuple[ServiceTopic, ...]:
    """Detect a small, reviewable set of service topics from user or offer text."""

    lowered_locale = locale.lower()
    normalized_locale = (
        "ary"
        if lowered_locale == "ar" or lowered_locale.startswith("ar-")
        else lowered_locale.split("-")[0]
    )
    stems = _TOPIC_STEMS.get(normalized_locale, _TOPIC_STEMS["de"])
    normalized_text = _normalized(text)
    words = tuple(re.findall(r"[^\W_]+", normalized_text, flags=re.UNICODE))
    detected: list[ServiceTopic] = []

    for topic in SERVICE_TOPICS:
        topic_stems = stems[topic]
        if any(
            _normalized(phrase) in normalized_text
            if " " in phrase
            else any(word.startswith(_normalized(phrase)) for word in words)
            for phrase in topic_stems
        ):
            detected.append(topic)

    return tuple(detected)
