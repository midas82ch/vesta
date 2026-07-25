import hashlib
import json
import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser
from uuid import NAMESPACE_URL, uuid4, uuid5

from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from sqlalchemy import Engine, text

USER_AGENT = "VestaPrototypeOfferVerifier/0.2 (+https://vesta.vielzuwenig.ch)"
MAX_PAGE_BYTES = 2_000_000
VERIFICATION_TTL = timedelta(days=7)


class CatalogAccessRules(BaseModel):
    accepts_dogs: bool | None = None
    identity_document_required: bool | None = None
    accepted_genders: list[str] = Field(default_factory=list)
    minimum_age: int | None = None
    maximum_age: int | None = None


class CatalogSource(BaseModel):
    label: str
    url: HttpUrl
    evidence: list[str] = Field(min_length=2)


class CatalogOffer(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    slug: str = Field(pattern=r"^[a-z0-9-]+$")
    organization_key: str
    organization_name: str
    name: str
    summary: str
    needs: list[str] = Field(min_length=1)
    languages: list[str] = Field(min_length=1)
    access: CatalogAccessRules
    availability: str
    contact_note: str
    source: CatalogSource


class OfferCatalog(BaseModel):
    catalog_version: int
    offers: list[CatalogOffer] = Field(min_length=1)


@dataclass(frozen=True)
class FetchedPage:
    status_code: int
    text: str
    content_sha256: str


@dataclass(frozen=True)
class EvidenceResult:
    accepted: bool
    missing: tuple[str, ...]


@dataclass(frozen=True)
class IngestionSummary:
    checked: int
    imported: int
    failed: int


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._hidden_depth = 0

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        del attrs
        if tag in {"script", "style", "noscript", "template", "svg"}:
            self._hidden_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "template", "svg"}:
            self._hidden_depth = max(0, self._hidden_depth - 1)

    def handle_data(self, data: str) -> None:
        if self._hidden_depth == 0:
            self.parts.append(data)


def html_to_text(html: str) -> str:
    parser = _VisibleTextParser()
    parser.feed(html)
    return " ".join(parser.parts)


def normalize_evidence_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"\s+", " ", normalized).strip()


def evaluate_evidence(page_text: str, required: list[str]) -> EvidenceResult:
    normalized_page = normalize_evidence_text(page_text)
    missing = tuple(
        item
        for item in required
        if normalize_evidence_text(item) not in normalized_page
    )
    return EvidenceResult(accepted=not missing, missing=missing)


def load_catalog(path: Path) -> OfferCatalog:
    payload = json.loads(path.read_text(encoding="utf-8"))
    catalog = OfferCatalog.model_validate(payload)
    slugs = [offer.slug for offer in catalog.offers]
    if len(slugs) != len(set(slugs)):
        raise ValueError("Offer catalog contains duplicate slugs")
    if any(not offer.name.startswith("Testangebot:") for offer in catalog.offers):
        raise ValueError("Every automatically imported offer must be marked as a test")
    return catalog


class WebPageFetcher:
    def __init__(self) -> None:
        self._robots: dict[str, RobotFileParser] = {}

    def _robots_parser(self, url: str) -> RobotFileParser:
        split_url = urlsplit(url)
        origin = f"{split_url.scheme}://{split_url.netloc}"
        if origin not in self._robots:
            parser = RobotFileParser()
            parser.set_url(urljoin(origin, "/robots.txt"))
            parser.read()
            self._robots[origin] = parser
        return self._robots[origin]

    def fetch(self, url: str) -> FetchedPage:
        if urlsplit(url).scheme != "https":
            raise ValueError("Only HTTPS offer sources are allowed")
        if not self._robots_parser(url).can_fetch(USER_AGENT, url):
            raise PermissionError("Source disallows this importer in robots.txt")

        request = Request(
            url,
            headers={
                "Accept": "text/html,application/xhtml+xml",
                "User-Agent": USER_AGENT,
            },
        )
        with urlopen(request, timeout=15) as response:
            content_type = response.headers.get_content_type()
            if content_type not in {"text/html", "application/xhtml+xml"}:
                raise ValueError(f"Unsupported content type: {content_type}")
            body = response.read(MAX_PAGE_BYTES + 1)
            if len(body) > MAX_PAGE_BYTES:
                raise ValueError("Source page exceeds the 2 MB safety limit")
            charset = response.headers.get_content_charset() or "utf-8"
            html = body.decode(charset, errors="replace")
            return FetchedPage(
                status_code=response.status,
                text=html_to_text(html),
                content_sha256=hashlib.sha256(body).hexdigest(),
            )


_UPSERT_ORGANIZATION = text(
    """
    INSERT INTO organizations (id, name)
    VALUES (:id, :name)
    ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name
    """
)

_UPSERT_OFFER = text(
    """
    INSERT INTO offers (
        id,
        organization_id,
        slug,
        name,
        summary,
        languages,
        access_rules,
        contact,
        availability,
        published,
        is_demo,
        updated_at
    )
    VALUES (
        :id,
        :organization_id,
        :slug,
        :name,
        :summary,
        :languages,
        CAST(:access_rules AS jsonb),
        CAST(:contact AS jsonb),
        CAST(:availability AS offer_availability),
        true,
        true,
        now()
    )
    ON CONFLICT (id) DO UPDATE SET
        organization_id = EXCLUDED.organization_id,
        slug = EXCLUDED.slug,
        name = EXCLUDED.name,
        summary = EXCLUDED.summary,
        languages = EXCLUDED.languages,
        access_rules = EXCLUDED.access_rules,
        contact = EXCLUDED.contact,
        availability = EXCLUDED.availability,
        published = true,
        is_demo = true,
        updated_at = now()
    """
)

_DELETE_CATEGORIES = text(
    "DELETE FROM offer_categories WHERE offer_id = :offer_id"
)
_INSERT_CATEGORY = text(
    """
    INSERT INTO offer_categories (offer_id, category)
    VALUES (:offer_id, :category)
    ON CONFLICT DO NOTHING
    """
)
_UPSERT_VERIFICATION = text(
    """
    INSERT INTO offer_verifications (
        id,
        offer_id,
        source_label,
        source_url,
        verified_by,
        verified_at,
        expires_at,
        notes
    )
    VALUES (
        :id,
        :offer_id,
        :source_label,
        :source_url,
        'automated-public-source-check',
        :verified_at,
        :expires_at,
        :notes
    )
    ON CONFLICT (id) DO UPDATE SET
        source_label = EXCLUDED.source_label,
        source_url = EXCLUDED.source_url,
        verified_by = EXCLUDED.verified_by,
        verified_at = EXCLUDED.verified_at,
        expires_at = EXCLUDED.expires_at,
        notes = EXCLUDED.notes
    """
)
_INSERT_RUN = text(
    """
    INSERT INTO offer_ingestion_runs (
        id,
        offer_slug,
        source_url,
        status,
        http_status,
        content_sha256,
        missing_evidence,
        error,
        checked_at
    )
    VALUES (
        :id,
        :offer_slug,
        :source_url,
        :status,
        :http_status,
        :content_sha256,
        :missing_evidence,
        :error,
        :checked_at
    )
    """
)


def _record_failed_run(
    engine: Engine,
    offer: CatalogOffer,
    *,
    status: str,
    checked_at: datetime,
    page: FetchedPage | None = None,
    missing_evidence: tuple[str, ...] = (),
    error: str | None = None,
) -> None:
    with engine.begin() as connection:
        connection.execute(
            _INSERT_RUN,
            {
                "id": uuid4(),
                "offer_slug": offer.slug,
                "source_url": str(offer.source.url),
                "status": status,
                "http_status": page.status_code if page else None,
                "content_sha256": page.content_sha256 if page else None,
                "missing_evidence": list(missing_evidence),
                "error": error[:500] if error else None,
                "checked_at": checked_at,
            },
        )


def _store_offer(
    engine: Engine,
    offer: CatalogOffer,
    page: FetchedPage,
    checked_at: datetime,
) -> None:
    organization_id = uuid5(
        NAMESPACE_URL,
        f"https://vesta.vielzuwenig.ch/organizations/{offer.organization_key}",
    )
    offer_id = uuid5(
        NAMESPACE_URL,
        f"https://vesta.vielzuwenig.ch/offers/{offer.slug}",
    )
    verification_id = uuid5(
        NAMESPACE_URL,
        (
            "https://vesta.vielzuwenig.ch/verifications/"
            f"{offer.slug}/{page.content_sha256}"
        ),
    )

    with engine.begin() as connection:
        connection.execute(
            _UPSERT_ORGANIZATION,
            {"id": organization_id, "name": offer.organization_name},
        )
        connection.execute(
            _UPSERT_OFFER,
            {
                "id": offer_id,
                "organization_id": organization_id,
                "slug": offer.slug,
                "name": offer.name,
                "summary": offer.summary,
                "languages": [language.lower() for language in offer.languages],
                "access_rules": offer.access.model_dump_json(),
                "contact": json.dumps({"note": offer.contact_note}),
                "availability": offer.availability,
            },
        )
        connection.execute(_DELETE_CATEGORIES, {"offer_id": offer_id})
        connection.execute(
            _INSERT_CATEGORY,
            [
                {"offer_id": offer_id, "category": category}
                for category in offer.needs
            ],
        )
        connection.execute(
            _UPSERT_VERIFICATION,
            {
                "id": verification_id,
                "offer_id": offer_id,
                "source_label": offer.source.label,
                "source_url": str(offer.source.url),
                "verified_at": checked_at,
                "expires_at": checked_at + VERIFICATION_TTL,
                "notes": (
                    "Automatisch als Testdatensatz geprüft; "
                    f"content_sha256={page.content_sha256}"
                ),
            },
        )
        connection.execute(
            _INSERT_RUN,
            {
                "id": uuid4(),
                "offer_slug": offer.slug,
                "source_url": str(offer.source.url),
                "status": "imported",
                "http_status": page.status_code,
                "content_sha256": page.content_sha256,
                "missing_evidence": [],
                "error": None,
                "checked_at": checked_at,
            },
        )


def ingest_catalog(
    engine: Engine,
    catalog: OfferCatalog,
    *,
    fetch_page: Callable[[str], FetchedPage] | None = None,
    now: datetime | None = None,
) -> IngestionSummary:
    fetch = fetch_page or WebPageFetcher().fetch
    checked_at = now or datetime.now(UTC)
    imported = 0
    failed = 0

    for offer in catalog.offers:
        try:
            page = fetch(str(offer.source.url))
        except (HTTPError, URLError, OSError, ValueError, PermissionError) as error:
            _record_failed_run(
                engine,
                offer,
                status="fetch_failed",
                checked_at=checked_at,
                error=f"{type(error).__name__}: {error}",
            )
            print(f"FAILED {offer.slug}: source could not be checked")
            failed += 1
            continue

        evidence = evaluate_evidence(page.text, offer.source.evidence)
        if not evidence.accepted:
            _record_failed_run(
                engine,
                offer,
                status="evidence_missing",
                checked_at=checked_at,
                page=page,
                missing_evidence=evidence.missing,
            )
            print(f"FAILED {offer.slug}: expected evidence is missing")
            failed += 1
            continue

        _store_offer(engine, offer, page, checked_at)
        print(f"IMPORTED {offer.slug}")
        imported += 1

    return IngestionSummary(
        checked=len(catalog.offers),
        imported=imported,
        failed=failed,
    )
