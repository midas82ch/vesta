"""Mark already-ingested offers as verified, not demo data.

Revision ID: 20260727_0007
Revises: 20260727_0006
Create Date: 2026-07-27
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260727_0007"
down_revision: str | None = "20260727_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("UPDATE offers SET is_demo = false WHERE is_demo = true")


def downgrade() -> None:
    op.execute("UPDATE offers SET is_demo = true WHERE is_demo = false")
