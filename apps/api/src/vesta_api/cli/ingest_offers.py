from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import text

from vesta_api.config import settings
from vesta_api.ingestion.web_offers import ingest_catalog, load_catalog
from vesta_api.repositories.database import create_database_engine


def main() -> None:
    database_url = settings.get_database_url()
    if database_url is None:
        raise RuntimeError("DATABASE_URL is required to ingest offers")

    catalog = load_catalog(settings.offer_source_catalog_path)
    engine = create_database_engine(database_url)
    try:
        with engine.begin() as connection:
            automatic_enabled = connection.execute(
                text(
                    "SELECT automatic_enabled FROM offer_import_settings WHERE id = 1"
                )
            ).scalar_one()
            if not automatic_enabled:
                connection.execute(
                    text(
                        """
                        INSERT INTO offer_ingestion_runs (
                            id, offer_slug, source_url, status, missing_evidence,
                            checked_at
                        ) VALUES (
                            :id, '__catalog__', 'internal:automatic-import',
                            'skipped_disabled', '{}', :checked_at
                        )
                        """
                    ),
                    {"id": uuid4(), "checked_at": datetime.now(UTC)},
                )
                print("Automatic offer import is disabled; run skipped.")
                return
        summary = ingest_catalog(engine, catalog)
    finally:
        engine.dispose()

    print(
        f"Checked {summary.checked} sources: "
        f"{summary.imported} imported, {summary.failed} failed."
    )
    if summary.failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
