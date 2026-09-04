"""Normalize unrestricted gender access rules.

Revision ID: 20260904_0013
Revises: 20260902_0012
Create Date: 2026-09-04
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260904_0013"
down_revision: str | None = "20260902_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE offers
        SET access_rules = jsonb_set(
                COALESCE(access_rules, '{}'::jsonb),
                '{accepted_genders}',
                '[]'::jsonb,
                true
            ),
            revision = revision + 1,
            updated_at = now()
        WHERE jsonb_typeof(access_rules -> 'accepted_genders') = 'array'
          AND access_rules -> 'accepted_genders' @> '["all"]'::jsonb
        """
    )
    op.create_check_constraint(
        "ck_offers_no_all_gender_marker",
        "offers",
        "NOT COALESCE((access_rules -> 'accepted_genders') "
        "@> '[\"all\"]'::jsonb, false)",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_offers_no_all_gender_marker",
        "offers",
        type_="check",
    )
    # Empty restrictions are the canonical representation for unrestricted
    # access. Reintroducing the redundant marker would recreate the ambiguity.
