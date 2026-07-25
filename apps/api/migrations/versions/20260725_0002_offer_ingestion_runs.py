"""Track automated offer source checks.

Revision ID: 20260725_0002
Revises: 20260725_0001
Create Date: 2026-07-25
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260725_0002"
down_revision: str | None = "20260725_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS offer_ingestion_runs (
            id UUID PRIMARY KEY,
            offer_slug TEXT NOT NULL,
            source_url TEXT NOT NULL,
            status TEXT NOT NULL CHECK (
                status IN ('imported', 'evidence_missing', 'fetch_failed')
            ),
            http_status INTEGER,
            content_sha256 TEXT,
            missing_evidence TEXT[] NOT NULL DEFAULT '{}',
            error TEXT,
            checked_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS offer_ingestion_runs_source_checked_idx
        ON offer_ingestion_runs (source_url, checked_at DESC)
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS offer_ingestion_runs")
