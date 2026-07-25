"""Create the verified offer registry.

Revision ID: 20260725_0001
Revises:
Create Date: 2026-07-25
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260725_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        """
        DO $$
        BEGIN
            CREATE TYPE offer_availability AS ENUM (
                'confirmed',
                'call_to_confirm',
                'unknown'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END
        $$;
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS organizations (
            id UUID PRIMARY KEY,
            name TEXT NOT NULL,
            contact_email TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS offers (
            id UUID PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES organizations(id),
            slug TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            summary TEXT NOT NULL,
            languages TEXT[] NOT NULL DEFAULT '{}',
            location GEOGRAPHY(POINT, 4326),
            access_rules JSONB NOT NULL DEFAULT '{}',
            contact JSONB NOT NULL DEFAULT '{}',
            availability offer_availability NOT NULL DEFAULT 'unknown',
            published BOOLEAN NOT NULL DEFAULT false,
            is_demo BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        ALTER TABLE offers
        ADD COLUMN IF NOT EXISTS is_demo BOOLEAN NOT NULL DEFAULT false
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS offer_categories (
            offer_id UUID NOT NULL REFERENCES offers(id) ON DELETE CASCADE,
            category TEXT NOT NULL,
            PRIMARY KEY (offer_id, category)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS offer_verifications (
            id UUID PRIMARY KEY,
            offer_id UUID NOT NULL REFERENCES offers(id) ON DELETE CASCADE,
            source_label TEXT NOT NULL,
            source_url TEXT,
            verified_by TEXT NOT NULL,
            verified_at TIMESTAMPTZ NOT NULL,
            expires_at TIMESTAMPTZ NOT NULL,
            notes TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS knowledge_chunks (
            id UUID PRIMARY KEY,
            offer_id UUID REFERENCES offers(id) ON DELETE CASCADE,
            content TEXT NOT NULL,
            source_url TEXT,
            expires_at TIMESTAMPTZ NOT NULL,
            embedding VECTOR(1536)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS anonymous_outcomes (
            id UUID PRIMARY KEY,
            need TEXT NOT NULL,
            result TEXT NOT NULL,
            barrier TEXT,
            offer_id UUID REFERENCES offers(id) ON DELETE SET NULL,
            occurred_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS offers_location_idx "
        "ON offers USING GIST (location)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS knowledge_chunks_embedding_idx "
        "ON knowledge_chunks USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS anonymous_outcomes")
    op.execute("DROP TABLE IF EXISTS knowledge_chunks")
    op.execute("DROP TABLE IF EXISTS offer_verifications")
    op.execute("DROP TABLE IF EXISTS offer_categories")
    op.execute("DROP TABLE IF EXISTS offers")
    op.execute("DROP TABLE IF EXISTS organizations")
    op.execute("DROP TYPE IF EXISTS offer_availability")
