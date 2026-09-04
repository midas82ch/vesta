import json
import re
import unicodedata
from dataclasses import asdict
from datetime import timedelta
from urllib.parse import urlsplit
from uuid import uuid4

from sqlalchemy import Engine, text

from vesta_api.ingestion.offer_import_ai import (
    ExtractedOffer,
    LocalizedOfferDraft,
    OfferImportAiPort,
)
from vesta_api.ingestion.safe_url import SafeUrlError, SafeUrlFetcher
from vesta_api.repositories.offer_import_jobs import OfferImportJobRepository

LEASE_DURATION = timedelta(minutes=5)
TRANSIENT_ERROR_CODES = {"network_error", "dns_resolution_failed", "provider_error"}


def _slugify(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-") or "angebot"


class OfferImportDraftStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def find_duplicates(
        self,
        *,
        normalized_url: str,
        content_sha256: str,
        extracted: ExtractedOffer,
    ) -> tuple[str, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT DISTINCT o.id::text
                    FROM offers o
                    JOIN organizations org ON org.id = o.organization_id
                    LEFT JOIN offer_verifications v ON v.offer_id = o.id
                    LEFT JOIN offer_import_jobs j ON j.offer_id = o.id
                    WHERE lower(COALESCE(v.source_url, '')) = lower(:source_url)
                       OR j.content_sha256 = :content_sha256
                       OR (
                            lower(org.name) = lower(:organization_name)
                            AND lower(o.name) = lower(:name)
                       )
                    """
                ),
                {
                    "source_url": normalized_url,
                    "content_sha256": content_sha256,
                    "organization_name": extracted.organization_name,
                    "name": extracted.name,
                },
            ).scalars().all()
        return tuple(str(value) for value in rows)

    @staticmethod
    def _unique_slug(connection: object, value: str) -> str:
        base = _slugify(value)
        candidate = base
        suffix = 2
        while connection.execute(  # type: ignore[attr-defined]
            text("SELECT 1 FROM offers WHERE slug = :slug"), {"slug": candidate}
        ).scalar_one_or_none():
            candidate = f"{base}-{suffix}"
            suffix += 1
        return candidate

    def save_draft(
        self,
        *,
        job_id: str,
        normalized_url: str,
        extracted: ExtractedOffer,
        localizations: tuple[LocalizedOfferDraft, ...],
    ) -> str:
        if not extracted.organization_name or not extracted.name or not extracted.summary:
            raise ValueError("missing_required_extraction")
        offer_id = uuid4()
        with self._engine.begin() as connection:
            requested = connection.execute(
                text(
                    """
                    SELECT j.requested_by, u.username
                    FROM offer_import_jobs j
                    JOIN admin_users u ON u.id = j.requested_by
                    WHERE j.id = CAST(:job_id AS uuid)
                    """
                ),
                {"job_id": job_id},
            ).mappings().one()
            organization_id = connection.execute(
                text("SELECT id FROM organizations WHERE lower(name) = lower(:name) LIMIT 1"),
                {"name": extracted.organization_name},
            ).scalar_one_or_none()
            if organization_id is None:
                organization_id = uuid4()
                connection.execute(
                    text("INSERT INTO organizations (id, name) VALUES (:id, :name)"),
                    {"id": organization_id, "name": extracted.organization_name},
                )
            slug = self._unique_slug(connection, extracted.name)
            access_rules = {
                "accepts_dogs": extracted.accepts_dogs,
                "identity_document_required": extracted.identity_document_required,
                "accepted_genders": list(extracted.accepted_genders),
                "minimum_age": extracted.minimum_age,
                "maximum_age": extracted.maximum_age,
            }
            contact = {"note": extracted.contact_note, "address": extracted.address}
            connection.execute(
                text(
                    """
                    INSERT INTO offers (
                        id, organization_id, slug, name, summary, languages,
                        access_rules, contact, location, availability, published,
                        is_demo, origin, management_mode, revision, updated_at
                    ) VALUES (
                        :id, :organization_id, :slug, :name, :summary, :languages,
                        CAST(:access_rules AS jsonb), CAST(:contact AS jsonb), NULL,
                        CAST(:availability AS offer_availability), false, false,
                        'imported', 'source', 1, now()
                    )
                    """
                ),
                {
                    "id": offer_id,
                    "organization_id": organization_id,
                    "slug": slug,
                    "name": extracted.name,
                    "summary": extracted.summary,
                    "languages": list(extracted.languages or (extracted.source_language,)),
                    "access_rules": json.dumps(access_rules, ensure_ascii=False),
                    "contact": json.dumps(contact, ensure_ascii=False),
                    "availability": extracted.availability,
                },
            )
            connection.execute(
                text(
                    """
                    INSERT INTO offer_categories (offer_id, category)
                    SELECT :offer_id, key FROM need_definitions
                    WHERE key = ANY(:needs) AND status <> 'archived'
                    """
                ),
                {"offer_id": offer_id, "needs": list(extracted.needs)},
            )
            connection.execute(
                text(
                    """
                    INSERT INTO offer_verifications (
                        id, offer_id, source_label, source_url, verified_by,
                        verified_at, expires_at, notes
                    ) VALUES (
                        :id, :offer_id, :label, :url, 'url-import-machine-draft',
                        now(), now(), 'Vor einer Veröffentlichung vollständig manuell prüfen.'
                    )
                    """
                ),
                {
                    "id": uuid4(),
                    "offer_id": offer_id,
                    "label": urlsplit(normalized_url).hostname or normalized_url,
                    "url": normalized_url,
                },
            )
            connection.execute(
                text(
                    """
                    INSERT INTO offer_localizations (
                        offer_id, locale, name, summary, contact_note,
                        status, revision, updated_at
                    ) VALUES (
                        :offer_id, :locale, :name, :summary, :contact_note,
                        'machine_draft', 1, now()
                    )
                    """
                ),
                [
                    {
                        "offer_id": offer_id,
                        "locale": item.locale,
                        "name": item.name,
                        "summary": item.summary,
                        "contact_note": item.contact_note,
                    }
                    for item in localizations
                ],
            )
            connection.execute(
                text(
                    """
                    INSERT INTO admin_change_log (
                        id, admin_user_id, admin_username, entity_type,
                        entity_id, action, after_data
                    ) VALUES (
                        :id, :admin_id, :username, 'offer_import',
                        :entity_id, 'draft_created', CAST(:after_data AS jsonb)
                    )
                    """
                ),
                {
                    "id": uuid4(),
                    "admin_id": requested["requested_by"],
                    "username": requested["username"],
                    "entity_id": job_id,
                    "after_data": json.dumps(
                        {"offer_id": str(offer_id), "source_url": normalized_url}
                    ),
                },
            )
        return str(offer_id)


class OfferImportProcessor:
    def __init__(
        self,
        *,
        jobs: OfferImportJobRepository,
        fetcher: SafeUrlFetcher,
        ai: OfferImportAiPort,
        store: OfferImportDraftStore,
    ) -> None:
        self._jobs = jobs
        self._fetcher = fetcher
        self._ai = ai
        self._store = store

    def process_next(self) -> bool:
        job = self._jobs.claim_next(lease=LEASE_DURATION)
        if job is None:
            return False
        try:
            page = self._fetcher.fetch(job.normalized_url)
            self._jobs.update(
                job.id,
                status="extracting",
                content_sha256=page.content_sha256,
            )
            extracted = self._ai.extract(
                source_url=page.final_url,
                page_text=page.text,
                job_id=job.id,
            )
            extracted_data = asdict(extracted)
            duplicates = self._store.find_duplicates(
                normalized_url=page.final_url,
                content_sha256=page.content_sha256,
                extracted=extracted,
            )
            if duplicates:
                self._jobs.update(
                    job.id,
                    status="ready_for_review",
                    source_language=extracted.source_language,
                    extracted_data=extracted_data,
                    evidence=extracted.evidence,
                    duplicate_offer_ids=duplicates,
                )
                return True
            self._jobs.update(
                job.id,
                status="translating",
                source_language=extracted.source_language,
                extracted_data=extracted_data,
                evidence=extracted.evidence,
            )
            localizations = self._ai.translate(extracted=extracted, job_id=job.id)
            offer_id = self._store.save_draft(
                job_id=job.id,
                normalized_url=page.final_url,
                extracted=extracted,
                localizations=localizations,
            )
            self._jobs.update(job.id, status="ready_for_review", offer_id=offer_id)
        except SafeUrlError as error:
            self._handle_error(job.id, job.attempts, error.code, str(error))
        except Exception as error:
            self._handle_error(job.id, job.attempts, "provider_error", str(error))
        return True

    def _handle_error(self, job_id: str, attempts: int, code: str, detail: str) -> None:
        retry = code in TRANSIENT_ERROR_CODES and attempts < 3
        self._jobs.update(
            job_id,
            status="queued" if retry else "failed",
            error_code=code,
            error_detail=detail,
        )
