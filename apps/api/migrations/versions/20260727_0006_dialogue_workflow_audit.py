"""Create the dialogue workflow audit trail.

Revision ID: 20260727_0006
Revises: 20260727_0005
Create Date: 2026-07-27
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260727_0006"
down_revision: str | None = "20260727_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS dialogue_workflow_log (
            id UUID PRIMARY KEY,
            workflow_id TEXT NOT NULL,
            stage TEXT NOT NULL
                CHECK (stage IN ('input', 'system', 'output')),
            event_type TEXT NOT NULL,
            summary TEXT NOT NULL,
            payload JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS dialogue_workflow_log_created_at_idx "
        "ON dialogue_workflow_log (created_at DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS dialogue_workflow_log_workflow_id_idx "
        "ON dialogue_workflow_log (workflow_id, created_at)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS dialogue_workflow_log")
