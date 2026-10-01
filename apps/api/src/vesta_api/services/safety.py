import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class SafetySignal:
    code: str
    matched_pattern: str


_VIOLENCE_PATTERNS: dict[str, tuple[str, ...]] = {
    "de": (
        r"\b(?:mein|meine|mein[e]?)\s+(?:mann|frau|partner|partnerin)\s+ist\s+gewaltt[aä]tig\b",
        r"\b(?:schl[aä]gt|wuergt|würgt|bedroht|verfolgt)\s+mich\b",
        r"\bich\s+werde\s+(?:geschlagen|bedroht|misshandelt)\b",
        r"\b(?:jemand|er|sie)\s+(?:droht|bedroht|schl[aä]gt|verfolgt)\s+mich\b",
        r"\b(?:ich\s+bin|wir\s+sind)\s+(?:in\s+)?(?:akuter\s+)?gefahr\b",
        r"\b(?:will|versucht)\s+mich\s+(?:zu\s+)?(?:t[oö]ten|verletzen)\b",
        r"\bh[aä]usliche\s+gewalt\b",
    ),
    "fr": (
        r"\b(?:mon|ma)\s+(?:mari|femme|partenaire)\s+est\s+violent",
        r"\b(?:me\s+frappe|me\s+menace|m[' ]etrangle)",
        r"\b(?:je\s+suis|nous\s+sommes)\s+en\s+danger\b",
        r"\b(?:veut|essaie\s+de)\s+me\s+(?:tuer|blesser)\b",
        r"\bviolence\s+domestique\b",
    ),
    "en": (
        r"\b(?:my|a)\s+(?:husband|wife|partner)\s+is\s+violent\b",
        r"\b(?:hits|strangles|threatens|stalks)\s+me\b",
        r"\b(?:i\s+am|we\s+are)\s+in\s+(?:immediate\s+)?danger\b",
        r"\b(?:wants|tried|is\s+trying)\s+to\s+(?:kill|hurt)\s+me\b",
        r"\bdomestic\s+(?:abuse|violence)\b",
    ),
    "es": (
        r"\bmi\s+(?:marido|mujer|pareja)\s+es\s+violent[oa]\b",
        r"\bme\s+(?:pega|golpea|amenaza|estrangula)\b",
        r"\b(?:estoy|estamos)\s+en\s+peligro\b",
        r"\b(?:quiere|intenta)\s+(?:matarme|hacerme\s+daño)\b",
        r"\bviolencia\s+dom[eé]stica\b",
    ),
    "pt": (
        r"\b(?:o\s+meu|a\s+minha)\s+(?:marido|mulher|companheir[oa])\s+[eé]\s+violent[oa]\b",
        r"\b(?:bate-me|amea[cç]a-me|estrangula-me)\b",
        r"\b(?:estou|estamos)\s+em\s+perigo\b",
        r"\b(?:quer|tenta)\s+(?:matar-me|ferir-me)\b",
        r"\bviol[eê]ncia\s+dom[eé]stica\b",
    ),
    "ary": (
        r"(?:راجلي|مرتي|الشريك|الشريكة).{0,12}(?:عنيف|عنيفة|كيضربني|كيهددني)",
        r"(?:كيضربني|كيخنقني|كيهددني|عنف أسري|العنف الأسري)",
        r"(?:أنا|حنا).{0,8}(?:فخطر|في خطر)",
        r"(?:باغي|حاول).{0,8}(?:يقتلني|يجرحني)",
    ),
}

_NEGATIONS: dict[str, tuple[str, ...]] = {
    "de": (
        "nicht gewalttätig",
        "keine gewalt",
        "keine häusliche gewalt",
        "nicht bedroht",
        "nicht in gefahr",
    ),
    "fr": (
        "pas violent",
        "aucune violence",
        "pas de violence domestique",
        "pas menacé",
        "pas en danger",
    ),
    "en": (
        "not violent",
        "no violence",
        "no domestic violence",
        "not threatened",
        "not in danger",
    ),
    "es": (
        "no es violento",
        "sin violencia",
        "sin violencia doméstica",
        "no me amenaza",
        "no estoy en peligro",
    ),
    "pt": (
        "não é violento",
        "sem violência",
        "sem violência doméstica",
        "não me ameaça",
        "não estou em perigo",
    ),
    "ary": ("ماشي عنيف", "ما كاينش العنف", "ما كيهددنيش"),
}


def _normalized(value: str) -> str:
    return unicodedata.normalize("NFKC", value).casefold().strip()


def normalized_locale(locale: str) -> str:
    normalized = locale.lower().replace("_", "-")
    if normalized == "ar" or normalized.startswith("ar-"):
        return "ary"
    language = normalized.split("-", 1)[0]
    return language if language in _VIOLENCE_PATTERNS else "de"


def detect_safety_signal(free_text: str, locale: str) -> SafetySignal | None:
    language = normalized_locale(locale)
    text = _normalized(free_text)
    for negation in _NEGATIONS[language]:
        text = text.replace(negation, " ")
    for pattern in _VIOLENCE_PATTERNS[language]:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return SafetySignal(code="possible_violence_or_threat", matched_pattern=pattern)
    return None


_RESOURCE_TEXTS: dict[str, dict[str, str]] = {
    "de": {
        "police": "Polizei",
        "medical": "Medizinische Hilfe",
        "victim": "Opferhilfe Schweiz",
        "police_note": "Bei unmittelbarer Bedrohung sofort anrufen.",
        "medical_note": "Bei Verletzungen oder einem medizinischen Notfall.",
        "victim_note": "Kostenlos, vertraulich und rund um die Uhr erreichbar.",
        "youth": "Beratung 147",
        "youth_note": "Für Kinder und Jugendliche: kostenlos, vertraulich und rund um die Uhr.",
        "crisis": "Die Dargebotene Hand",
        "crisis_note": "Ein offenes Ohr in schwierigen Situationen, rund um die Uhr.",
    },
    "fr": {
        "police": "Police",
        "medical": "Urgences médicales",
        "victim": "Aide aux victimes Suisse",
        "police_note": "Appelez immédiatement en cas de menace directe.",
        "medical_note": "En cas de blessure ou d'urgence médicale.",
        "victim_note": "Service gratuit, confidentiel et disponible 24 h/24.",
        "youth": "Conseil 147",
        "youth_note": (
            "Pour les enfants et les jeunes : gratuit, confidentiel "
            "et disponible 24 h/24."
        ),
        "crisis": "La Main Tendue",
        "crisis_note": "Une écoute dans les moments difficiles, disponible 24 h/24.",
    },
    "en": {
        "police": "Police",
        "medical": "Medical emergency",
        "victim": "Victim Support Switzerland",
        "police_note": "Call immediately if you are under direct threat.",
        "medical_note": "For injuries or a medical emergency.",
        "victim_note": "Free, confidential and available around the clock.",
        "youth": "Counselling 147",
        "youth_note": (
            "For children and young people: free, confidential and "
            "available around the clock."
        ),
        "crisis": "The Helping Hand",
        "crisis_note": "Someone to listen in difficult situations, available around the clock.",
    },
    "es": {
        "police": "Policía",
        "medical": "Emergencias médicas",
        "victim": "Ayuda a víctimas Suiza",
        "police_note": "Llama inmediatamente si existe una amenaza directa.",
        "medical_note": "En caso de lesiones o emergencia médica.",
        "victim_note": "Servicio gratuito, confidencial y disponible las 24 horas.",
        "youth": "Asesoramiento 147",
        "youth_note": (
            "Para niños, niñas y jóvenes: gratuito, confidencial y "
            "disponible las 24 horas."
        ),
        "crisis": "La Mano Tendida",
        "crisis_note": "Alguien que escucha en situaciones difíciles, disponible las 24 horas.",
    },
    "pt": {
        "police": "Polícia",
        "medical": "Emergência médica",
        "victim": "Apoio à vítima Suíça",
        "police_note": "Liga imediatamente em caso de ameaça direta.",
        "medical_note": "Em caso de ferimentos ou emergência médica.",
        "victim_note": "Serviço gratuito, confidencial e disponível 24 horas.",
        "youth": "Aconselhamento 147",
        "youth_note": "Para crianças e jovens: gratuito, confidencial e disponível 24 horas.",
        "crisis": "A Mão Amiga",
        "crisis_note": "Alguém que escuta em situações difíceis, disponível 24 horas.",
    },
    "ary": {
        "police": "البوليس",
        "medical": "المساعدة الطبية المستعجلة",
        "victim": "مساعدة الضحايا فسويسرا",
        "police_note": "عيط دابا إلا كنت فخطر مباشر.",
        "medical_note": "إلا كنت مجروح ولا كاينة حالة طبية مستعجلة.",
        "victim_note": "مساعدة مجانية وسرية ومتوفرة فالليل والنهار.",
        "youth": "المساعدة 147",
        "youth_note": "للأطفال والشباب: مجانية وسرية ومتوفرة فالليل والنهار.",
        "crisis": "اليد الممدودة",
        "crisis_note": "شي حد يسمع ليك فالظروف الصعيبة، فالليل والنهار.",
    },
}


def safety_resources(locale: str, *, immediate_danger: bool) -> tuple[dict[str, str], ...]:
    texts = _RESOURCE_TEXTS[normalized_locale(locale)]
    if immediate_danger:
        return (
            {
                "kind": "emergency",
                "name": texts["police"],
                "phone": "117",
                "url": "tel:117",
                "description": texts["police_note"],
            },
            {
                "kind": "emergency",
                "name": texts["medical"],
                "phone": "144",
                "url": "tel:144",
                "description": texts["medical_note"],
            },
        )
    return (
        {
            "kind": "victim_support",
            "name": texts["victim"],
            "phone": "142",
            "url": "tel:142",
            "description": texts["victim_note"],
        },
        {
            "kind": "victim_support",
            "name": texts["victim"],
            "phone": "",
            "url": "https://www.opferhilfe-schweiz.ch/",
            "description": texts["victim_note"],
        },
    )


def no_match_resources(
    locale: str, *, youth: bool = False, emotional_crisis: bool = False
) -> tuple[dict[str, str], ...]:
    """Return contextual support without turning a normal no-match into a handoff."""

    texts = _RESOURCE_TEXTS[normalized_locale(locale)]
    resources: list[dict[str, str]] = []
    if youth:
        resources.append(
            {
                "kind": "youth_support",
                "name": texts["youth"],
                "phone": "147",
                "url": "tel:147",
                "description": texts["youth_note"],
            }
        )
    if emotional_crisis:
        resources.append(
            {
                "kind": "crisis_support",
                "name": texts["crisis"],
                "phone": "143",
                "url": "tel:143",
                "description": texts["crisis_note"],
            }
        )
    return tuple(resources)
