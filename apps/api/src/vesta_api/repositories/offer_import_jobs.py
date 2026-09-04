import json
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from threading import Lock
from typing import Any, Protocol
from uuid import uuid4

from sqlalchemy import Engine, text

from vesta_api.domain.admin_models import AdminUser
from vesta_api.domain.offer_import_models import OfferImportJob, OfferImportStatus
from vesta_api.repositories.database import create_database_engine


class OfferImportJobRepository(Protocol):
    def create(self, source_url: str, normalized_url: str, admin: AdminUser) -> OfferImportJob: ...

    def list(self, *, limit: int, offset: int) -> tuple[OfferImportJob, ...]: ...

    def get(self, job_id: str) -> OfferImportJob | None: ...

    def retry(
        self, job_id: str, admin: AdminUser | None = None
    ) -> OfferImportJob | None: ...

    def claim_next(self, *, lease: timedelta) -> OfferImportJob | None: ...

    def update(
        self,
        job_id: str,
        *,
        status: OfferImportStatus,
        source_language: str | None = None,
        content_sha256: str | None = None,
        extracted_data: dict[str, object] | None = None,
        evidence: tuple[dict[str, str], ...] = (),
        duplicate_offer_ids: tuple[str, ...] = (),
        offer_id: str | None = None,
        error_code: str | None = None,
        error_detail: str | None = None,
    ) -> OfferImportJob: ...

    def healthcheck(self) -> None: ...

    def close(self) -> None: ...


def _row_to_job(row: Mapping[str, Any]) -> OfferImportJob:
    return OfferImportJob(
        id=str(row["id"]),
        source_url=str(row["source_url"]),
        normalized_url=str(row["normalized_url"]),
        status=row["status"],
        requested_by=str(row["requested_by"]),
        offer_id=str(row["offer_id"]) if row["offer_id"] else None,
        source_language=(str(row["source_language"]) if row["source_language"] else None),
        content_sha256=(str(row["content_sha256"]) if row["content_sha256"] else None),
        extracted_data=dict(row["extracted_data"]) if row["extracted_data"] else None,
        evidence=tuple(dict(item) for item in (row["evidence"] or [])),
        duplicate_offer_ids=tuple(str(value) for value in row["duplicate_offer_ids"]),
        error_code=str(row["error_code"]) if row["error_code"] else None,
        error_detail=str(row["error_detail"]) if row["error_detail"] else None,
        attempts=int(row["attempts"]),
        lease_expires_at=row["lease_expires_at"],
        created_at=row["created_at"],
        started_at=row["started_at"],
        completed_at=row["completed_at"],
        updated_at=row["updated_at"],
    )


_SELECT = """
SELECT j.id::text, j.source_url, j.normalized_url, j.status,
       u.username AS requested_by, j.offer_id::text, j.source_language,
       j.content_sha256, j.extracted_data, j.evidence, j.duplicate_offer_ids,
       j.error_code, j.error_detail, j.attempts, j.lease_expires_at,
       j.created_at, j.started_at, j.completed_at, j.updated_at
FROM offer_import_jobs j
JOIN admin_users u ON u.id = j.requested_by
"""

_INSERT_QUEUE_CHANGE = text(
    """
    INSERT INTO admin_change_log (
        id, admin_user_id, admin_username, entity_type,
        entity_id, action, after_data
    ) VALUES (
        :change_id, CAST(:admin_id AS uuid), :username,
        'offer_import', :entity_id, 'queued',
        jsonb_build_object('source_url', CAST(:source_url AS text))
    )
    """
)

_CLAIM_NEXT = text(
    _SELECT
    + """
    WHERE j.id = (
        SELECT id FROM offer_import_jobs
        WHERE (
            status = 'queued'
            OR (status IN ('fetching', 'extracting', 'translating')
                AND lease_expires_at < now())
        ) AND attempts < 3
        ORDER BY created_at
        FOR UPDATE SKIP LOCKED
        LIMIT 1
    )
    FOR UPDATE OF j
    """
)


class PostgresOfferImportJobRepository:
    def __init__(self, database_url: str, *, engine: Engine | None = None) -> None:
        self._engine = engine or create_database_engine(database_url)

    def create(self, source_url: str, normalized_url: str, admin: AdminUser) -> OfferImportJob:
        job_id = str(uuid4())
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO offer_import_jobs (
                        id, source_url, normalized_url, requested_by
                    ) VALUES (
                        CAST(:id AS uuid), :source_url, :normalized_url,
                        CAST(:requested_by AS uuid)
                    )
                    """
                ),
                {
                    "id": job_id,
                    "source_url": source_url,
                    "normalized_url": normalized_url,
                    "requested_by": admin.id,
                },
            )
            connection.execute(
                _INSERT_QUEUE_CHANGE,
                {
                    "change_id": uuid4(),
                    "admin_id": admin.id,
                    "username": admin.username,
                    "entity_id": job_id,
                    "source_url": normalized_url,
                },
            )
        job = self.get(job_id)
        assert job is not None
        return job

    def list(self, *, limit: int, offset: int) -> tuple[OfferImportJob, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                text(_SELECT + " ORDER BY j.created_at DESC LIMIT :limit OFFSET :offset"),
                {"limit": limit, "offset": offset},
            ).mappings().all()
        return tuple(_row_to_job(row) for row in rows)

    def get(self, job_id: str) -> OfferImportJob | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text(_SELECT + " WHERE j.id = CAST(:id AS uuid)"), {"id": job_id}
            ).mappings().one_or_none()
        return _row_to_job(row) if row else None

    def retry(
        self, job_id: str, admin: AdminUser | None = None
    ) -> OfferImportJob | None:
        with self._engine.begin() as connection:
            changed = connection.execute(
                text(
                    """
                    UPDATE offer_import_jobs SET
                        status = 'queued', error_code = NULL, error_detail = NULL,
                        lease_expires_at = NULL, completed_at = NULL, updated_at = now()
                    WHERE id = CAST(:id AS uuid) AND status = 'failed' AND attempts < 3
                    RETURNING id
                    """
                ),
                {"id": job_id},
            ).scalar_one_or_none()
            if changed and admin is not None:
                connection.execute(
                    text(
                        """
                        INSERT INTO admin_change_log (
                            id, admin_user_id, admin_username, entity_type,
                            entity_id, action
                        ) VALUES (
                            :change_id, CAST(:admin_id AS uuid), :username,
                            'offer_import', :entity_id, 'retried'
                        )
                        """
                    ),
                    {
                        "change_id": uuid4(),
                        "admin_id": admin.id,
                        "username": admin.username,
                        "entity_id": job_id,
                    },
                )
        return self.get(job_id) if changed else None

    def claim_next(self, *, lease: timedelta) -> OfferImportJob | None:
        lease_seconds = int(lease.total_seconds())
        with self._engine.begin() as connection:
            row = connection.execute(_CLAIM_NEXT).mappings().one_or_none()
            if row is None:
                return None
            connection.execute(
                text(
                    """
                    UPDATE offer_import_jobs SET
                        status = 'fetching', attempts = attempts + 1,
                        started_at = COALESCE(started_at, now()),
                        lease_expires_at = now() + make_interval(secs => :lease_seconds),
                        updated_at = now()
                    WHERE id = CAST(:id AS uuid)
                    """
                ),
                {"id": row["id"], "lease_seconds": lease_seconds},
            )
        return self.get(str(row["id"]))

    def update(
        self,
        job_id: str,
        *,
        status: OfferImportStatus,
        source_language: str | None = None,
        content_sha256: str | None = None,
        extracted_data: dict[str, object] | None = None,
        evidence: tuple[dict[str, str], ...] = (),
        duplicate_offer_ids: tuple[str, ...] = (),
        offer_id: str | None = None,
        error_code: str | None = None,
        error_detail: str | None = None,
    ) -> OfferImportJob:
        terminal = status in ("ready_for_review", "failed")
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE offer_import_jobs SET
                        status = :status,
                        source_language = COALESCE(:source_language, source_language),
                        content_sha256 = COALESCE(:content_sha256, content_sha256),
                        extracted_data = COALESCE(CAST(:extracted_data AS jsonb), extracted_data),
                        evidence = CASE WHEN CAST(:evidence AS jsonb) = '[]'::jsonb
                            THEN evidence ELSE CAST(:evidence AS jsonb) END,
                        duplicate_offer_ids = CASE WHEN cardinality(CAST(:duplicates AS uuid[])) = 0
                            THEN duplicate_offer_ids ELSE CAST(:duplicates AS uuid[]) END,
                        offer_id = COALESCE(CAST(:offer_id AS uuid), offer_id),
                        error_code = :error_code, error_detail = :error_detail,
                        completed_at = CASE WHEN :terminal THEN now() ELSE completed_at END,
                        lease_expires_at = CASE
                            WHEN :terminal OR :status = 'queued' THEN NULL
                            ELSE now() + interval '5 minutes'
                        END,
                        updated_at = now()
                    WHERE id = CAST(:id AS uuid)
                    """
                ),
                {
                    "id": job_id,
                    "status": status,
                    "source_language": source_language,
                    "content_sha256": content_sha256,
                    "extracted_data": (
                        json.dumps(extracted_data) if extracted_data is not None else None
                    ),
                    "evidence": json.dumps(evidence),
                    "duplicates": list(duplicate_offer_ids),
                    "offer_id": offer_id,
                    "error_code": error_code,
                    "error_detail": error_detail[:500] if error_detail else None,
                    "terminal": terminal,
                },
            )
        job = self.get(job_id)
        if job is None:
            raise KeyError("offer_import_job_not_found")
        return job

    def healthcheck(self) -> None:
        with self._engine.connect() as connection:
            connection.execute(text("SELECT 1"))

    def close(self) -> None:
        self._engine.dispose()


class InMemoryOfferImportJobRepository:
    def __init__(self) -> None:
        self._jobs: dict[str, OfferImportJob] = {}
        self._lock = Lock()

    def create(self, source_url: str, normalized_url: str, admin: AdminUser) -> OfferImportJob:
        now = datetime.now(UTC)
        job = OfferImportJob(
            id=str(uuid4()),
            source_url=source_url,
            normalized_url=normalized_url,
            status="queued",
            requested_by=admin.username,
            offer_id=None,
            source_language=None,
            content_sha256=None,
            extracted_data=None,
            evidence=(),
            duplicate_offer_ids=(),
            error_code=None,
            error_detail=None,
            attempts=0,
            lease_expires_at=None,
            created_at=now,
            started_at=None,
            completed_at=None,
            updated_at=now,
        )
        self._jobs[job.id] = job
        return job

    def list(self, *, limit: int, offset: int) -> tuple[OfferImportJob, ...]:
        jobs = sorted(self._jobs.values(), key=lambda item: item.created_at, reverse=True)
        return tuple(jobs[offset : offset + limit])

    def get(self, job_id: str) -> OfferImportJob | None:
        return self._jobs.get(job_id)

    def retry(
        self, job_id: str, admin: AdminUser | None = None
    ) -> OfferImportJob | None:
        del admin
        job = self._jobs.get(job_id)
        if job is None or job.status != "failed" or job.attempts >= 3:
            return None
        return self._replace(
            job,
            status="queued",
            error_code=None,
            error_detail=None,
            completed_at=None,
            lease_expires_at=None,
        )

    def claim_next(self, *, lease: timedelta) -> OfferImportJob | None:
        with self._lock:
            now = datetime.now(UTC)
            eligible = [
                job
                for job in self._jobs.values()
                if job.attempts < 3
                and (
                    job.status == "queued"
                    or (
                        job.status in ("fetching", "extracting", "translating")
                        and job.lease_expires_at is not None
                        and job.lease_expires_at < now
                    )
                )
            ]
            if not eligible:
                return None
            job = min(eligible, key=lambda item: item.created_at)
            return self._replace(
                job,
                status="fetching",
                attempts=job.attempts + 1,
                lease_expires_at=now + lease,
                started_at=job.started_at or now,
            )

    def _replace(self, job: OfferImportJob, **changes: object) -> OfferImportJob:
        from dataclasses import replace

        changed = replace(job, updated_at=datetime.now(UTC), **changes)
        self._jobs[job.id] = changed
        return changed

    def update(
        self, job_id: str, *, status: OfferImportStatus, **changes: object
    ) -> OfferImportJob:
        job = self._jobs[job_id]
        terminal = status in ("ready_for_review", "failed")
        return self._replace(
            job,
            status=status,
            completed_at=datetime.now(UTC) if terminal else job.completed_at,
            lease_expires_at=(
                None
                if terminal or status == "queued"
                else datetime.now(UTC) + timedelta(minutes=5)
            ),
            **{key: value for key, value in changes.items() if value not in (None, (), {})},
        )

    def healthcheck(self) -> None:
        return None

    def close(self) -> None:
        return None
