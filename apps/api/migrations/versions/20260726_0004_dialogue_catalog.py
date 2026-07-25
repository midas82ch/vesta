"""Create the parametrized dialogue catalog (needs, attributes, questions).

Revision ID: 20260726_0004
Revises: 20260725_0003
Create Date: 2026-07-26
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260726_0004"
down_revision: str | None = "20260725_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NEED_SLEEP = "00000000-0000-0000-0001-000000000001"
NEED_BASIC = "00000000-0000-0000-0001-000000000002"
NEED_COUNSELLING = "00000000-0000-0000-0001-000000000003"

ATTR_DOG = "00000000-0000-0000-0002-000000000001"
ATTR_IDENTITY = "00000000-0000-0000-0002-000000000002"
ATTR_GENDER = "00000000-0000-0000-0002-000000000003"
ATTR_AGE = "00000000-0000-0000-0002-000000000004"

OPTION_FINTA = "00000000-0000-0000-0003-000000000001"
OPTION_OTHER = "00000000-0000-0000-0003-000000000002"

QUESTION_DOG = "00000000-0000-0000-0004-000000000001"
QUESTION_IDENTITY = "00000000-0000-0000-0004-000000000002"
QUESTION_GENDER = "00000000-0000-0000-0004-000000000003"
QUESTION_AGE = "00000000-0000-0000-0004-000000000004"


def _insert(table: str, columns: list[str], rows: list[tuple], conflict: str) -> None:
    column_list = ", ".join(columns)
    row_values = ",\n".join(f"    ({', '.join(_sql(v) for v in row)})" for row in rows)
    op.execute(
        f"INSERT INTO {table} ({column_list}) VALUES\n{row_values}\n"
        f"ON CONFLICT ({conflict}) DO NOTHING"
    )


def _sql(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    escaped = str(value).replace("'", "''")
    return f"'{escaped}'"


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS need_definitions (
            id UUID PRIMARY KEY,
            key TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL DEFAULT 'published',
            sort_order INTEGER NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS need_localizations (
            need_id UUID NOT NULL REFERENCES need_definitions(id) ON DELETE CASCADE,
            locale TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            PRIMARY KEY (need_id, locale)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS attribute_definitions (
            id UUID PRIMARY KEY,
            key TEXT NOT NULL UNIQUE,
            value_type TEXT NOT NULL
                CHECK (value_type IN ('boolean', 'integer', 'enum')),
            confirmation_required BOOLEAN NOT NULL DEFAULT true,
            skippable BOOLEAN NOT NULL DEFAULT true,
            status TEXT NOT NULL DEFAULT 'published',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS attribute_options (
            id UUID PRIMARY KEY,
            attribute_id UUID NOT NULL
                REFERENCES attribute_definitions(id) ON DELETE CASCADE,
            value TEXT NOT NULL,
            sort_order INTEGER NOT NULL,
            UNIQUE (attribute_id, value)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS attribute_option_localizations (
            option_id UUID NOT NULL
                REFERENCES attribute_options(id) ON DELETE CASCADE,
            locale TEXT NOT NULL,
            label TEXT NOT NULL,
            explanation TEXT,
            PRIMARY KEY (option_id, locale)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS question_definitions (
            id UUID PRIMARY KEY,
            key TEXT NOT NULL UNIQUE,
            attribute_definition_id UUID NOT NULL
                REFERENCES attribute_definitions(id),
            answer_type TEXT NOT NULL
                CHECK (answer_type IN ('yes_no_unknown', 'single_choice', 'number')),
            priority INTEGER NOT NULL,
            ai_rephrasing_allowed BOOLEAN NOT NULL DEFAULT true,
            status TEXT NOT NULL DEFAULT 'published',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS question_localizations (
            question_id UUID NOT NULL
                REFERENCES question_definitions(id) ON DELETE CASCADE,
            locale TEXT NOT NULL,
            canonical_text TEXT NOT NULL,
            help_text TEXT,
            unknown_label TEXT NOT NULL,
            decline_label TEXT NOT NULL,
            PRIMARY KEY (question_id, locale)
        )
        """
    )

    # --- Seed data: mirrors data/seed/dialogue_catalog.json exactly. ---

    _insert(
        "need_definitions",
        ["id", "key", "sort_order"],
        [
            (NEED_SLEEP, "sleep_tonight", 1),
            (NEED_BASIC, "basic_needs", 2),
            (NEED_COUNSELLING, "counselling", 3),
        ],
        conflict="id",
    )
    _insert(
        "need_localizations",
        ["need_id", "locale", "title", "description"],
        [
            (NEED_SLEEP, "de", "Heute schlafen", "Einen Platz für die Nacht suchen"),
            (NEED_SLEEP, "fr", "Dormir ce soir", "Chercher une place pour la nuit"),
            (NEED_SLEEP, "en", "Sleep tonight", "Find a place for the night"),
            (NEED_SLEEP, "ar", "النوم الليلة", "البحث عن مكان لقضاء الليلة"),
            (NEED_BASIC, "de", "Grundversorgung", "Essen, Dusche oder Ersthilfe"),
            (
                NEED_BASIC,
                "fr",
                "Besoins de base",
                "Nourriture, douche ou premiers secours",
            ),
            (NEED_BASIC, "en", "Basic needs", "Food, shower or first aid"),
            (
                NEED_BASIC,
                "ar",
                "الاحتياجات الأساسية",
                "الطعام أو الاستحمام أو الإسعافات الأولية",
            ),
            (NEED_COUNSELLING, "de", "Beratung", "Hilfe bei Sucht, Wohnen oder Geld"),
            (
                NEED_COUNSELLING,
                "fr",
                "Conseil",
                "Aide en cas de dépendance, logement ou argent",
            ),
            (
                NEED_COUNSELLING,
                "en",
                "Counselling",
                "Help with addiction, housing or money",
            ),
            (
                NEED_COUNSELLING,
                "ar",
                "الاستشارة",
                "المساعدة في الإدمان أو السكن أو المال",
            ),
        ],
        conflict="need_id, locale",
    )

    _insert(
        "attribute_definitions",
        ["id", "key", "value_type", "confirmation_required", "skippable"],
        [
            (ATTR_DOG, "person.has_dog", "boolean", True, True),
            (ATTR_IDENTITY, "person.has_identity_document", "boolean", True, True),
            (ATTR_GENDER, "person.gender", "enum", True, True),
            (ATTR_AGE, "person.age", "integer", True, True),
        ],
        conflict="id",
    )
    _insert(
        "attribute_options",
        ["id", "attribute_id", "value", "sort_order"],
        [
            (OPTION_FINTA, ATTR_GENDER, "finta", 1),
            (OPTION_OTHER, ATTR_GENDER, "other", 2),
        ],
        conflict="id",
    )
    _insert(
        "attribute_option_localizations",
        ["option_id", "locale", "label"],
        [
            (OPTION_FINTA, "de", "Frau / FINTA"),
            (OPTION_FINTA, "fr", "Femme / FINTA"),
            (OPTION_FINTA, "en", "Woman / FINTA"),
            (OPTION_FINTA, "ar", "امرأة / FINTA"),
            (OPTION_OTHER, "de", "Andere / allgemeine Suche"),
            (OPTION_OTHER, "fr", "Autre / recherche générale"),
            (OPTION_OTHER, "en", "Other / general search"),
            (OPTION_OTHER, "ar", "أخرى / بحث عام"),
        ],
        conflict="option_id, locale",
    )

    _insert(
        "question_definitions",
        [
            "id",
            "key",
            "attribute_definition_id",
            "answer_type",
            "priority",
            "ai_rephrasing_allowed",
        ],
        [
            (QUESTION_DOG, "sleep.has_dog", ATTR_DOG, "yes_no_unknown", 10, True),
            (
                QUESTION_IDENTITY,
                "sleep.has_identity_document",
                ATTR_IDENTITY,
                "yes_no_unknown",
                20,
                True,
            ),
            (QUESTION_GENDER, "sleep.gender", ATTR_GENDER, "single_choice", 30, True),
            (QUESTION_AGE, "sleep.age", ATTR_AGE, "number", 40, True),
        ],
        conflict="id",
    )
    _insert(
        "question_localizations",
        [
            "question_id",
            "locale",
            "canonical_text",
            "help_text",
            "unknown_label",
            "decline_label",
        ],
        [
            (
                QUESTION_DOG,
                "de",
                "Führen Sie ein Tier mit sich?",
                "Einige Schlafangebote können keine Hunde aufnehmen.",
                "Weiss nicht",
                "Möchte ich nicht sagen",
            ),
            (
                QUESTION_DOG,
                "fr",
                "Avez-vous un animal avec vous ?",
                "Certaines offres d'hébergement n'acceptent pas les chiens.",
                "Je ne sais pas",
                "Je préfère ne pas dire",
            ),
            (
                QUESTION_DOG,
                "en",
                "Do you have an animal with you?",
                "Some overnight offers cannot accept dogs.",
                "Don't know",
                "Prefer not to say",
            ),
            (
                QUESTION_DOG,
                "ar",
                "هل معك حيوان؟",
                "بعض أماكن المبيت لا يمكنها استقبال الكلاب.",
                "لا أعرف",
                "أفضل عدم الإجابة",
            ),
            (
                QUESTION_IDENTITY,
                "de",
                "Haben Sie einen Ausweis dabei?",
                "Einige Angebote setzen einen Ausweis voraus.",
                "Weiss nicht",
                "Möchte ich nicht sagen",
            ),
            (
                QUESTION_IDENTITY,
                "fr",
                "Avez-vous une pièce d'identité ?",
                "Certaines offres exigent une pièce d'identité.",
                "Je ne sais pas",
                "Je préfère ne pas dire",
            ),
            (
                QUESTION_IDENTITY,
                "en",
                "Do you have an identity document?",
                "Some offers require an identity document.",
                "Don't know",
                "Prefer not to say",
            ),
            (
                QUESTION_IDENTITY,
                "ar",
                "هل معك وثيقة هوية؟",
                "بعض العروض تتطلب وثيقة هوية.",
                "لا أعرف",
                "أفضل عدم الإجابة",
            ),
            (
                QUESTION_GENDER,
                "de",
                "Welche Zielgruppe trifft auf Sie zu?",
                "Die Angabe hilft, Angebote mit besonderen "
                "Zugangsbedingungen korrekt einzuordnen.",
                "Weiss nicht",
                "Keine Angabe",
            ),
            (
                QUESTION_GENDER,
                "fr",
                "Quel groupe cible vous correspond ?",
                "Cette information aide à identifier les offres avec des "
                "conditions d'accès particulières.",
                "Je ne sais pas",
                "Sans indication",
            ),
            (
                QUESTION_GENDER,
                "en",
                "Which target group applies to you?",
                "This helps match offers with specific access conditions.",
                "Don't know",
                "Prefer not to say",
            ),
            (
                QUESTION_GENDER,
                "ar",
                "ما هي الفئة المستهدفة التي تنطبق عليك؟",
                "تساعد هذه المعلومة في تحديد العروض ذات شروط الوصول الخاصة.",
                "لا أعرف",
                "دون تحديد",
            ),
            (
                QUESTION_AGE,
                "de",
                "Wie alt sind Sie?",
                "Einige Angebote gelten nur ab oder bis zu einem bestimmten Alter.",
                "Weiss nicht",
                "Möchte ich nicht sagen",
            ),
            (
                QUESTION_AGE,
                "fr",
                "Quel âge avez-vous ?",
                "Certaines offres s'appliquent seulement à partir ou "
                "jusqu'à un certain âge.",
                "Je ne sais pas",
                "Je préfère ne pas dire",
            ),
            (
                QUESTION_AGE,
                "en",
                "How old are you?",
                "Some offers only apply from or up to a certain age.",
                "Don't know",
                "Prefer not to say",
            ),
            (
                QUESTION_AGE,
                "ar",
                "كم عمرك؟",
                "بعض العروض تنطبق فقط بدءًا من أو حتى عمر معين.",
                "لا أعرف",
                "أفضل عدم الإجابة",
            ),
        ],
        conflict="question_id, locale",
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS question_localizations")
    op.execute("DROP TABLE IF EXISTS question_definitions")
    op.execute("DROP TABLE IF EXISTS attribute_option_localizations")
    op.execute("DROP TABLE IF EXISTS attribute_options")
    op.execute("DROP TABLE IF EXISTS attribute_definitions")
    op.execute("DROP TABLE IF EXISTS need_localizations")
    op.execute("DROP TABLE IF EXISTS need_definitions")
