from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from vesta_api.api.admin_schemas import (
    AdminLoginRequest,
    AiAuditEntryDetailResponse,
    AiAuditEntrySummaryResponse,
    AiAuditLogListResponse,
)
from vesta_api.config import settings
from vesta_api.domain.admin_models import AdminUser
from vesta_api.domain.audit_models import AiOutcome, AiPort
from vesta_api.repositories.admin_users import AdminUserRepository
from vesta_api.repositories.ai_audit_log import AiAuditLogRepository
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
