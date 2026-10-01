"""Add precise service choices, provider approval and verification grace.

Revision ID: 20261001_0014
Revises: 20260904_0013
Create Date: 2026-10-01
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20261001_0014"
down_revision: str | None = "20260904_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE attribute_definitions
        DROP CONSTRAINT IF EXISTS attribute_definitions_value_type_check;
        ALTER TABLE attribute_definitions
        ADD CONSTRAINT attribute_definitions_value_type_check
        CHECK (value_type IN ('boolean', 'integer', 'enum', 'multi_enum'));

        ALTER TABLE question_definitions
        DROP CONSTRAINT IF EXISTS question_definitions_answer_type_check;
        ALTER TABLE question_definitions
        ADD CONSTRAINT question_definitions_answer_type_check
        CHECK (answer_type IN (
            'yes_no_unknown', 'single_choice', 'multi_choice', 'number'
        ));

        ALTER TABLE question_definitions
            ADD COLUMN IF NOT EXISTS presentation TEXT NOT NULL DEFAULT 'list',
            ADD COLUMN IF NOT EXISTS selection_mode TEXT NOT NULL DEFAULT 'single',
            ADD COLUMN IF NOT EXISTS minimum_selections INTEGER NOT NULL DEFAULT 1;
        ALTER TABLE question_definitions
        DROP CONSTRAINT IF EXISTS question_definitions_presentation_check;
        ALTER TABLE question_definitions
        ADD CONSTRAINT question_definitions_presentation_check
        CHECK (presentation IN ('list', 'icon_grid'));
        ALTER TABLE question_definitions
        DROP CONSTRAINT IF EXISTS question_definitions_selection_mode_check;
        ALTER TABLE question_definitions
        ADD CONSTRAINT question_definitions_selection_mode_check
        CHECK (selection_mode IN ('single', 'multiple'));
        ALTER TABLE question_definitions
        DROP CONSTRAINT IF EXISTS question_definitions_minimum_selections_check;
        ALTER TABLE question_definitions
        ADD CONSTRAINT question_definitions_minimum_selections_check
        CHECK (minimum_selections BETWEEN 0 AND 20);

        ALTER TABLE attribute_options
        ADD COLUMN IF NOT EXISTS icon TEXT NOT NULL DEFAULT 'other';

        ALTER TABLE need_definitions
        DROP CONSTRAINT IF EXISTS need_definitions_icon_check;
        ALTER TABLE need_definitions
        ADD CONSTRAINT need_definitions_icon_check
        CHECK (icon IN (
            'home', 'food', 'book', 'health', 'clothing',
            'shower', 'support', 'daytime', 'other'
        ));
        """
    )

    op.execute(
        """
        INSERT INTO need_definitions (id, key, status, sort_order, icon)
        VALUES (
            md5('need:daytime_stay')::uuid,
            'daytime_stay', 'published', 5, 'daytime'
        )
        ON CONFLICT (key) DO UPDATE SET
            status = 'published', sort_order = 5, icon = 'daytime';

        INSERT INTO need_localizations (need_id, locale, title, description)
        SELECT n.id, value.locale, value.title, value.description
        FROM need_definitions n
        CROSS JOIN (VALUES
            ('de', 'Aufenthalt & Toilette',
             'Ein Ort zum Verweilen ohne Konsumzwang und mit Toilette'),
            ('fr', 'Lieu d’accueil et toilettes',
             'Un lieu où rester sans obligation de consommer, avec des toilettes'),
            ('en', 'Daytime space & toilet',
             'A place to stay without having to buy anything, with a toilet'),
            ('es', 'Espacio de estancia y aseo',
             'Un lugar donde estar sin obligación de consumir, con aseo'),
            ('pt', 'Espaço de permanência e casa de banho',
             'Um local onde ficar sem obrigação de consumir, com casa de banho'),
            ('ary', 'بلاصة ترتاح فيها',
             'بلاصة تبقى فيها بلا ما تشري شي حاجة ومع مرحاض')
        ) AS value(locale, title, description)
        WHERE n.key = 'daytime_stay'
        ON CONFLICT (need_id, locale) DO UPDATE SET
            title = EXCLUDED.title,
            description = EXCLUDED.description;
        """
    )

    op.execute(
        """
        CREATE TABLE service_definitions (
            key TEXT PRIMARY KEY,
            service_group TEXT NOT NULL CHECK (
                service_group IN ('basic_needs', 'counselling', 'addiction')
            ),
            icon TEXT NOT NULL,
            sort_order INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'published'
                CHECK (status IN ('draft', 'published', 'archived')),
            revision INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE TABLE service_localizations (
            service_key TEXT NOT NULL
                REFERENCES service_definitions(key) ON UPDATE CASCADE ON DELETE CASCADE,
            locale TEXT NOT NULL CHECK (locale IN ('de', 'fr', 'en', 'es', 'pt', 'ary')),
            label TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            PRIMARY KEY (service_key, locale)
        );
        CREATE TABLE offer_services (
            offer_id UUID NOT NULL REFERENCES offers(id) ON DELETE CASCADE,
            service_key TEXT NOT NULL
                REFERENCES service_definitions(key) ON UPDATE CASCADE ON DELETE RESTRICT,
            status TEXT NOT NULL DEFAULT 'confirmed'
                CHECK (status IN ('draft', 'confirmed')),
            evidence_url TEXT,
            evidence_note TEXT,
            verified_at TIMESTAMPTZ,
            PRIMARY KEY (offer_id, service_key)
        );
        CREATE INDEX offer_services_service_idx
            ON offer_services (service_key, status, offer_id);

        CREATE TABLE provider_approvals (
            offer_id UUID PRIMARY KEY REFERENCES offers(id) ON DELETE CASCADE,
            status TEXT NOT NULL CHECK (
                status IN ('legacy_pending', 'pending', 'approved', 'declined')
            ),
            contact_reference TEXT,
            scope_note TEXT,
            approved_at TIMESTAMPTZ,
            approved_by UUID REFERENCES admin_users(id),
            decision_evidence TEXT,
            legacy_deadline TIMESTAMPTZ,
            revision INTEGER NOT NULL DEFAULT 1,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CHECK (
                status <> 'approved'
                OR (approved_at IS NOT NULL AND scope_note IS NOT NULL)
            )
        );
        CREATE TABLE offer_source_revisions (
            id UUID PRIMARY KEY,
            offer_id UUID NOT NULL REFERENCES offers(id) ON DELETE CASCADE,
            source_url TEXT NOT NULL,
            content_sha256 TEXT NOT NULL,
            extracted_data JSONB NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending_review'
                CHECK (status IN ('pending_review', 'accepted', 'rejected')),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            reviewed_at TIMESTAMPTZ,
            reviewed_by UUID REFERENCES admin_users(id),
            UNIQUE (offer_id, content_sha256)
        );
        CREATE INDEX offer_source_revisions_review_idx
            ON offer_source_revisions (status, created_at DESC);
        INSERT INTO provider_approvals (offer_id, status, legacy_deadline)
        SELECT id, 'legacy_pending', now() + interval '90 days'
        FROM offers
        ON CONFLICT (offer_id) DO NOTHING;
        """
    )

    services = (
        ("meal", "basic_needs", "meal", 1),
        ("groceries", "basic_needs", "groceries", 2),
        ("shower", "basic_needs", "shower", 3),
        ("laundry", "basic_needs", "laundry", 4),
        ("clothing", "basic_needs", "clothing", 5),
        ("toilet", "basic_needs", "toilet", 6),
        ("locker", "basic_needs", "locker", 7),
        ("general_social", "counselling", "chat", 1),
        ("housing", "counselling", "housing", 2),
        ("finances", "counselling", "wallet", 3),
        ("health", "counselling", "health", 4),
        ("mental_health", "counselling", "mental-health", 5),
        ("legal", "counselling", "legal", 6),
        ("addiction", "counselling", "support", 7),
        ("addiction_alcohol", "addiction", "alcohol", 1),
        ("addiction_opioids", "addiction", "medication", 2),
        ("addiction_other", "addiction", "substances", 3),
        ("addiction_multiple", "addiction", "multiple", 4),
        ("addiction_unsure", "addiction", "question", 5),
        ("daytime_no_purchase", "basic_needs", "daytime", 8),
    )
    values = ",\n".join(
        "("
        + ", ".join(
            "'" + str(value).replace("'", "''") + "'" if not isinstance(value, int) else str(value)
            for value in row
        )
        + ")"
        for row in services
    )
    op.execute(
        f"""
        INSERT INTO service_definitions (key, service_group, icon, sort_order)
        VALUES {values}
        ON CONFLICT (key) DO UPDATE SET
            service_group = EXCLUDED.service_group,
            icon = EXCLUDED.icon,
            sort_order = EXCLUDED.sort_order;
        """
    )

    translations = {
        "meal": ("Mahlzeit", "Repas", "Meal", "Comida preparada", "Refeição", "وجبة"),
        "groceries": (
            "Lebensmittel",
            "Aliments",
            "Groceries",
            "Alimentos",
            "Alimentos",
            "مواد غذائية",
        ),
        "shower": ("Dusche", "Douche", "Shower", "Ducha", "Duche", "دوش"),
        "laundry": (
            "Wäsche waschen",
            "Laver le linge",
            "Laundry",
            "Lavar la ropa",
            "Lavar roupa",
            "تصبين الحوايج",
        ),
        "clothing": ("Kleidung", "Vêtements", "Clothing", "Ropa", "Roupa", "حوايج"),
        "toilet": ("Toilette", "Toilettes", "Toilet", "Aseo", "Casa de banho", "مرحاض"),
        "locker": ("Schliessfach", "Casier", "Locker", "Taquilla", "Cacifo", "خزانة"),
        "general_social": (
            "Allgemeine Sozialberatung",
            "Conseil social général",
            "General social advice",
            "Asesoramiento social general",
            "Aconselhamento social geral",
            "نصيحة اجتماعية",
        ),
        "housing": ("Wohnen", "Logement", "Housing", "Vivienda", "Habitação", "السكن"),
        "finances": (
            "Geld und Schulden",
            "Argent et dettes",
            "Money and debt",
            "Dinero y deudas",
            "Dinheiro e dívidas",
            "الفلوس والديون",
        ),
        "health": ("Gesundheit", "Santé", "Health", "Salud", "Saúde", "الصحة"),
        "mental_health": (
            "Psychische Belastung",
            "Difficultés psychiques",
            "Mental distress",
            "Malestar psicológico",
            "Sofrimento psicológico",
            "الضغط النفسي",
        ),
        "legal": (
            "Recht",
            "Droit",
            "Legal matters",
            "Asuntos legales",
            "Assuntos jurídicos",
            "القانون",
        ),
        "addiction": ("Sucht", "Dépendance", "Addiction", "Adicciones", "Dependências", "الإدمان"),
        "addiction_alcohol": ("Alkohol", "Alcool", "Alcohol", "Alcohol", "Álcool", "الكحول"),
        "addiction_opioids": (
            "Opioide / Heroin",
            "Opioïdes / héroïne",
            "Opioids / heroin",
            "Opioides / heroína",
            "Opioides / heroína",
            "الأفيونات / الهيروين",
        ),
        "addiction_other": (
            "Andere Substanzen",
            "Autres substances",
            "Other substances",
            "Otras sustancias",
            "Outras substâncias",
            "مخدرات أخرى",
        ),
        "addiction_multiple": (
            "Mehrere Substanzen",
            "Plusieurs substances",
            "Multiple substances",
            "Varias sustancias",
            "Várias substâncias",
            "بزاف ديال المواد",
        ),
        "addiction_unsure": (
            "Nicht sicher",
            "Je ne sais pas",
            "Not sure",
            "No lo sé",
            "Não tenho a certeza",
            "ما متأكدش",
        ),
        "daytime_no_purchase": (
            "Aufenthalt ohne Konsumzwang",
            "Accueil sans obligation de consommer",
            "Stay without buying anything",
            "Estancia sin obligación de consumir",
            "Permanência sem obrigação de consumir",
            "بلاصة بلا ما تشري شي حاجة",
        ),
    }
    locale_order = ("de", "fr", "en", "es", "pt", "ary")
    localized_rows = []
    for key, labels in translations.items():
        for locale, label in zip(locale_order, labels, strict=True):
            escaped_label = label.replace("'", "''")
            localized_rows.append(f"('{key}', '{locale}', '{escaped_label}')")
    op.execute(
        "INSERT INTO service_localizations (service_key, locale, label) VALUES\n"
        + ",\n".join(localized_rows)
        + " ON CONFLICT (service_key, locale) DO UPDATE SET label = EXCLUDED.label"
    )

    op.execute(
        """
        INSERT INTO attribute_definitions (
            id, key, value_type, confirmation_required, skippable, status
        ) VALUES
            (md5('attribute:request.services.basic')::uuid,
             'request.services.basic', 'multi_enum', true, true, 'published'),
            (md5('attribute:request.services.counselling')::uuid,
             'request.services.counselling', 'multi_enum', true, true, 'published'),
            (md5('attribute:request.services.addiction')::uuid,
             'request.services.addiction', 'multi_enum', true, true, 'published')
        ON CONFLICT (key) DO UPDATE SET status = 'published';

        INSERT INTO attribute_options (id, attribute_id, value, sort_order, icon)
        SELECT md5('option:' || a.key || ':' || s.key)::uuid,
               a.id, s.key, s.sort_order, s.icon
        FROM attribute_definitions a
        JOIN service_definitions s ON (
            (a.key = 'request.services.basic' AND s.service_group = 'basic_needs'
                AND s.key <> 'daytime_no_purchase')
            OR (a.key = 'request.services.counselling' AND s.service_group = 'counselling')
            OR (a.key = 'request.services.addiction' AND s.service_group = 'addiction')
        )
        ON CONFLICT (attribute_id, value) DO UPDATE SET
            sort_order = EXCLUDED.sort_order,
            icon = EXCLUDED.icon;

        INSERT INTO attribute_option_localizations (option_id, locale, label)
        SELECT ao.id, sl.locale, sl.label
        FROM attribute_options ao
        JOIN service_localizations sl ON sl.service_key = ao.value
        WHERE ao.attribute_id IN (
            SELECT id FROM attribute_definitions
            WHERE key LIKE 'request.services.%'
        )
        ON CONFLICT (option_id, locale) DO UPDATE SET label = EXCLUDED.label;

        INSERT INTO question_definitions (
            id, key, attribute_definition_id, answer_type, priority,
            ai_rephrasing_allowed, status, presentation, selection_mode,
            minimum_selections
        ) VALUES
            (md5('question:basic.services')::uuid, 'basic.services',
             md5('attribute:request.services.basic')::uuid,
             'multi_choice', 1, false, 'published', 'icon_grid', 'multiple', 1),
            (md5('question:counselling.services')::uuid, 'counselling.services',
             md5('attribute:request.services.counselling')::uuid,
             'multi_choice', 1, false, 'published', 'icon_grid', 'multiple', 1),
            (md5('question:counselling.addiction')::uuid, 'counselling.addiction',
             md5('attribute:request.services.addiction')::uuid,
             'multi_choice', 2, false, 'published', 'icon_grid', 'multiple', 1)
        ON CONFLICT (key) DO UPDATE SET
            answer_type = EXCLUDED.answer_type,
            priority = EXCLUDED.priority,
            ai_rephrasing_allowed = false,
            status = 'published',
            presentation = 'icon_grid',
            selection_mode = 'multiple',
            minimum_selections = 1;

        INSERT INTO question_need_definitions (question_id, need_id)
        SELECT q.id, n.id
        FROM question_definitions q
        JOIN need_definitions n ON (
            (q.key = 'basic.services' AND n.key = 'basic_needs')
            OR (q.key IN ('counselling.services', 'counselling.addiction')
                AND n.key = 'counselling')
        )
        WHERE q.key IN ('basic.services', 'counselling.services', 'counselling.addiction')
        ON CONFLICT DO NOTHING;

        UPDATE attribute_definitions
        SET status = 'published'
        WHERE key = 'person.age';
        UPDATE question_definitions
        SET key = 'access.age', status = 'published', priority = 40,
            ai_rephrasing_allowed = false, answer_type = 'number',
            presentation = 'list', selection_mode = 'single', minimum_selections = 1
        WHERE key = 'sleep.age';
        UPDATE question_definitions SET status = 'archived'
        WHERE key = 'access.is_adult';
        DELETE FROM question_need_definitions
        WHERE question_id = (SELECT id FROM question_definitions WHERE key = 'access.age');
        INSERT INTO question_need_definitions (question_id, need_id)
        SELECT q.id, n.id FROM question_definitions q, need_definitions n
        WHERE q.key = 'access.age' AND n.key = 'sleep_tonight'
        ON CONFLICT DO NOTHING;
        """
    )

    question_texts = {
        "basic.services": (
            (
                "de",
                "Was brauchst du?",
                "Du kannst mehrere Dinge auswählen.",
                "Weiss ich nicht",
                "Überspringen",
            ),
            (
                "fr",
                "De quoi as-tu besoin ?",
                "Tu peux choisir plusieurs éléments.",
                "Je ne sais pas",
                "Passer",
            ),
            ("en", "What do you need?", "You can choose more than one.", "I don't know", "Skip"),
            ("es", "¿Qué necesitas?", "Puedes elegir varias opciones.", "No lo sé", "Omitir"),
            ("pt", "Do que precisas?", "Podes escolher várias opções.", "Não sei", "Ignorar"),
            ("ary", "شنو محتاج؟", "تقدر تختار كثر من حاجة.", "ما عارفش", "دوز"),
        ),
        "counselling.services": (
            (
                "de",
                "Wobei brauchst du Unterstützung?",
                "Du kannst mehrere Themen auswählen.",
                "Weiss ich nicht",
                "Überspringen",
            ),
            (
                "fr",
                "Pour quoi as-tu besoin de soutien ?",
                "Tu peux choisir plusieurs thèmes.",
                "Je ne sais pas",
                "Passer",
            ),
            (
                "en",
                "What do you need support with?",
                "You can choose more than one topic.",
                "I don't know",
                "Skip",
            ),
            (
                "es",
                "¿Con qué necesitas apoyo?",
                "Puedes elegir varios temas.",
                "No lo sé",
                "Omitir",
            ),
            (
                "pt",
                "Em que precisas de apoio?",
                "Podes escolher vários temas.",
                "Não sei",
                "Ignorar",
            ),
            ("ary", "فاش محتاج المساعدة؟", "تقدر تختار كثر من موضوع.", "ما عارفش", "دوز"),
        ),
        "counselling.addiction": (
            (
                "de",
                "Worum geht es bei der Sucht?",
                "Wähle aus, was am besten passt.",
                "Weiss ich nicht",
                "Überspringen",
            ),
            (
                "fr",
                "De quelle dépendance s’agit-il ?",
                "Choisis ce qui correspond le mieux.",
                "Je ne sais pas",
                "Passer",
            ),
            (
                "en",
                "What kind of addiction is it?",
                "Choose what fits best.",
                "I don't know",
                "Skip",
            ),
            (
                "es",
                "¿De qué adicción se trata?",
                "Elige lo que mejor corresponda.",
                "No lo sé",
                "Omitir",
            ),
            (
                "pt",
                "De que dependência se trata?",
                "Escolhe o que corresponde melhor.",
                "Não sei",
                "Ignorar",
            ),
            ("ary", "على شنو داير الإدمان؟", "اختار شنو كيناسب كثر.", "ما عارفش", "دوز"),
        ),
    }
    rows = []
    for question_key, translations_for_question in question_texts.items():
        for locale, text_value, help_text, unknown, decline in translations_for_question:
            escaped = tuple(
                value.replace("'", "''")
                for value in (question_key, locale, text_value, help_text, unknown, decline)
            )
            rows.append(
                "((SELECT id FROM question_definitions WHERE key = '"
                + escaped[0]
                + "'), '"
                + "', '".join(escaped[1:])
                + "')"
            )
    op.execute(
        "INSERT INTO question_localizations "
        "(question_id, locale, canonical_text, help_text, unknown_label, decline_label) VALUES\n"
        + ",\n".join(rows)
        + " ON CONFLICT (question_id, locale) DO UPDATE SET "
        "canonical_text = EXCLUDED.canonical_text, help_text = EXCLUDED.help_text, "
        "unknown_label = EXCLUDED.unknown_label, decline_label = EXCLUDED.decline_label"
    )

    op.execute(
        """
        UPDATE question_localizations ql
        SET canonical_text = CASE ql.locale
                WHEN 'de' THEN 'Wie alt ist die Person, für die du Hilfe suchst?'
                WHEN 'fr' THEN 'Quel âge a la personne pour laquelle tu cherches de l’aide ?'
                WHEN 'en' THEN 'How old is the person you are seeking help for?'
                WHEN 'es' THEN '¿Qué edad tiene la persona para la que buscas ayuda?'
                WHEN 'pt' THEN 'Que idade tem a pessoa para quem procuras ajuda?'
                WHEN 'ary' THEN 'شحال فعمر الشخص اللي كتقلب ليه على المساعدة؟'
                ELSE ql.canonical_text
            END,
            help_text = CASE ql.locale
                WHEN 'de' THEN 'Das Alter wird nur für diese Suche verwendet und nicht gespeichert.'
                WHEN 'fr' THEN 'L’âge sert uniquement à cette recherche et n’est pas enregistré.'
                WHEN 'en' THEN 'The age is used only for this search and is not stored.'
                WHEN 'es' THEN 'La edad solo se utiliza para esta búsqueda y no se guarda.'
                WHEN 'pt' THEN 'A idade é usada apenas para esta pesquisa e não é guardada.'
                WHEN 'ary' THEN 'العمر كيتستعمل غير فهاد البحث وما كيتخزنش.'
                ELSE ql.help_text
            END
        FROM question_definitions q
        WHERE ql.question_id = q.id AND q.key = 'access.age';

        INSERT INTO offer_services (
            offer_id, service_key, status, evidence_url, evidence_note, verified_at
        )
        SELECT o.id, values.service_key, 'confirmed', v.source_url,
               'Initiale Zuordnung aus dem geprüften Angebotskatalog', v.verified_at
        FROM offers o
        JOIN LATERAL (
            SELECT source_url, verified_at FROM offer_verifications
            WHERE offer_id = o.id ORDER BY verified_at DESC LIMIT 1
        ) v ON TRUE
        JOIN (VALUES
            ('contact-la-gare-bern', 'meal'),
            ('contact-la-gare-bern', 'addiction'),
            ('contact-la-gare-bern', 'addiction_alcohol'),
            ('wohnberatung-bern', 'housing'),
            ('hope-point-bern', 'general_social'),
            ('contact-suchtbehandlung-bern', 'addiction'),
            ('contact-suchtbehandlung-bern', 'addiction_alcohol'),
            ('contact-suchtbehandlung-bern', 'addiction_opioids'),
            ('contact-suchtbehandlung-bern', 'addiction_other'),
            ('contact-suchtbehandlung-bern', 'addiction_multiple'),
            ('contact-anlaufstelle-bern', 'addiction'),
            ('opferhilfe-schweiz-142', 'general_social'),
            ('opferhilfe-bern', 'general_social')
        ) AS values(slug, service_key) ON values.slug = o.slug
        ON CONFLICT (offer_id, service_key) DO NOTHING;

        DELETE FROM offer_categories oc
        USING offers o
        WHERE oc.offer_id = o.id
          AND oc.category = 'basic_needs'
          AND o.slug IN ('contact-anlaufstelle-bern', 'hope-point-bern');

        INSERT INTO offer_services (
            offer_id, service_key, status, evidence_url, evidence_note, verified_at
        )
        SELECT o.id, 'general_social', 'confirmed', v.source_url,
               'Kirchliche Gassenarbeit: allgemeine aufsuchende Sozialberatung',
               v.verified_at
        FROM offers o
        JOIN LATERAL (
            SELECT source_url, verified_at FROM offer_verifications
            WHERE offer_id = o.id ORDER BY verified_at DESC LIMIT 1
        ) v ON TRUE
        WHERE o.slug ILIKE '%gassenarbeit%'
        ON CONFLICT (offer_id, service_key) DO NOTHING;

        UPDATE offers
        SET access_rules = (access_rules - 'minimum_age' - 'maximum_age')
            || '{"minimum_age": null, "maximum_age": null}'::jsonb,
            languages = ARRAY['de', 'fr', 'it', 'en', 'es']::text[]
        WHERE slug ILIKE '%gassenarbeit%';

        UPDATE offers
        SET access_rules = (access_rules - 'minimum_age' - 'maximum_age')
            || '{"minimum_age": 14, "maximum_age": 23}'::jsonb
        WHERE name ILIKE '%Pluto%' OR slug ILIKE '%pluto%';

        ALTER TABLE admin_change_log
        DROP CONSTRAINT IF EXISTS admin_change_log_entity_type_check;
        ALTER TABLE admin_change_log
        ADD CONSTRAINT admin_change_log_entity_type_check
        CHECK (entity_type IN (
            'category', 'offer', 'import_settings', 'offer_import',
            'offer_localization', 'service_definition', 'provider_approval'
        ));
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE admin_change_log
        DROP CONSTRAINT IF EXISTS admin_change_log_entity_type_check;
        ALTER TABLE admin_change_log
        ADD CONSTRAINT admin_change_log_entity_type_check
        CHECK (entity_type IN (
            'category', 'offer', 'import_settings',
            'offer_import', 'offer_localization'
        ));
        DROP TABLE IF EXISTS offer_source_revisions;
        DROP TABLE IF EXISTS provider_approvals;
        DROP TABLE IF EXISTS offer_services;
        DROP TABLE IF EXISTS service_localizations;
        DROP TABLE IF EXISTS service_definitions;
        DELETE FROM question_definitions
        WHERE key IN ('basic.services', 'counselling.services', 'counselling.addiction');
        DELETE FROM attribute_definitions
        WHERE key IN (
            'request.services.basic',
            'request.services.counselling',
            'request.services.addiction'
        );
        UPDATE question_definitions SET key = 'sleep.age', status = 'archived'
        WHERE key = 'access.age';
        UPDATE attribute_definitions SET status = 'archived'
        WHERE key = 'person.age';
        UPDATE question_definitions SET status = 'published'
        WHERE key = 'access.is_adult';
        DELETE FROM need_definitions WHERE key = 'daytime_stay';
        ALTER TABLE attribute_options DROP COLUMN IF EXISTS icon;
        ALTER TABLE question_definitions
            DROP COLUMN IF EXISTS presentation,
            DROP COLUMN IF EXISTS selection_mode,
            DROP COLUMN IF EXISTS minimum_selections;
        ALTER TABLE question_definitions
        DROP CONSTRAINT IF EXISTS question_definitions_answer_type_check;
        ALTER TABLE question_definitions
        ADD CONSTRAINT question_definitions_answer_type_check
        CHECK (answer_type IN ('yes_no_unknown', 'single_choice', 'number'));
        ALTER TABLE attribute_definitions
        DROP CONSTRAINT IF EXISTS attribute_definitions_value_type_check;
        ALTER TABLE attribute_definitions
        ADD CONSTRAINT attribute_definitions_value_type_check
        CHECK (value_type IN ('boolean', 'integer', 'enum'));
        """
    )
