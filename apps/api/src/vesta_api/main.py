from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from vesta_api import __version__
from vesta_api.api.routes import router
from vesta_api.config import settings
from vesta_api.repositories.offers import (
    JsonOfferRepository,
    OfferRepository,
    PostgresOfferRepository,
)
from vesta_api.services.matching import MatchingService


def create_offer_repository() -> OfferRepository:
    database_url = settings.get_database_url()
    if database_url is not None:
        return PostgresOfferRepository(database_url)
    if settings.environment.lower() == "production":
        raise RuntimeError("DATABASE_URL is required when VESTA_ENV=production")
    return JsonOfferRepository(settings.offer_data_path)


@asynccontextmanager
async def lifespan(app: FastAPI):
    repository = create_offer_repository()
    repository.healthcheck()
    app.state.offer_repository = repository
    app.state.matching_service = MatchingService(repository)
    try:
        yield
    finally:
        repository.close()


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
