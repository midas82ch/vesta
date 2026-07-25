from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from vesta_api import __version__
from vesta_api.api.routes import router
from vesta_api.config import settings
from vesta_api.repositories.offers import JsonOfferRepository
from vesta_api.services.matching import MatchingService


@asynccontextmanager
async def lifespan(app: FastAPI):
    repository = JsonOfferRepository(settings.offer_data_path)
    app.state.matching_service = MatchingService(repository)
    yield


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
