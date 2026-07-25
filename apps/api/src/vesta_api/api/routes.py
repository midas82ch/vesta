from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from vesta_api.api.schemas import (
    MatchRequest,
    MatchResponse,
    candidate_to_response,
)
from vesta_api.domain.models import MatchQuery
from vesta_api.repositories.offers import OfferRepository
from vesta_api.services.matching import MatchingService

router = APIRouter()


def matching_service(request: Request) -> MatchingService:
    return request.app.state.matching_service


def offer_repository(request: Request) -> OfferRepository:
    return request.app.state.offer_repository


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
) -> MatchResponse:
    result = service.match(
        MatchQuery(
            need=payload.need,
            language=payload.language,
            dog=payload.dog,
            has_identity_document=payload.has_identity_document,
            gender=payload.gender,
            age=payload.age,
            at=datetime.now(UTC),
            risk_flags=tuple(payload.risk_flags),
        )
    )

    return MatchResponse(
        candidates=[candidate_to_response(candidate) for candidate in result.candidates],
        human_handoff_required=result.human_handoff_required,
        handoff_reason=result.handoff_reason,
        disclaimer=(
            "Angebote werden nicht automatisch reserviert. "
            "Aktualität und Kontaktangaben vor Ort bestätigen."
        ),
    )
