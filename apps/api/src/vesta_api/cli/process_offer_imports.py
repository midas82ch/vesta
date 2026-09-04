import argparse
import signal
from threading import Event

from vesta_api.config import settings
from vesta_api.ingestion.offer_import_ai import OpenAiOfferImportGateway
from vesta_api.ingestion.offer_import_worker import (
    OfferImportDraftStore,
    OfferImportProcessor,
)
from vesta_api.ingestion.safe_url import SafeUrlFetcher
from vesta_api.repositories.ai_audit_log import PostgresAiAuditLogRepository
from vesta_api.repositories.database import create_database_engine
from vesta_api.repositories.offer_import_jobs import PostgresOfferImportJobRepository


def main() -> None:
    parser = argparse.ArgumentParser(description="Process queued Vesta URL imports")
    parser.add_argument("--once", action="store_true", help="Process at most one queued job")
    args = parser.parse_args()

    if not settings.offer_url_import_enabled:
        if args.once:
            return
        stopped = Event()

        def stop_disabled(_signum: int, _frame: object) -> None:
            stopped.set()

        signal.signal(signal.SIGTERM, stop_disabled)
        signal.signal(signal.SIGINT, stop_disabled)
        stopped.wait()
        return

    database_url = settings.get_database_url()
    if database_url is None:
        raise RuntimeError("DATABASE_URL is required for the offer-import worker")
    api_key = settings.get_openai_api_key()
    if api_key is None:
        raise RuntimeError("OPENAI_API_KEY is required for the offer-import worker")

    engine = create_database_engine(database_url)
    jobs = PostgresOfferImportJobRepository(database_url, engine=engine)
    audit = PostgresAiAuditLogRepository(database_url, engine=engine)
    processor = OfferImportProcessor(
        jobs=jobs,
        fetcher=SafeUrlFetcher(),
        ai=OpenAiOfferImportGateway(
            api_key=api_key,
            model=settings.openai_model,
            audit_log=audit,
        ),
        store=OfferImportDraftStore(engine),
    )
    if args.once:
        processor.process_next()
        engine.dispose()
        return

    stopped = Event()

    def stop(_signum: int, _frame: object) -> None:
        stopped.set()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        while not stopped.is_set():
            if not processor.process_next():
                stopped.wait(2)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
