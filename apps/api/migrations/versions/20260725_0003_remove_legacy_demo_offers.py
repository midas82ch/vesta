"""Remove generic demo offers after public-source ingestion.

Revision ID: 20260725_0003
Revises: 20260725_0002
Create Date: 2026-07-25
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260725_0003"
down_revision: str | None = "20260725_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

LEGACY_DEMO_SLUGS = (
    "demo-sleep",
    "demo-basic-needs",
    "demo-counselling",
)


def upgrade() -> None:
    op.execute(
        """
        DELETE FROM offers
        WHERE is_demo = true
          AND slug IN (
              'demo-sleep',
              'demo-basic-needs',
              'demo-counselling'
          )
        """
    )
    op.execute(
        """
        DELETE FROM organizations
        WHERE name = 'Vesta Demo-Daten'
          AND NOT EXISTS (
              SELECT 1
              FROM offers
              WHERE offers.organization_id = organizations.id
          )
        """
    )


def downgrade() -> None:
    # The development seed command can recreate these fixtures if required.
    return None
