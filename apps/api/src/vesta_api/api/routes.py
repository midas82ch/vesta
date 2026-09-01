from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from vesta_api.api.localization import disclaimer_for
from vesta_api.api.schemas import (
    MatchRequest,
    MatchResponse,
    PublicCategoryListResponse,
    PublicCategoryResponse,
    candidate_to_response,
)
from vesta_api.domain.models import MatchQuery
from vesta_api.repositories.dialogue_catalog import DialogueCatalogRepository
from vesta_api.repositories.offers import OfferRepository
from vesta_api.services.matching import MatchingService

router = APIRouter()


def matching_service(request: Request) -> MatchingService:
    return request.app.state.matching_service


def offer_repository(request: Request) -> OfferRepository:
    return request.app.state.offer_repository


def dialogue_catalog_repository(request: Request) -> DialogueCatalogRepository:
    return request.app.state.dialogue_catalog


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
def ready(
    repository: Annotated[OfferRepository, Depends(offer_repository)],
) -> dict[str, str]:
    try:
        repository.healthcheck()
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="database_unavailable",
        ) from error
    return {"status": "ready"}


@router.post("/v1/matches", response_model=MatchResponse)
def create_match(
    payload: MatchRequest,
    service: Annotated[MatchingService, Depends(matching_service)],
    catalog: Annotated[
        DialogueCatalogRepository, Depends(dialogue_catalog_repository)
    ],
) -> MatchResponse:
    if payload.need not in {need.key for need in catalog.list_needs()}:
        raise HTTPException(status_code=422, detail="unknown_or_inactive_category")
    result = service.match(
        MatchQuery(
            need=payload.need,
            language=payload.language,
            dog=payload.dog,
            has_identity_document=payload.has_identity_document,
            gender=payload.gender,
            age=payload.age,
            user_location=(
                payload.user_location.to_domain()
                if payload.user_location is not None
                else None
            ),
            at=datetime.now(UTC),
            risk_flags=tuple(payload.risk_flags),
        )
    )

    return MatchResponse(
        candidates=[candidate_to_response(candidate) for candidate in result.candidates],
        outcome=(
            "handoff"
            if result.human_handoff_required
            else "matches"
            if result.candidates
            else "no_match"
        ),
        human_handoff_required=result.human_handoff_required,
        handoff_reason=result.handoff_reason,
        disclaimer=disclaimer_for(payload.language),
    )


@router.get("/v1/catalog/categories", response_model=PublicCategoryListResponse)
def list_public_categories(
    catalog: Annotated[
        DialogueCatalogRepository, Depends(dialogue_catalog_repository)
    ],
    language: str = "de",
) -> PublicCategoryListResponse:
    categories: list[PublicCategoryResponse] = []
    for need in catalog.list_needs():
        localization = (
            need.localizations.get(language)
            or need.localizations.get("de")
            or next(iter(need.localizations.values()), {})
        )
        categories.append(
            PublicCategoryResponse(
                key=need.key,
                title=localization.get("title", need.key),
                description=localization.get("description", ""),
                icon=need.icon,
            )
        )
    return PublicCategoryListResponse(categories=categories)
