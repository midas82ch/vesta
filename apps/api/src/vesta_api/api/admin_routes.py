from datetime import UTC, datetime
from typing import Annotated, Literal, NoReturn

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from vesta_api.api.admin_schemas import (
    AdminCategoryListResponse,
    AdminCategoryResponse,
    AdminCategoryWriteRequest,
    AdminChangeListResponse,
    AdminChangeResponse,
    AdminLoginRequest,
    AdminOfferLifecycleRequest,
    AdminOfferListResponse,
    AdminOfferResponse,
    AdminOfferWriteRequest,
    AiAuditEntryDetailResponse,
    AiAuditEntrySummaryResponse,
    AiAuditLogListResponse,
    ImportSettingsResponse,
    ImportSettingsUpdateRequest,
    IngestionRunListResponse,
    IngestionRunResponse,
    OfferImportJobCreateRequest,
    OfferImportJobListResponse,
    OfferImportJobResponse,
    OfferLocalizationWriteRequest,
    WorkflowAuditDetailResponse,
    WorkflowAuditListResponse,
    WorkflowAuditStepResponse,
    WorkflowAuditSummaryResponse,
)
from vesta_api.config import settings
from vesta_api.domain.admin_catalog_models import (
    CategoryWrite,
    OfferLocalizationWrite,
    OfferWrite,
)
from vesta_api.domain.admin_models import AdminUser
from vesta_api.domain.audit_models import AiOutcome, AiPort
from vesta_api.domain.ingestion_models import IngestionStatus
from vesta_api.ingestion.safe_url import SafeUrlError, normalize_offer_url
from vesta_api.repositories.admin_catalog import (
    AdminCatalogRepository,
    CatalogConflictError,
    CatalogNotFoundError,
    CatalogValidationError,
)
from vesta_api.repositories.admin_users import AdminUserRepository
from vesta_api.repositories.ai_audit_log import AiAuditLogRepository
from vesta_api.repositories.ingestion_runs import IngestionRunRepository
from vesta_api.repositories.offer_import_jobs import OfferImportJobRepository
from vesta_api.repositories.workflow_audit_log import WorkflowAuditLogRepository
from vesta_api.security import (
    SESSION_COOKIE_NAME,
    SESSION_TTL,
    AdminLoginAttemptStore,
    AdminSessionStore,
    verify_password_or_dummy,
)

router = APIRouter(prefix="/v1/admin")

MAX_LIST_LIMIT = 200


def admin_user_repository(request: Request) -> AdminUserRepository:
    return request.app.state.admin_users


def admin_session_store(request: Request) -> AdminSessionStore:
    return request.app.state.admin_sessions


def admin_login_attempt_store(request: Request) -> AdminLoginAttemptStore:
    return request.app.state.admin_login_attempts


def ai_audit_log_repository(request: Request) -> AiAuditLogRepository:
    return request.app.state.ai_audit_log


def workflow_audit_log_repository(request: Request) -> WorkflowAuditLogRepository:
    return request.app.state.workflow_audit_log


def ingestion_run_repository(request: Request) -> IngestionRunRepository:
    return request.app.state.ingestion_runs


def admin_offer_repository(request: Request) -> AdminCatalogRepository:
    return request.app.state.admin_catalog


def offer_import_job_repository(request: Request) -> OfferImportJobRepository:
    return request.app.state.offer_import_jobs


def _raise_catalog_http_error(error: Exception) -> NoReturn:
    if isinstance(error, CatalogNotFoundError):
        raise HTTPException(status_code=404, detail=str(error)) from error
    if isinstance(error, CatalogConflictError):
        raise HTTPException(status_code=409, detail=str(error)) from error
    if isinstance(error, CatalogValidationError):
        raise HTTPException(status_code=422, detail=str(error)) from error
    raise error


def require_admin_session(
    request: Request,
    sessions: Annotated[AdminSessionStore, Depends(admin_session_store)],
    users: Annotated[AdminUserRepository, Depends(admin_user_repository)],
) -> AdminUser:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="not_authenticated"
        )
    session = sessions.get(token, datetime.now(UTC))
    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="session_expired")
    user = users.get_by_username(session.username)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="not_authenticated")
    return user


@router.post("/login")
def login(
    payload: AdminLoginRequest,
    response: Response,
    users: Annotated[AdminUserRepository, Depends(admin_user_repository)],
    sessions: Annotated[AdminSessionStore, Depends(admin_session_store)],
    attempts: Annotated[AdminLoginAttemptStore, Depends(admin_login_attempt_store)],
) -> dict[str, str]:
    now = datetime.now(UTC)
    username = payload.username.strip()
    retry_after = attempts.retry_after_seconds(username, now)
    if retry_after is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="too_many_attempts",
            headers={"Retry-After": str(retry_after)},
        )

    user = users.get_by_username(username)
    password_valid = verify_password_or_dummy(
        payload.password,
        user.password_hash if user is not None else None,
    )
    if (
        user is None
        or not user.is_active
        or not password_valid
    ):
        attempts.record_failure(username, now)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials"
        )
    attempts.clear(username)
    token = sessions.create(user.username, now)
    response.set_cookie(
        SESSION_COOKIE_NAME,
        token,
        httponly=True,
        secure=settings.environment.lower() == "production",
        samesite="strict",
        max_age=int(SESSION_TTL.total_seconds()),
        path="/",
    )
    return {"status": "ok"}


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    sessions: Annotated[AdminSessionStore, Depends(admin_session_store)],
) -> dict[str, str]:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token is not None:
        sessions.delete(token)
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return {"status": "ok"}


@router.get("/ai-audit-log", response_model=AiAuditLogListResponse)
def list_ai_audit_log(
    _admin: Annotated[AdminUser, Depends(require_admin_session)],
    audit_log: Annotated[AiAuditLogRepository, Depends(ai_audit_log_repository)],
    limit: Annotated[int, Query(ge=1, le=MAX_LIST_LIMIT)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    port: Annotated[AiPort | None, Query()] = None,
    outcome: Annotated[AiOutcome | None, Query()] = None,
    session_id: str | None = None,
) -> AiAuditLogListResponse:
    entries = audit_log.list_entries(
        limit=limit,
        offset=offset,
        port=port,
        outcome=outcome,
        session_id=session_id,
    )
    return AiAuditLogListResponse(
        entries=[
            AiAuditEntrySummaryResponse(
                id=entry.id,
                session_id=entry.session_id,
                port=entry.port,
                provider=entry.provider,
                model=entry.model,
                outcome=entry.outcome,
                created_at=entry.created_at,
            )
            for entry in entries
        ]
    )


@router.get("/ai-audit-log/{entry_id}", response_model=AiAuditEntryDetailResponse)
def get_ai_audit_log_entry(
    entry_id: str,
    _admin: Annotated[AdminUser, Depends(require_admin_session)],
    audit_log: Annotated[AiAuditLogRepository, Depends(ai_audit_log_repository)],
) -> AiAuditEntryDetailResponse:
    entry = audit_log.get_entry(entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    return AiAuditEntryDetailResponse(
        id=entry.id,
        session_id=entry.session_id,
        port=entry.port,
        provider=entry.provider,
        model=entry.model,
        outcome=entry.outcome,
        violations=list(entry.violations),
        error_detail=entry.error_detail,
        request_text=entry.request_text,
        response_text=entry.response_text,
        created_at=entry.created_at,
    )


_AI_STEP_LABELS = {
    "interpret": "AI · Eingabe verstehen",
    "render_question": "AI · Frage formulieren",
    "explain": "AI · Ergebnis erklären",
}

_WORKFLOW_STAGE_LABELS = {
    "input": "Eingabe",
    "system": "Systemlogik",
    "output": "Antwort",
}


@router.get("/ai-audit-workflows", response_model=WorkflowAuditListResponse)
def list_ai_audit_workflows(
    _admin: Annotated[AdminUser, Depends(require_admin_session)],
    workflow_log: Annotated[
        WorkflowAuditLogRepository, Depends(workflow_audit_log_repository)
    ],
    audit_log: Annotated[AiAuditLogRepository, Depends(ai_audit_log_repository)],
    limit: Annotated[int, Query(ge=1, le=MAX_LIST_LIMIT)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> WorkflowAuditListResponse:
    workflows = workflow_log.list_workflows(limit=MAX_LIST_LIMIT, offset=0)
    workflow_map = {workflow.workflow_id: workflow for workflow in workflows}
    ai_groups: dict[str, list[AiAuditEntrySummaryResponse]] = {}
    for entry in audit_log.list_entries(
        limit=MAX_LIST_LIMIT,
        offset=0,
    ):
        workflow_id = entry.session_id or f"legacy__{entry.id}"
        ai_groups.setdefault(workflow_id, []).append(
            AiAuditEntrySummaryResponse(
                id=entry.id,
                session_id=entry.session_id,
                port=entry.port,
                provider=entry.provider,
                model=entry.model,
                outcome=entry.outcome,
                created_at=entry.created_at,
            )
        )

    responses: list[WorkflowAuditSummaryResponse] = []
    for workflow_id in workflow_map.keys() | ai_groups.keys():
        workflow = workflow_map.get(workflow_id)
        ai_entries = ai_groups.get(workflow_id, [])
        timestamps = [entry.created_at for entry in ai_entries]
        if workflow is not None:
            timestamps.extend((workflow.started_at, workflow.updated_at))
        assert timestamps
        responses.append(
            WorkflowAuditSummaryResponse(
                workflow_id=workflow_id,
                started_at=min(timestamps),
                updated_at=max(timestamps),
                input_preview=(
                    workflow.input_preview
                    if workflow is not None
                    else (
                        "Historische AI-Interpretation ohne vollständige Workflow-Spur"
                        if workflow_id.startswith("legacy__")
                        else "Historischer Dialog ohne erfasste Eingabe"
                    )
                ),
                event_count=workflow.event_count if workflow is not None else 0,
                ai_call_count=len(ai_entries),
                complete=(
                    workflow is not None
                    and workflow.has_input
                    and workflow.has_system
                    and workflow.has_output
                ),
                has_fallback=any(entry.outcome != "ai" for entry in ai_entries),
            )
        )
    responses.sort(key=lambda workflow: workflow.updated_at, reverse=True)
    return WorkflowAuditListResponse(workflows=responses[offset : offset + limit])


@router.get(
    "/ai-audit-workflows/{workflow_id}",
    response_model=WorkflowAuditDetailResponse,
)
def get_ai_audit_workflow(
    workflow_id: str,
    _admin: Annotated[AdminUser, Depends(require_admin_session)],
    workflow_log: Annotated[
        WorkflowAuditLogRepository, Depends(workflow_audit_log_repository)
    ],
    audit_log: Annotated[AiAuditLogRepository, Depends(ai_audit_log_repository)],
) -> WorkflowAuditDetailResponse:
    if workflow_id.startswith("legacy__"):
        legacy_entry_id = workflow_id.removeprefix("legacy__")
        legacy_entry = audit_log.get_entry(legacy_entry_id)
        events = ()
        ai_summaries = (legacy_entry,) if legacy_entry is not None else ()
    else:
        events = workflow_log.list_events(workflow_id)
        ai_summaries = audit_log.list_entries(
            limit=MAX_LIST_LIMIT,
            offset=0,
            session_id=workflow_id,
        )
    if not events and not ai_summaries:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")

    steps = [
        WorkflowAuditStepResponse(
            id=event.id,
            kind=event.stage,
            event_type=event.event_type,
            label=_WORKFLOW_STAGE_LABELS[event.stage],
            summary=event.summary,
            created_at=event.created_at,
            details=event.payload,
        )
        for event in events
    ]
    for summary in ai_summaries:
        detail = audit_log.get_entry(summary.id)
        if detail is None:
            continue
        steps.append(
            WorkflowAuditStepResponse(
                id=detail.id,
                kind="ai",
                event_type=detail.port,
                label=_AI_STEP_LABELS[detail.port],
                summary=(
                    f"{detail.provider}/{detail.model} · Ergebnis: {detail.outcome}"
                ),
                created_at=detail.created_at,
                provider=detail.provider,
                model=detail.model,
                outcome=detail.outcome,
                details={
                    "request_text": detail.request_text,
                    "response_text": detail.response_text,
                    "violations": list(detail.violations),
                    "error_detail": detail.error_detail,
                },
            )
        )
    steps.sort(key=lambda step: (step.created_at, step.id))
    kinds = {step.kind for step in steps}
    return WorkflowAuditDetailResponse(
        workflow_id=workflow_id,
        started_at=steps[0].created_at,
        updated_at=steps[-1].created_at,
        complete={"input", "system", "output"}.issubset(kinds),
        steps=steps,
    )


@router.get("/ingestion-runs", response_model=IngestionRunListResponse)
def list_ingestion_runs(
    _admin: Annotated[AdminUser, Depends(require_admin_session)],
    runs: Annotated[IngestionRunRepository, Depends(ingestion_run_repository)],
    limit: Annotated[int, Query(ge=1, le=MAX_LIST_LIMIT)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    status_filter: Annotated[IngestionStatus | None, Query(alias="status")] = None,
) -> IngestionRunListResponse:
    return IngestionRunListResponse(
        runs=[
            IngestionRunResponse(
                id=run.id,
                offer_slug=run.offer_slug,
                source_url=run.source_url,
                status=run.status,
                http_status=run.http_status,
                content_sha256=run.content_sha256,
                missing_evidence=list(run.missing_evidence),
                error=run.error,
                checked_at=run.checked_at,
            )
            for run in runs.list_runs(limit=limit, offset=offset, status=status_filter)
        ]
    )


@router.get("/offers", response_model=AdminOfferListResponse)
def list_admin_offers(
    _admin: Annotated[AdminUser, Depends(require_admin_session)],
    offers: Annotated[AdminCatalogRepository, Depends(admin_offer_repository)],
    limit: Annotated[int, Query(ge=1, le=MAX_LIST_LIMIT)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AdminOfferListResponse:
    all_offers = offers.list_offers()
    selected_offers = all_offers[offset : offset + limit]
    return AdminOfferListResponse(
        offers=[_offer_response(offer) for offer in selected_offers],
        total=len(all_offers),
        limit=limit,
        offset=offset,
    )


def _category_response(category: object) -> AdminCategoryResponse:
    return AdminCategoryResponse.model_validate(category, from_attributes=True)


def _offer_response(offer: object) -> AdminOfferResponse:
    return AdminOfferResponse.model_validate(offer, from_attributes=True)


@router.get("/categories", response_model=AdminCategoryListResponse)
def list_admin_categories(
    _admin: Annotated[AdminUser, Depends(require_admin_session)],
    catalog: Annotated[AdminCatalogRepository, Depends(admin_offer_repository)],
) -> AdminCategoryListResponse:
    return AdminCategoryListResponse(
        categories=[_category_response(category) for category in catalog.list_categories()]
    )


@router.post(
    "/categories", response_model=AdminCategoryResponse, status_code=201
)
def create_admin_category(
    payload: AdminCategoryWriteRequest,
    admin: Annotated[AdminUser, Depends(require_admin_session)],
    catalog: Annotated[AdminCatalogRepository, Depends(admin_offer_repository)],
) -> AdminCategoryResponse:
    try:
        category = catalog.create_category(
            CategoryWrite(
                icon=payload.icon,
                status=payload.status,
                sort_order=payload.sort_order,
                localizations={
                    locale: values.model_dump()
                    for locale, values in payload.localizations.items()
                },
            ),
            admin,
        )
    except Exception as error:
        _raise_catalog_http_error(error)
    return _category_response(category)


@router.put("/categories/{key}", response_model=AdminCategoryResponse)
def update_admin_category(
    key: str,
    payload: AdminCategoryWriteRequest,
    admin: Annotated[AdminUser, Depends(require_admin_session)],
    catalog: Annotated[AdminCatalogRepository, Depends(admin_offer_repository)],
) -> AdminCategoryResponse:
    if payload.revision is None:
        raise HTTPException(status_code=422, detail="revision_required")
    try:
        category = catalog.update_category(
            key,
            CategoryWrite(
                icon=payload.icon,
                status=payload.status,
                sort_order=payload.sort_order,
                localizations={
                    locale: values.model_dump()
                    for locale, values in payload.localizations.items()
                },
                revision=payload.revision,
            ),
            admin,
        )
    except Exception as error:
        _raise_catalog_http_error(error)
    return _category_response(category)


def _offer_write(payload: AdminOfferWriteRequest) -> OfferWrite:
    return OfferWrite(
        name=payload.name,
        organization_name=payload.organization_name,
        summary=payload.summary,
        needs=tuple(payload.needs),
        languages=tuple(payload.languages),
        access_rules=payload.access_rules.model_dump(),
        availability=payload.availability,
        contact_note=payload.contact_note,
        address=payload.address,
        latitude=payload.latitude,
        longitude=payload.longitude,
        source_label=payload.source_label,
        source_url=str(payload.source_url) if payload.source_url else None,
        expires_at=payload.expires_at,
        slug=payload.slug,
        management_mode=payload.management_mode,
        revision=payload.revision,
    )


@router.get("/offers/{offer_id}", response_model=AdminOfferResponse)
def get_admin_offer(
    offer_id: str,
    _admin: Annotated[AdminUser, Depends(require_admin_session)],
    catalog: Annotated[AdminCatalogRepository, Depends(admin_offer_repository)],
) -> AdminOfferResponse:
    offer = catalog.get_offer(offer_id)
    if offer is None:
        raise HTTPException(status_code=404, detail="offer_not_found")
    return _offer_response(offer)


@router.post("/offers", response_model=AdminOfferResponse, status_code=201)
def create_admin_offer(
    payload: AdminOfferWriteRequest,
    admin: Annotated[AdminUser, Depends(require_admin_session)],
    catalog: Annotated[AdminCatalogRepository, Depends(admin_offer_repository)],
) -> AdminOfferResponse:
    try:
        offer = catalog.create_offer(_offer_write(payload), admin)
    except Exception as error:
        _raise_catalog_http_error(error)
    return _offer_response(offer)


@router.put("/offers/{offer_id}", response_model=AdminOfferResponse)
def update_admin_offer(
    offer_id: str,
    payload: AdminOfferWriteRequest,
    admin: Annotated[AdminUser, Depends(require_admin_session)],
    catalog: Annotated[AdminCatalogRepository, Depends(admin_offer_repository)],
) -> AdminOfferResponse:
    if payload.revision is None:
        raise HTTPException(status_code=422, detail="revision_required")
    try:
        offer = catalog.update_offer(offer_id, _offer_write(payload), admin)
    except Exception as error:
        _raise_catalog_http_error(error)
    return _offer_response(offer)


@router.post("/offers/{offer_id}/lifecycle", response_model=AdminOfferResponse)
def set_admin_offer_lifecycle(
    offer_id: str,
    payload: AdminOfferLifecycleRequest,
    admin: Annotated[AdminUser, Depends(require_admin_session)],
    catalog: Annotated[AdminCatalogRepository, Depends(admin_offer_repository)],
) -> AdminOfferResponse:
    try:
        offer = catalog.set_offer_lifecycle(
            offer_id, payload.lifecycle, payload.revision, admin
        )
    except Exception as error:
        _raise_catalog_http_error(error)
    return _offer_response(offer)


@router.put(
    "/offers/{offer_id}/localizations/{locale}",
    response_model=AdminOfferResponse,
)
def put_admin_offer_localization(
    offer_id: str,
    locale: str,
    payload: OfferLocalizationWriteRequest,
    admin: Annotated[AdminUser, Depends(require_admin_session)],
    catalog: Annotated[AdminCatalogRepository, Depends(admin_offer_repository)],
) -> AdminOfferResponse:
    try:
        offer = catalog.put_offer_localization(
            offer_id,
            locale,
            OfferLocalizationWrite(
                name=payload.name,
                summary=payload.summary,
                contact_note=payload.contact_note,
                status=payload.status,
                revision=payload.revision,
            ),
            admin,
        )
    except Exception as error:
        _raise_catalog_http_error(error)
    return _offer_response(offer)


@router.post(
    "/offer-import-jobs",
    response_model=OfferImportJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_offer_import_job(
    payload: OfferImportJobCreateRequest,
    admin: Annotated[AdminUser, Depends(require_admin_session)],
    jobs: Annotated[OfferImportJobRepository, Depends(offer_import_job_repository)],
) -> OfferImportJobResponse:
    try:
        normalized = normalize_offer_url(payload.url)
    except SafeUrlError as error:
        raise HTTPException(status_code=422, detail=error.code) from error
    job = jobs.create(payload.url.strip(), normalized, admin)
    return OfferImportJobResponse.model_validate(job, from_attributes=True)


@router.get("/offer-import-jobs", response_model=OfferImportJobListResponse)
def list_offer_import_jobs(
    _admin: Annotated[AdminUser, Depends(require_admin_session)],
    jobs: Annotated[OfferImportJobRepository, Depends(offer_import_job_repository)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> OfferImportJobListResponse:
    return OfferImportJobListResponse(
        jobs=[
            OfferImportJobResponse.model_validate(job, from_attributes=True)
            for job in jobs.list(limit=limit, offset=offset)
        ],
        limit=limit,
        offset=offset,
    )


@router.get("/offer-import-jobs/{job_id}", response_model=OfferImportJobResponse)
def get_offer_import_job(
    job_id: str,
    _admin: Annotated[AdminUser, Depends(require_admin_session)],
    jobs: Annotated[OfferImportJobRepository, Depends(offer_import_job_repository)],
) -> OfferImportJobResponse:
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="offer_import_job_not_found")
    return OfferImportJobResponse.model_validate(job, from_attributes=True)


@router.post(
    "/offer-import-jobs/{job_id}/retry",
    response_model=OfferImportJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def retry_offer_import_job(
    job_id: str,
    admin: Annotated[AdminUser, Depends(require_admin_session)],
    jobs: Annotated[OfferImportJobRepository, Depends(offer_import_job_repository)],
) -> OfferImportJobResponse:
    job = jobs.retry(job_id, admin)
    if job is None:
        existing = jobs.get(job_id)
        if existing is None:
            raise HTTPException(status_code=404, detail="offer_import_job_not_found")
        raise HTTPException(status_code=409, detail="offer_import_job_not_retryable")
    return OfferImportJobResponse.model_validate(job, from_attributes=True)


@router.get("/import-settings", response_model=ImportSettingsResponse)
def get_admin_import_settings(
    _admin: Annotated[AdminUser, Depends(require_admin_session)],
    catalog: Annotated[AdminCatalogRepository, Depends(admin_offer_repository)],
) -> ImportSettingsResponse:
    return ImportSettingsResponse.model_validate(
        catalog.get_import_settings(), from_attributes=True
    )


@router.put("/import-settings", response_model=ImportSettingsResponse)
def update_admin_import_settings(
    payload: ImportSettingsUpdateRequest,
    admin: Annotated[AdminUser, Depends(require_admin_session)],
    catalog: Annotated[AdminCatalogRepository, Depends(admin_offer_repository)],
) -> ImportSettingsResponse:
    try:
        settings_value = catalog.update_import_settings(
            payload.automatic_enabled, payload.revision, admin
        )
    except Exception as error:
        _raise_catalog_http_error(error)
    return ImportSettingsResponse.model_validate(settings_value, from_attributes=True)


@router.get("/changes", response_model=AdminChangeListResponse)
def list_admin_changes(
    _admin: Annotated[AdminUser, Depends(require_admin_session)],
    catalog: Annotated[AdminCatalogRepository, Depends(admin_offer_repository)],
    entity_type: Annotated[
        Literal[
            "category",
            "offer",
            "import_settings",
            "offer_import",
            "offer_localization",
        ],
        Query(),
    ],
    entity_id: Annotated[str, Query(min_length=1, max_length=200)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> AdminChangeListResponse:
    return AdminChangeListResponse(
        changes=[
            AdminChangeResponse.model_validate(change, from_attributes=True)
            for change in catalog.list_changes(
                entity_type=entity_type, entity_id=entity_id, limit=limit
            )
        ]
    )
