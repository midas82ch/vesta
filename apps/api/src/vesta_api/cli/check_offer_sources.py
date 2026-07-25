from urllib.error import HTTPError, URLError

from vesta_api.config import settings
from vesta_api.ingestion.web_offers import (
    WebPageFetcher,
    evaluate_evidence,
    load_catalog,
)


def main() -> None:
    catalog = load_catalog(settings.offer_source_catalog_path)
    fetcher = WebPageFetcher()
    failed = 0

    for offer in catalog.offers:
        try:
            page = fetcher.fetch(str(offer.source.url))
        except (HTTPError, URLError, OSError, ValueError, PermissionError) as error:
            print(f"FAILED {offer.slug}: {type(error).__name__}")
            failed += 1
            continue

        evidence = evaluate_evidence(page.text, offer.source.evidence)
        if evidence.accepted:
            print(f"OK {offer.slug}: HTTP {page.status_code}")
        else:
            print(
                f"FAILED {offer.slug}: missing evidence: "
                f"{', '.join(evidence.missing)}"
            )
            failed += 1

    print(f"Checked {len(catalog.offers)} sources: {failed} failed.")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
