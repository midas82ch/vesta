from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from vesta_api.api.admin_schemas import (
    AdminLoginRequest,
    AdminOfferListResponse,
    AdminOfferResponse,
    AiAuditEntryDetailResponse,
    AiAuditEntrySummaryResponse,
    AiAuditLogListResponse,
    IngestionRunListResponse,
    IngestionRunResponse,
    WorkflowAuditDetailResponse,
    WorkflowAuditListResponse,
    WorkflowAuditStepResponse,
    WorkflowAuditSummaryResponse,
)
from vesta_api.config import settings
from vesta_api.domain.admin_models import AdminUser
from vesta_api.domain.audit_models import AiOutcome, AiPort
from vesta_api.domain.ingestion_models import IngestionStatus
from vesta_api.repositories.admin_users import AdminUserRepository
from vesta_api.repositories.ai_audit_log import AiAuditLogRepository
from vesta_api.repositories.ingestion_runs import IngestionRunRepository
from vesta_api.repositories.offers import OfferRepository
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


def admin_offer_repository(request: Request) -> OfferRepository:
    return request.app.state.offer_repository


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
    offers: Annotated[OfferRepository, Depends(admin_offer_repository)],
    limit: Annotated[int, Query(ge=1, le=MAX_LIST_LIMIT)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AdminOfferListResponse:
    all_offers = offers.list_offers()
    selected_offers = all_offers[offset : offset + limit]
    return AdminOfferListResponse(
        offers=[
            AdminOfferResponse(
                id=offer.id,
                slug=offer.slug,
                name=offer.name,
                organization_name=offer.organization_name,
                summary=offer.summary,
                needs=[need.value for need in offer.needs],
                languages=list(offer.languages),
                availability=offer.availability.value,
                published=offer.published,
                is_demo=offer.is_demo,
                contact_note=offer.contact_note,
                address=offer.location.address if offer.location is not None else None,
                source_label=offer.source.label,
                source_url=offer.source.url,
                verified_at=offer.source.verified_at,
                updated_at=offer.updated_at,
            )
            for offer in selected_offers
        ],
        total=len(all_offers),
        limit=limit,
        offset=offset,
    )
