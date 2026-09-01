"""Add the administrable offer catalog and import control.

Revision ID: 20260901_0011
Revises: 20260817_0010
Create Date: 2026-09-01
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260901_0011"
down_revision: str | None = "20260817_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE need_definitions
            ADD COLUMN IF NOT EXISTS icon TEXT NOT NULL DEFAULT 'other',
            ADD COLUMN IF NOT EXISTS revision INTEGER NOT NULL DEFAULT 1,
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        """
    )
    op.execute(
        """
        UPDATE need_definitions
        SET icon = CASE key
            WHEN 'sleep_tonight' THEN 'home'
            WHEN 'basic_needs' THEN 'food'
            WHEN 'counselling' THEN 'book'
            ELSE icon
        END
        """
    )
    op.execute(
        """
        ALTER TABLE need_definitions
        DROP CONSTRAINT IF EXISTS need_definitions_status_check
        """
    )
    op.execute(
        """
        ALTER TABLE need_definitions
        ADD CONSTRAINT need_definitions_status_check
        CHECK (status IN ('draft', 'published', 'archived'))
        """
    )
    op.execute(
        """
        ALTER TABLE need_definitions
        DROP CONSTRAINT IF EXISTS need_definitions_icon_check
        """
    )
    op.execute(
        """
        ALTER TABLE need_definitions
        ADD CONSTRAINT need_definitions_icon_check
        CHECK (icon IN (
            'home', 'food', 'book', 'health', 'clothing',
            'shower', 'support', 'other'
        ))
        """
    )

    op.execute(
        """
        ALTER TABLE offers
            ADD COLUMN IF NOT EXISTS origin TEXT NOT NULL DEFAULT 'imported',
            ADD COLUMN IF NOT EXISTS management_mode TEXT NOT NULL DEFAULT 'source',
            ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ,
            ADD COLUMN IF NOT EXISTS revision INTEGER NOT NULL DEFAULT 1
        """
    )
    op.execute(
        """
        ALTER TABLE offers
        DROP CONSTRAINT IF EXISTS offers_origin_check
        """
    )
    op.execute(
        """
        ALTER TABLE offers
        ADD CONSTRAINT offers_origin_check
        CHECK (origin IN ('imported', 'manual'))
        """
    )
    op.execute(
        """
        ALTER TABLE offers
        DROP CONSTRAINT IF EXISTS offers_management_mode_check
        """
    )
    op.execute(
        """
        ALTER TABLE offers
        ADD CONSTRAINT offers_management_mode_check
        CHECK (management_mode IN ('source', 'manual'))
        """
    )

    op.execute(
        """
        ALTER TABLE offer_categories
        DROP CONSTRAINT IF EXISTS offer_categories_category_fkey
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS offer_categories_category_idx
        ON offer_categories (category)
        """
    )
    op.execute(
        """
        ALTER TABLE offer_categories
        ADD CONSTRAINT offer_categories_category_fkey
        FOREIGN KEY (category) REFERENCES need_definitions(key)
        ON UPDATE CASCADE ON DELETE RESTRICT
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS offer_import_settings (
            id SMALLINT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
            automatic_enabled BOOLEAN NOT NULL DEFAULT true,
            revision INTEGER NOT NULL DEFAULT 1,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_by UUID REFERENCES admin_users(id)
        )
        """
    )
    op.execute(
        """
        INSERT INTO offer_import_settings (id, automatic_enabled)
        VALUES (1, true)
        ON CONFLICT (id) DO NOTHING
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS admin_change_log (
            id UUID PRIMARY KEY,
            admin_user_id UUID NOT NULL REFERENCES admin_users(id),
            admin_username TEXT NOT NULL,
            entity_type TEXT NOT NULL CHECK (
                entity_type IN ('category', 'offer', 'import_settings')
            ),
            entity_id TEXT NOT NULL,
            action TEXT NOT NULL,
            before_data JSONB,
            after_data JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS admin_change_log_entity_created_idx
        ON admin_change_log (entity_type, entity_id, created_at DESC)
        """
    )

    op.execute(
        """
        ALTER TABLE offer_ingestion_runs
        DROP CONSTRAINT IF EXISTS offer_ingestion_runs_status_check
        """
    )
    op.execute(
        """
        ALTER TABLE offer_ingestion_runs
        ADD CONSTRAINT offer_ingestion_runs_status_check
        CHECK (status IN (
            'imported', 'evidence_missing', 'fetch_failed', 'skipped_disabled'
        ))
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE offer_ingestion_runs
        DROP CONSTRAINT IF EXISTS offer_ingestion_runs_status_check
        """
    )
    op.execute(
        """
        ALTER TABLE offer_ingestion_runs
        ADD CONSTRAINT offer_ingestion_runs_status_check
        CHECK (status IN ('imported', 'evidence_missing', 'fetch_failed'))
        """
    )
    op.execute("DROP TABLE IF EXISTS admin_change_log")
    op.execute("DROP TABLE IF EXISTS offer_import_settings")
    op.execute("DROP INDEX IF EXISTS offer_categories_category_idx")
    op.execute(
        "ALTER TABLE offer_categories "
        "DROP CONSTRAINT IF EXISTS offer_categories_category_fkey"
    )
    op.execute(
        "ALTER TABLE offers DROP COLUMN IF EXISTS revision, "
        "DROP COLUMN IF EXISTS archived_at, "
        "DROP COLUMN IF EXISTS management_mode, "
        "DROP COLUMN IF EXISTS origin"
    )
    op.execute(
        "ALTER TABLE need_definitions DROP COLUMN IF EXISTS updated_at, "
        "DROP COLUMN IF EXISTS revision, DROP COLUMN IF EXISTS icon"
    )
