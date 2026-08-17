"""Add Spanish, Portuguese and Darija dialogue localizations.

Revision ID: 20260817_0010
Revises: 20260817_0009
Create Date: 2026-08-17
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260817_0010"
down_revision: str | None = "20260817_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NEED_SLEEP = "00000000-0000-0000-0001-000000000001"
NEED_BASIC = "00000000-0000-0000-0001-000000000002"
NEED_COUNSELLING = "00000000-0000-0000-0001-000000000003"
OPTION_FINTA = "00000000-0000-0000-0003-000000000001"
OPTION_OTHER = "00000000-0000-0000-0003-000000000002"
QUESTION_DOG = "00000000-0000-0000-0004-000000000001"
QUESTION_IDENTITY = "00000000-0000-0000-0004-000000000002"
QUESTION_GENDER = "00000000-0000-0000-0004-000000000003"
QUESTION_AGE = "00000000-0000-0000-0004-000000000004"


def _sql(value: str) -> str:
    escaped = value.replace("'", "''")
    return f"'{escaped}'"


def _values(rows: list[tuple[str, ...]]) -> str:
    return ",\n".join(
        f"    ({', '.join(_sql(value) for value in row)})" for row in rows
    )


def upgrade() -> None:
    op.execute("DELETE FROM need_localizations WHERE locale = 'ar'")
    op.execute("DELETE FROM attribute_option_localizations WHERE locale = 'ar'")
    op.execute("DELETE FROM question_localizations WHERE locale = 'ar'")

    need_rows = [
        (NEED_SLEEP, "es", "Dormir esta noche", "Buscar un lugar para pasar la noche"),
        (NEED_SLEEP, "pt", "Dormir esta noite", "Procurar um lugar para passar a noite"),
        (NEED_SLEEP, "ary", "فين تنعس الليلة", "قلب على بلاصة تبات فيها"),
        (NEED_BASIC, "es", "Necesidades básicas", "Comida, ducha o primeros auxilios"),
        (NEED_BASIC, "pt", "Necessidades básicas", "Comida, duche ou primeiros socorros"),
        (NEED_BASIC, "ary", "الحاجيات الأساسية", "الماكلة، الدوش ولا الإسعافات الأولية"),
        (
            NEED_COUNSELLING,
            "es",
            "Asesoramiento",
            "Ayuda con adicciones, vivienda o dinero",
        ),
        (
            NEED_COUNSELLING,
            "pt",
            "Aconselhamento",
            "Ajuda com dependências, habitação ou dinheiro",
        ),
        (
            NEED_COUNSELLING,
            "ary",
            "الاستشارة",
            "مساعدة فالإدمان، السكن ولا الفلوس",
        ),
    ]
    op.execute(
        "INSERT INTO need_localizations "
        "(need_id, locale, title, description) VALUES\n"
        f"{_values(need_rows)}\n"
        "ON CONFLICT (need_id, locale) DO UPDATE SET "
        "title = EXCLUDED.title, description = EXCLUDED.description"
    )

    option_rows = [
        (OPTION_FINTA, "es", "Mujer / FINTA"),
        (OPTION_FINTA, "pt", "Mulher / FINTA"),
        (OPTION_FINTA, "ary", "مرا / FINTA"),
        (OPTION_OTHER, "es", "Otro / búsqueda general"),
        (OPTION_OTHER, "pt", "Outro / pesquisa geral"),
        (OPTION_OTHER, "ary", "اختيار آخر / بحث عام"),
    ]
    op.execute(
        "INSERT INTO attribute_option_localizations "
        "(option_id, locale, label) VALUES\n"
        f"{_values(option_rows)}\n"
        "ON CONFLICT (option_id, locale) DO UPDATE SET label = EXCLUDED.label"
    )

    question_rows = [
        (
            QUESTION_DOG,
            "de",
            "Hast du ein Tier dabei?",
            "Einige Schlafangebote können keine Hunde aufnehmen.",
            "Weiss nicht",
            "Möchte ich nicht angeben",
        ),
        (
            QUESTION_DOG,
            "fr",
            "As-tu un animal avec toi ?",
            "Certaines offres d'hébergement n'acceptent pas les chiens.",
            "Je ne sais pas",
            "Je préfère ne pas l’indiquer",
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
            "es",
            "¿Tienes un animal contigo?",
            "Algunos alojamientos nocturnos no admiten perros.",
            "No lo sé",
            "Prefiero no responder",
        ),
        (
            QUESTION_DOG,
            "pt",
            "Tens algum animal contigo?",
            "Alguns alojamentos noturnos não aceitam cães.",
            "Não sei",
            "Prefiro não responder",
        ),
        (
            QUESTION_DOG,
            "ary",
            "واش معاك شي حيوان؟",
            "شي خدمات المبيت ما كيقبلوش الكلاب.",
            "ما عارفش",
            "ما بغيتش نجاوب",
        ),
        (
            QUESTION_IDENTITY,
            "de",
            "Hast du einen Ausweis dabei?",
            "Einige Angebote setzen einen Ausweis voraus.",
            "Weiss nicht",
            "Möchte ich nicht angeben",
        ),
        (
            QUESTION_IDENTITY,
            "fr",
            "As-tu une pièce d’identité ?",
            "Certaines offres exigent une pièce d'identité.",
            "Je ne sais pas",
            "Je préfère ne pas l’indiquer",
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
            "es",
            "¿Tienes un documento de identidad?",
            "Algunos servicios exigen un documento de identidad.",
            "No lo sé",
            "Prefiero no responder",
        ),
        (
            QUESTION_IDENTITY,
            "pt",
            "Tens um documento de identificação?",
            "Alguns serviços exigem um documento de identificação.",
            "Não sei",
            "Prefiro não responder",
        ),
        (
            QUESTION_IDENTITY,
            "ary",
            "واش معاك وثيقة الهوية؟",
            "شي خدمات كيطلبو وثيقة الهوية.",
            "ما عارفش",
            "ما بغيتش نجاوب",
        ),
        (
            QUESTION_GENDER,
            "de",
            "Kommt für dich ein Angebot speziell für Frauen und FINTA-Personen infrage?",
            "Einige Unterkünfte sind ausschliesslich für Frauen und FINTA-Personen zugänglich.",
            "Weiss nicht",
            "Keine Angabe",
        ),
        (
            QUESTION_GENDER,
            "fr",
            "Une offre spécialement destinée aux femmes et aux personnes FINTA te convient-elle ?",
            "Certains hébergements sont exclusivement accessibles aux femmes "
            "et aux personnes FINTA.",
            "Je ne sais pas",
            "Sans indication",
        ),
        (
            QUESTION_GENDER,
            "en",
            "Would a service specifically for women and FINTA people suit you?",
            "Some shelters are exclusively available to women and FINTA people.",
            "Don't know",
            "Prefer not to say",
        ),
        (
            QUESTION_GENDER,
            "es",
            "¿Te conviene un servicio específico para mujeres y personas FINTA?",
            "Algunos alojamientos son accesibles exclusivamente para mujeres y personas FINTA.",
            "No lo sé",
            "Prefiero no indicarlo",
        ),
        (
            QUESTION_GENDER,
            "pt",
            "Um serviço específico para mulheres e pessoas FINTA é adequado para ti?",
            "Alguns alojamentos destinam-se exclusivamente a mulheres e pessoas FINTA.",
            "Não sei",
            "Prefiro não indicar",
        ),
        (
            QUESTION_GENDER,
            "ary",
            "واش تناسبك خدمة خاصة بالنساء وبأشخاص FINTA؟",
            "شي مراكز الإيواء مخصصين غير للنساء ولأشخاص FINTA.",
            "ما عارفش",
            "ما بغيتش نجاوب",
        ),
        (
            QUESTION_AGE,
            "de",
            "Geht es um eine volljährige Person?",
            "Einige Schlafangebote sind erst ab 18 Jahren zugänglich.",
            "Weiss nicht",
            "Möchte ich nicht angeben",
        ),
        (
            QUESTION_AGE,
            "fr",
            "La recherche concerne-t-elle une personne majeure ?",
            "Certains hébergements ne sont accessibles qu’à partir de 18 ans.",
            "Je ne sais pas",
            "Je préfère ne pas l’indiquer",
        ),
        (
            QUESTION_AGE,
            "en",
            "Is the search for an adult?",
            "Some overnight services are only available from the age of 18.",
            "Don't know",
            "Prefer not to say",
        ),
        (
            QUESTION_AGE,
            "es",
            "¿La búsqueda es para una persona adulta?",
            "Algunos alojamientos nocturnos solo están disponibles a partir de los 18 años.",
            "No lo sé",
            "Prefiero no indicarlo",
        ),
        (
            QUESTION_AGE,
            "pt",
            "A pesquisa é para uma pessoa adulta?",
            "Alguns alojamentos noturnos só estão disponíveis a partir dos 18 anos.",
            "Não sei",
            "Prefiro não indicar",
        ),
        (
            QUESTION_AGE,
            "ary",
            "واش البحث على شخص راشد؟",
            "شي خدمات المبيت متوفرين غير للناس اللي عندهم 18 عام ولا كثر.",
            "ما عارفش",
            "ما بغيتش نجاوب",
        ),
    ]
    op.execute(
        "INSERT INTO question_localizations "
        "(question_id, locale, canonical_text, help_text, unknown_label, decline_label) "
        "VALUES\n"
        f"{_values(question_rows)}\n"
        "ON CONFLICT (question_id, locale) DO UPDATE SET "
        "canonical_text = EXCLUDED.canonical_text, "
        "help_text = EXCLUDED.help_text, "
        "unknown_label = EXCLUDED.unknown_label, "
        "decline_label = EXCLUDED.decline_label"
    )


def downgrade() -> None:
    op.execute("DELETE FROM need_localizations WHERE locale IN ('es', 'pt')")
    op.execute(
        "DELETE FROM attribute_option_localizations WHERE locale IN ('es', 'pt')"
    )
    op.execute("DELETE FROM question_localizations WHERE locale IN ('es', 'pt')")
    op.execute("UPDATE need_localizations SET locale = 'ar' WHERE locale = 'ary'")
    op.execute(
        "UPDATE attribute_option_localizations SET locale = 'ar' WHERE locale = 'ary'"
    )
    op.execute("UPDATE question_localizations SET locale = 'ar' WHERE locale = 'ary'")
    # Existing de/fr/en wording remains improved after downgrade.
