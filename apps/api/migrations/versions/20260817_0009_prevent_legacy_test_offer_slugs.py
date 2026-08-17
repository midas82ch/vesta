"""Clean up and prevent legacy test-prefixed offer slugs.

Revision ID: 20260817_0009
Revises: 20260728_0008
Create Date: 2026-08-17
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260817_0009"
down_revision: str | None = "20260728_0008"
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


def upgrade() -> None:
    for old_slug, new_slug in SLUG_RENAMES.items():
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

    op.create_check_constraint(
        "ck_offers_slug_not_legacy_test",
        "offers",
        "slug NOT LIKE 'test-%'",
    )
    op.create_check_constraint(
        "ck_offer_ingestion_runs_slug_not_legacy_test",
        "offer_ingestion_runs",
        "offer_slug NOT LIKE 'test-%'",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_offer_ingestion_runs_slug_not_legacy_test",
        "offer_ingestion_runs",
        type_="check",
    )
    op.drop_constraint(
        "ck_offers_slug_not_legacy_test",
        "offers",
        type_="check",
    )
    # The cleanup itself is intentionally not reversed: revision 0008 already
    # defines clean slugs as the expected state.
