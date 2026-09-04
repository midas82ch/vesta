"""Add victim support, safe dialogue routing and reviewed URL imports.

Revision ID: 20260902_0012
Revises: 20260901_0011
Create Date: 2026-09-02
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260902_0012"
down_revision: str | None = "20260901_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NEED_VICTIM_SUPPORT = "00000000-0000-0000-0001-000000000004"
ATTR_IS_ADULT = "00000000-0000-0000-0002-000000000005"
ATTR_IMMEDIATE_DANGER = "00000000-0000-0000-0002-000000000006"
QUESTION_IS_ADULT = "00000000-0000-0000-0004-000000000005"
QUESTION_IMMEDIATE_DANGER = "00000000-0000-0000-0004-000000000006"


def upgrade() -> None:
    op.execute(
        "ALTER TABLE ai_interaction_log DROP CONSTRAINT IF EXISTS "
        "ai_interaction_log_port_check"
    )
    op.execute(
        """
        ALTER TABLE ai_interaction_log
        ADD CONSTRAINT ai_interaction_log_port_check
        CHECK (port IN (
            'interpret', 'render_question', 'explain',
            'offer_import_extract', 'offer_import_translate'
        ))
        """
    )
    op.execute(
        f"""
        INSERT INTO need_definitions (id, key, status, sort_order, icon)
        VALUES ('{NEED_VICTIM_SUPPORT}', 'victim_support', 'draft', 4, 'support')
        ON CONFLICT (key) DO UPDATE SET
            icon = EXCLUDED.icon,
            sort_order = EXCLUDED.sort_order
        """
    )
    op.execute(
        f"""
        INSERT INTO need_localizations (need_id, locale, title, description)
        VALUES
          ('{NEED_VICTIM_SUPPORT}', 'de', 'Opferhilfe',
           'Hilfe nach Gewalt, Drohungen oder einer Straftat'),
          ('{NEED_VICTIM_SUPPORT}', 'fr', 'Aide aux victimes',
           'Aide après des violences, des menaces ou une infraction'),
          ('{NEED_VICTIM_SUPPORT}', 'en', 'Victim support',
           'Help after violence, threats or a crime'),
          ('{NEED_VICTIM_SUPPORT}', 'es', 'Ayuda a víctimas',
           'Ayuda tras violencia, amenazas o un delito'),
          ('{NEED_VICTIM_SUPPORT}', 'pt', 'Apoio à vítima',
           'Ajuda após violência, ameaças ou um crime'),
          ('{NEED_VICTIM_SUPPORT}', 'ary', 'مساعدة الضحايا',
           'مساعدة من بعد العنف، التهديد ولا شي جريمة')
        ON CONFLICT (need_id, locale) DO UPDATE SET
            title = EXCLUDED.title,
            description = EXCLUDED.description
        """
    )

    op.execute(
        f"""
        INSERT INTO attribute_definitions (
            id, key, value_type, confirmation_required, skippable, status
        ) VALUES
          ('{ATTR_IS_ADULT}', 'person.is_adult', 'boolean', true, true, 'published'),
          ('{ATTR_IMMEDIATE_DANGER}', 'safety.immediate_danger',
           'boolean', true, true, 'published')
        ON CONFLICT (key) DO NOTHING
        """
    )
    op.execute(
        "UPDATE attribute_definitions SET status = 'archived' WHERE key = 'person.age'"
    )
    op.execute(
        "UPDATE question_definitions SET status = 'archived' WHERE key = 'sleep.age'"
    )
    op.execute(
        "UPDATE question_definitions SET key = 'access.has_identity_document' "
        "WHERE key = 'sleep.has_identity_document'"
    )
    op.execute(
        f"""
        INSERT INTO question_definitions (
            id, key, attribute_definition_id, answer_type, priority,
            ai_rephrasing_allowed, status
        ) VALUES
          ('{QUESTION_IS_ADULT}', 'access.is_adult', '{ATTR_IS_ADULT}',
           'yes_no_unknown', 40, true, 'published'),
          ('{QUESTION_IMMEDIATE_DANGER}', 'safety.immediate_danger',
           '{ATTR_IMMEDIATE_DANGER}', 'yes_no_unknown', 1, false, 'published')
        ON CONFLICT (key) DO NOTHING
        """
    )
    op.execute(
        f"""
        INSERT INTO question_localizations (
            question_id, locale, canonical_text, help_text,
            unknown_label, decline_label
        ) VALUES
          ('{QUESTION_IS_ADULT}', 'de',
           'Ist die Person, für die Sie Hilfe suchen, 18 Jahre oder älter?',
           'Einige Angebote sind nur für volljährige Personen zugänglich.',
           'Weiss ich nicht', 'Möchte ich nicht angeben'),
          ('{QUESTION_IS_ADULT}', 'fr',
           'La personne pour laquelle vous cherchez de l''aide a-t-elle 18 ans ou plus ?',
           'Certaines offres sont réservées aux personnes majeures.',
           'Je ne sais pas', 'Je préfère ne pas l''indiquer'),
          ('{QUESTION_IS_ADULT}', 'en',
           'Is the person you are seeking help for 18 or older?',
           'Some services are only available to adults.',
           'I don''t know', 'Prefer not to say'),
          ('{QUESTION_IS_ADULT}', 'es',
           '¿La persona para la que buscas ayuda tiene 18 años o más?',
           'Algunos servicios solo están disponibles para personas adultas.',
           'No lo sé', 'Prefiero no indicarlo'),
          ('{QUESTION_IS_ADULT}', 'pt',
           'A pessoa para quem procuras ajuda tem 18 anos ou mais?',
           'Alguns serviços destinam-se apenas a pessoas adultas.',
           'Não sei', 'Prefiro não indicar'),
          ('{QUESTION_IS_ADULT}', 'ary',
           'واش الشخص اللي كتقلب ليه على المساعدة عندو 18 عام ولا كثر؟',
           'شي خدمات مخصصين غير للناس الراشدين.',
           'ما عارفش', 'ما بغيتش نجاوب'),
          ('{QUESTION_IMMEDIATE_DANGER}', 'de',
           'Sind Sie gerade in unmittelbarer Gefahr?',
           'Wenn Sie akut bedroht oder verletzt sind, rufen Sie sofort Hilfe.',
           'Weiss ich nicht', 'Möchte ich nicht angeben'),
          ('{QUESTION_IMMEDIATE_DANGER}', 'fr',
           'Êtes-vous actuellement en danger immédiat ?',
           'Si vous êtes menacé·e ou blessé·e, appelez immédiatement les secours.',
           'Je ne sais pas', 'Je préfère ne pas l''indiquer'),
          ('{QUESTION_IMMEDIATE_DANGER}', 'en',
           'Are you in immediate danger right now?',
           'If you are being threatened or are injured, call for help immediately.',
           'I don''t know', 'Prefer not to say'),
          ('{QUESTION_IMMEDIATE_DANGER}', 'es',
           '¿Estás en peligro inmediato en este momento?',
           'Si estás amenazado o herido, llama inmediatamente a emergencias.',
           'No lo sé', 'Prefiero no indicarlo'),
          ('{QUESTION_IMMEDIATE_DANGER}', 'pt',
           'Estás em perigo imediato neste momento?',
           'Se estiveres sob ameaça ou ferido, liga imediatamente para a emergência.',
           'Não sei', 'Prefiro não indicar'),
          ('{QUESTION_IMMEDIATE_DANGER}', 'ary',
           'واش نتا دابا فخطر مباشر؟',
           'إلا كنت مهدد ولا مجروح، عيط للمساعدة دابا.',
           'ما عارفش', 'ما بغيتش نجاوب')
        ON CONFLICT (question_id, locale) DO UPDATE SET
            canonical_text = EXCLUDED.canonical_text,
            help_text = EXCLUDED.help_text,
            unknown_label = EXCLUDED.unknown_label,
            decline_label = EXCLUDED.decline_label
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS question_need_definitions (
            question_id UUID NOT NULL
                REFERENCES question_definitions(id) ON DELETE CASCADE,
            need_id UUID NOT NULL
                REFERENCES need_definitions(id) ON DELETE CASCADE,
            PRIMARY KEY (question_id, need_id)
        )
        """
    )
    op.execute(
        """
        INSERT INTO question_need_definitions (question_id, need_id)
        SELECT q.id, n.id
        FROM question_definitions q
        JOIN need_definitions n ON n.key = 'sleep_tonight'
        WHERE q.key IN ('sleep.has_dog', 'sleep.gender')
        ON CONFLICT DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO question_need_definitions (question_id, need_id)
        SELECT q.id, n.id
        FROM question_definitions q
        CROSS JOIN need_definitions n
        WHERE q.key IN ('access.has_identity_document', 'access.is_adult')
        ON CONFLICT DO NOTHING
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS offer_localizations (
            offer_id UUID NOT NULL REFERENCES offers(id) ON DELETE CASCADE,
            locale TEXT NOT NULL CHECK (locale IN ('de', 'fr', 'en', 'es', 'pt', 'ary')),
            name TEXT NOT NULL,
            summary TEXT NOT NULL,
            contact_note TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'machine_draft'
                CHECK (status IN ('machine_draft', 'reviewed')),
            revision INTEGER NOT NULL DEFAULT 1,
            reviewed_by UUID REFERENCES admin_users(id),
            reviewed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (offer_id, locale),
            CHECK (
                (status = 'reviewed' AND reviewed_at IS NOT NULL)
                OR status = 'machine_draft'
            )
        )
        """
    )
    op.execute(
        """
        INSERT INTO offer_localizations (
            offer_id, locale, name, summary, contact_note,
            status, reviewed_at, created_at, updated_at
        )
        SELECT id, 'de', name, summary, COALESCE(contact->>'note', ''),
               'reviewed', updated_at, created_at, updated_at
        FROM offers
        ON CONFLICT (offer_id, locale) DO NOTHING
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS offer_import_jobs (
            id UUID PRIMARY KEY,
            source_url TEXT NOT NULL,
            normalized_url TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN (
                'queued', 'fetching', 'extracting', 'translating',
                'ready_for_review', 'failed'
            )),
            requested_by UUID NOT NULL REFERENCES admin_users(id),
            offer_id UUID REFERENCES offers(id) ON DELETE SET NULL,
            source_language TEXT,
            content_sha256 TEXT,
            extracted_data JSONB,
            evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
            duplicate_offer_ids UUID[] NOT NULL DEFAULT '{}',
            error_code TEXT,
            error_detail TEXT,
            attempts INTEGER NOT NULL DEFAULT 0 CHECK (attempts BETWEEN 0 AND 3),
            lease_expires_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            started_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS offer_import_jobs_queue_idx "
        "ON offer_import_jobs (status, created_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS offer_import_jobs_url_idx "
        "ON offer_import_jobs (normalized_url, created_at DESC)"
    )

    op.execute(
        "ALTER TABLE admin_change_log DROP CONSTRAINT IF EXISTS "
        "admin_change_log_entity_type_check"
    )
    op.execute(
        """
        ALTER TABLE admin_change_log
        ADD CONSTRAINT admin_change_log_entity_type_check
        CHECK (entity_type IN (
            'category', 'offer', 'import_settings',
            'offer_import', 'offer_localization'
        ))
        """
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE ai_interaction_log DROP CONSTRAINT IF EXISTS "
        "ai_interaction_log_port_check"
    )
    op.execute(
        """
        ALTER TABLE ai_interaction_log
        ADD CONSTRAINT ai_interaction_log_port_check
        CHECK (port IN ('interpret', 'render_question', 'explain'))
        """
    )
    op.execute("DROP TABLE IF EXISTS offer_import_jobs")
    op.execute("DROP TABLE IF EXISTS offer_localizations")
    op.execute("DROP TABLE IF EXISTS question_need_definitions")
    op.execute(
        "ALTER TABLE admin_change_log DROP CONSTRAINT IF EXISTS "
        "admin_change_log_entity_type_check"
    )
    op.execute(
        """
        ALTER TABLE admin_change_log
        ADD CONSTRAINT admin_change_log_entity_type_check
        CHECK (entity_type IN ('category', 'offer', 'import_settings'))
        """
    )
    op.execute(
        f"DELETE FROM question_definitions WHERE id IN "
        f"('{QUESTION_IS_ADULT}', '{QUESTION_IMMEDIATE_DANGER}')"
    )
    op.execute(
        f"DELETE FROM attribute_definitions WHERE id IN "
        f"('{ATTR_IS_ADULT}', '{ATTR_IMMEDIATE_DANGER}')"
    )
    op.execute(
        "UPDATE attribute_definitions SET status = 'published' WHERE key = 'person.age'"
    )
    op.execute(
        "UPDATE question_definitions SET status = 'published' WHERE key = 'sleep.age'"
    )
    op.execute(
        "UPDATE question_definitions SET key = 'sleep.has_identity_document' "
        "WHERE key = 'access.has_identity_document'"
    )
    op.execute(f"DELETE FROM need_definitions WHERE id = '{NEED_VICTIM_SUPPORT}'")
