import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from vesta_api import __version__
from vesta_api.ai.gateway import AiGateway
from vesta_api.api.admin_routes import router as admin_router
from vesta_api.api.dialogue_routes import router as dialogue_router
from vesta_api.api.routes import router
from vesta_api.config import settings
from vesta_api.repositories.admin_users import (
    AdminUserRepository,
    InMemoryAdminUserRepository,
    PostgresAdminUserRepository,
)
from vesta_api.repositories.ai_audit_log import (
    AiAuditLogRepository,
    InMemoryAiAuditLogRepository,
    PostgresAiAuditLogRepository,
)
from vesta_api.repositories.dialogue_catalog import (
    DialogueCatalogRepository,
    JsonDialogueCatalogRepository,
    PostgresDialogueCatalogRepository,
)
from vesta_api.repositories.offers import (
    JsonOfferRepository,
    OfferRepository,
    PostgresOfferRepository,
)
from vesta_api.security import AdminLoginAttemptStore, AdminSessionStore
from vesta_api.services.dialogue_orchestrator import DialogueOrchestrator, DialogueSessionStore
from vesta_api.services.matching import MatchingService

logger = logging.getLogger(__name__)

def create_offer_repository() -> OfferRepository:
    database_url = settings.get_database_url()
    if database_url is not None:
        return PostgresOfferRepository(database_url)
    if settings.environment.lower() == "production":
        raise RuntimeError("DATABASE_URL is required when VESTA_ENV=production")
    return JsonOfferRepository(settings.offer_data_path)


def create_dialogue_catalog_repository() -> DialogueCatalogRepository:
    database_url = settings.get_database_url()
    if database_url is not None:
        return PostgresDialogueCatalogRepository(database_url)
    if settings.environment.lower() == "production":
        raise RuntimeError("DATABASE_URL is required when VESTA_ENV=production")
    return JsonDialogueCatalogRepository(settings.dialogue_catalog_path)


def create_admin_user_repository() -> AdminUserRepository:
    database_url = settings.get_database_url()
    if database_url is not None:
        return PostgresAdminUserRepository(database_url)
    if settings.environment.lower() == "production":
        raise RuntimeError("DATABASE_URL is required when VESTA_ENV=production")

    repository = InMemoryAdminUserRepository()
    if settings.dev_admin_username and settings.dev_admin_password:
        from vesta_api.security import hash_password

        repository.create(
            username=settings.dev_admin_username,
            password_hash=hash_password(settings.dev_admin_password),
        )
        logger.warning(
            "Seeded dev-only admin user %r into the in-memory repository "
            "(VESTA_DEV_ADMIN_USERNAME is set - never do this in production)",
            settings.dev_admin_username,
        )
    return repository


def create_ai_audit_log_repository() -> AiAuditLogRepository:
    database_url = settings.get_database_url()
    if database_url is not None:
        return PostgresAiAuditLogRepository(database_url)
    if settings.environment.lower() == "production":
        raise RuntimeError("DATABASE_URL is required when VESTA_ENV=production")
    return InMemoryAiAuditLogRepository()


def create_ai_gateway(audit_log: AiAuditLogRepository) -> AiGateway:
    if not settings.ai_enabled:
        return AiGateway(enabled=False)

    provider = settings.ai_provider.lower()

    if provider == "openai":
        api_key = settings.get_openai_api_key()
        if api_key is None:
            logger.warning(
                "VESTA_AI_ENABLED is set but OPENAI_API_KEY is missing; using template mode"
            )
            return AiGateway(enabled=False)
        try:
            from vesta_api.ai.openai_gateway import OpenAiGateway

            live = OpenAiGateway(api_key=api_key, model=settings.openai_model)
            return AiGateway(
                enabled=True,
                live=live,
                provider=provider,
                model=settings.openai_model,
                audit_log=audit_log,
            )
        except ModuleNotFoundError:
            logger.warning("VESTA_AI_ENABLED is set but the 'openai' package is not installed")
            return AiGateway(enabled=False)

    api_key = settings.get_anthropic_api_key()
    if api_key is None:
        logger.warning(
            "VESTA_AI_ENABLED is set but ANTHROPIC_API_KEY is missing; using template mode"
        )
        return AiGateway(enabled=False)

    try:
        from vesta_api.ai.live_gateway import AnthropicGateway

        live = AnthropicGateway(api_key=api_key, model=settings.ai_model)
        return AiGateway(
            enabled=True,
            live=live,
            provider=provider,
            model=settings.ai_model,
            audit_log=audit_log,
        )
    except ModuleNotFoundError:
        logger.warning("VESTA_AI_ENABLED is set but the 'anthropic' package is not installed")
        return AiGateway(enabled=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    repository = create_offer_repository()
    repository.healthcheck()
    app.state.offer_repository = repository
    app.state.matching_service = MatchingService(repository)

    catalog = create_dialogue_catalog_repository()
    catalog.healthcheck()
    app.state.dialogue_catalog = catalog

    admin_users = create_admin_user_repository()
    admin_users.healthcheck()
    app.state.admin_users = admin_users
    app.state.admin_sessions = AdminSessionStore()
    app.state.admin_login_attempts = AdminLoginAttemptStore()

    ai_audit_log = create_ai_audit_log_repository()
    ai_audit_log.healthcheck()
    app.state.ai_audit_log = ai_audit_log
    app.state.ai_gateway = create_ai_gateway(ai_audit_log)
    app.state.dialogue_orchestrator = DialogueOrchestrator(
        matching_service=app.state.matching_service,
        catalog=catalog,
        session_store=DialogueSessionStore(),
    )
    try:
        yield
    finally:
        repository.close()
        catalog.close()
        admin_users.close()
        ai_audit_log.close()


app = FastAPI(
    title="Vesta API",
    description="Verifizierte und nachvollziehbare Vermittlung zu sozialen Angeboten.",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.include_router(router)
app.include_router(dialogue_router)
app.include_router(admin_router)
