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
from vesta_api.domain.admin_catalog_models import (
    AdminCatalogState,
    AdminCategory,
    AdminOffer,
    OfferLocalization,
)
from vesta_api.repositories.admin_catalog import (
    AdminCatalogRepository,
    InMemoryAdminCatalogRepository,
    PostgresAdminCatalogRepository,
)
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
    AdminManagedDialogueCatalogRepository,
    DialogueCatalogRepository,
    JsonDialogueCatalogRepository,
    PostgresDialogueCatalogRepository,
)
from vesta_api.repositories.ingestion_runs import (
    IngestionRunRepository,
    InMemoryIngestionRunRepository,
    PostgresIngestionRunRepository,
)
from vesta_api.repositories.offer_import_jobs import (
    InMemoryOfferImportJobRepository,
    OfferImportJobRepository,
    PostgresOfferImportJobRepository,
)
from vesta_api.repositories.offers import (
    AdminManagedOfferRepository,
    JsonOfferRepository,
    OfferRepository,
    PostgresOfferRepository,
)
from vesta_api.repositories.workflow_audit_log import (
    InMemoryWorkflowAuditLogRepository,
    PostgresWorkflowAuditLogRepository,
    WorkflowAuditLogRepository,
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


def create_workflow_audit_log_repository() -> WorkflowAuditLogRepository:
    database_url = settings.get_database_url()
    if database_url is not None:
        return PostgresWorkflowAuditLogRepository(database_url)
    if settings.environment.lower() == "production":
        raise RuntimeError("DATABASE_URL is required when VESTA_ENV=production")
    return InMemoryWorkflowAuditLogRepository()


def create_ingestion_run_repository() -> IngestionRunRepository:
    database_url = settings.get_database_url()
    if database_url is not None:
        return PostgresIngestionRunRepository(database_url)
    if settings.environment.lower() == "production":
        raise RuntimeError("DATABASE_URL is required when VESTA_ENV=production")
    return InMemoryIngestionRunRepository()


def create_admin_catalog_repository(
    catalog: DialogueCatalogRepository,
    offers: OfferRepository,
) -> AdminCatalogRepository:
    database_url = settings.get_admin_database_url()
    if database_url is not None:
        return PostgresAdminCatalogRepository(database_url)
    if settings.environment.lower() == "production":
        raise RuntimeError(
            "ADMIN_DATABASE_URL is required when VESTA_ENV=production"
        )
    development_database_url = settings.get_database_url()
    if development_database_url is not None:
        return PostgresAdminCatalogRepository(development_database_url)
    state = AdminCatalogState(
        categories={
            need.key: AdminCategory(
                key=need.key,
                icon=need.icon,
                status="published",
                sort_order=need.sort_order,
                revision=1,
                localizations=need.localizations,
            )
            for need in catalog.list_needs()
        },
        offers={
            offer.id: AdminOffer(
                id=offer.id,
                slug=offer.slug or offer.id,
                name=offer.name,
                organization_name=offer.organization_name or "Unbekannte Organisation",
                summary=offer.summary,
                needs=offer.needs,
                languages=offer.languages,
                access_rules={
                    "accepts_dogs": offer.access.accepts_dogs,
                    "identity_document_required": (
                        offer.access.identity_document_required
                    ),
                    "accepted_genders": list(offer.access.accepted_genders),
                    "minimum_age": offer.access.minimum_age,
                    "maximum_age": offer.access.maximum_age,
                },
                availability=offer.availability.value,
                contact_note=offer.contact_note,
                address=offer.address,
                latitude=offer.location.latitude if offer.location else None,
                longitude=offer.location.longitude if offer.location else None,
                source_label=offer.source.label,
                source_url=offer.source.url,
                verified_by=offer.source.verified_by,
                verified_at=offer.source.verified_at,
                expires_at=offer.source.expires_at,
                origin="imported",
                management_mode="source",
                lifecycle="published" if offer.published else "draft",
                revision=1,
                is_demo=offer.is_demo,
                updated_at=offer.updated_at or offer.source.verified_at,
                localizations={
                    "de": OfferLocalization(
                        locale="de",
                        name=offer.name,
                        summary=offer.summary,
                        contact_note=offer.contact_note,
                        status="reviewed",
                        revision=1,
                        reviewed_by=offer.source.verified_by,
                        reviewed_at=offer.source.verified_at,
                        updated_at=offer.updated_at or offer.source.verified_at,
                    )
                },
            )
            for offer in offers.list_offers()
        },
    )
    return InMemoryAdminCatalogRepository(state)


def create_offer_import_job_repository() -> OfferImportJobRepository:
    database_url = settings.get_admin_database_url()
    if database_url is not None:
        return PostgresOfferImportJobRepository(database_url)
    if settings.environment.lower() == "production":
        raise RuntimeError("ADMIN_DATABASE_URL is required when VESTA_ENV=production")
    development_database_url = settings.get_database_url()
    if development_database_url is not None:
        return PostgresOfferImportJobRepository(development_database_url)
    return InMemoryOfferImportJobRepository()


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

    workflow_audit_log = create_workflow_audit_log_repository()
    workflow_audit_log.healthcheck()
    app.state.workflow_audit_log = workflow_audit_log

    ingestion_runs = create_ingestion_run_repository()
    ingestion_runs.healthcheck()
    app.state.ingestion_runs = ingestion_runs

    admin_catalog = create_admin_catalog_repository(catalog, repository)
    admin_catalog.healthcheck()
    app.state.admin_catalog = admin_catalog

    offer_import_jobs = create_offer_import_job_repository()
    offer_import_jobs.healthcheck()
    app.state.offer_import_jobs = offer_import_jobs
    if isinstance(admin_catalog, InMemoryAdminCatalogRepository):
        catalog = AdminManagedDialogueCatalogRepository(catalog, admin_catalog)
        app.state.dialogue_catalog = catalog
        repository = AdminManagedOfferRepository(admin_catalog)
        app.state.offer_repository = repository
        app.state.matching_service = MatchingService(repository)

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
        workflow_audit_log.close()
        ingestion_runs.close()
        admin_catalog.close()
        offer_import_jobs.close()


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
