"""Create admin_users and ai_interaction_log tables.

Revision ID: 20260727_0005
Revises: 20260726_0004
Create Date: 2026-07-27
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260727_0005"
down_revision: str | None = "20260726_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS admin_users (
            id UUID PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_interaction_log (
            id UUID PRIMARY KEY,
            session_id TEXT,
            port TEXT NOT NULL
                CHECK (port IN ('interpret', 'render_question', 'explain')),
            provider TEXT NOT NULL,
            model TEXT NOT NULL,
            outcome TEXT NOT NULL
                CHECK (outcome IN ('ai', 'fallback_validation', 'fallback_error')),
            violations JSONB NOT NULL DEFAULT '[]',
            error_detail TEXT,
            request_text TEXT NOT NULL,
            response_text TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ai_interaction_log_created_at_idx "
        "ON ai_interaction_log (created_at DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ai_interaction_log_session_id_idx "
        "ON ai_interaction_log (session_id)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ai_interaction_log")
    op.execute("DROP TABLE IF EXISTS admin_users")
