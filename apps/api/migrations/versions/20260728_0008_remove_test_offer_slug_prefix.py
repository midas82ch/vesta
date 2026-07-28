"""Remove the legacy test prefix from verified offer slugs.

Revision ID: 20260728_0008
Revises: 20260727_0007
Create Date: 2026-07-28
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260728_0008"
down_revision: str | None = "20260727_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SLUG_RENAMES = {
    "test-passantenheim-bern": "passantenheim-bern",
    "test-finta-notschlafstelle-bern": "finta-notschlafstelle-bern",
    "test-contact-anlaufstelle-bern": "contact-anlaufstelle-bern",
    "test-contact-la-gare-bern": "contact-la-gare-bern",
    "test-wohnberatung-bern": "wohnberatung-bern",
    "test-hope-point-bern": "hope-point-bern",
    "test-contact-suchtbehandlung-bern": "contact-suchtbehandlung-bern",
}


def _rename_slugs(renames: dict[str, str]) -> None:
    for old_slug, new_slug in renames.items():
        op.execute(
            f"""
            UPDATE offers
            SET slug = '{new_slug}',
                updated_at = now()
            WHERE slug = '{old_slug}'
            """
        )
        op.execute(
            f"""
            UPDATE offer_ingestion_runs
            SET offer_slug = '{new_slug}'
            WHERE offer_slug = '{old_slug}'
            """
        )


def upgrade() -> None:
    _rename_slugs(SLUG_RENAMES)


def downgrade() -> None:
    _rename_slugs({new_slug: old_slug for old_slug, new_slug in SLUG_RENAMES.items()})
