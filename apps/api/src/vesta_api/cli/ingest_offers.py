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
