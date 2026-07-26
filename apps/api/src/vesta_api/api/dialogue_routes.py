from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from vesta_api.ai.gateway import AiGateway
from vesta_api.api.dialogue_schemas import (
    AnswerRequest,
    AttributeProposalResponse,
    DialogueTurnResponse,
    ExplainedCandidateResponse,
    ExplanationReasonResponse,
    ExplanationResponse,
    InterpretRequest,
    InterpretResponse,
    QuestionOptionResponse,
    RenderedQuestionResponse,
    StartDialogueRequest,
)
from vesta_api.api.schemas import candidate_to_response
from vesta_api.domain.dialogue_catalog import QuestionDefinition
from vesta_api.domain.models import MatchResult
from vesta_api.repositories.dialogue_catalog import DialogueCatalogRepository
from vesta_api.services.dialogue_orchestrator import DialogueOrchestrator, DialogueTurnResult
from vesta_api.services.result_grounding import build_grounding_bundle

router = APIRouter(prefix="/v1/dialogue")

DISCLAIMER = (
    "Angebote werden nicht automatisch reserviert. "
    "Aktualität und Kontaktangaben vor Ort bestätigen."
)


def dialogue_orchestrator(request: Request) -> DialogueOrchestrator:
    return request.app.state.dialogue_orchestrator


def ai_gateway(request: Request) -> AiGateway:
    return request.app.state.ai_gateway


def dialogue_catalog(request: Request) -> DialogueCatalogRepository:
    return request.app.state.dialogue_catalog


@router.post("/interpret", response_model=InterpretResponse)
def interpret(
    payload: InterpretRequest,
    gateway: Annotated[AiGateway, Depends(ai_gateway)],
    catalog: Annotated[DialogueCatalogRepository, Depends(dialogue_catalog)],
) -> InterpretResponse:
    result = gateway.interpret(
        free_text=payload.free_text,
        locale=payload.language,
        needs=catalog.list_needs(),
        attributes=catalog.list_attributes(),
        session_id=None,
    )
    return InterpretResponse(
        need_key=result.need_key,
        proposals=[
            AttributeProposalResponse(key=p.key, value=p.value, confidence=p.confidence)
            for p in result.proposals
        ],
        requires_confirmation=list(result.requires_confirmation),
        ambiguities=list(result.ambiguities),
        source=result.source,
    )


def _find_question(
    catalog: DialogueCatalogRepository, question_key: str
) -> QuestionDefinition:
    for question in catalog.list_questions():
        if question.key == question_key:
            return question
    raise HTTPException(status_code=404, detail="unknown_question_key")


def _render_question(
    turn: DialogueTurnResult,
    *,
    gateway: AiGateway,
    catalog: DialogueCatalogRepository,
    locale: str,
    session_id: str,
) -> RenderedQuestionResponse | None:
    if turn.question is None:
        return None
    attribute = catalog.get_attribute(turn.question.attribute_key)
    assert attribute is not None
    rendered = gateway.render_question(
        question=turn.question, attribute=attribute, locale=locale, session_id=session_id
    )
    return RenderedQuestionResponse(
        question_key=turn.question.key,
        attribute_key=turn.question.attribute_key,
        answer_type=turn.question.answer_type,
        text=rendered.text,
        help_text=rendered.help_text,
        unknown_label=rendered.unknown_label,
        decline_label=rendered.decline_label,
        options=[QuestionOptionResponse(value=o.value, label=o.label) for o in rendered.options],
        source=rendered.source,
    )


def _explain_candidates(
    match_result: MatchResult | None,
    *,
    gateway: AiGateway,
    locale: str,
    session_id: str,
) -> list[ExplainedCandidateResponse]:
    if match_result is None:
        return []
    explained: list[ExplainedCandidateResponse] = []
    for candidate in match_result.candidates:
        bundle = build_grounding_bundle(candidate)
        explanation = gateway.explain(bundle=bundle, locale=locale, session_id=session_id)
        explained.append(
            ExplainedCandidateResponse(
                candidate=candidate_to_response(candidate),
                explanation=ExplanationResponse(
                    headline=explanation.headline,
                    reasons=[
                        ExplanationReasonResponse(text=r.text, supported_by=list(r.supported_by))
                        for r in explanation.reasons
                    ],
                    clarification=(
                        ExplanationReasonResponse(
                            text=explanation.clarification.text,
                            supported_by=list(explanation.clarification.supported_by),
                        )
                        if explanation.clarification is not None
                        else None
                    ),
                    next_action=explanation.next_action,
                    source=explanation.source,
                ),
            )
        )
    return explained


def _turn_response(
    turn: DialogueTurnResult,
    *,
    gateway: AiGateway,
    catalog: DialogueCatalogRepository,
    locale: str,
) -> DialogueTurnResponse:
    return DialogueTurnResponse(
        session_id=turn.state.session_id,
        ai_mode=gateway.mode,
        question=_render_question(
            turn,
            gateway=gateway,
            catalog=catalog,
            locale=locale,
            session_id=turn.state.session_id,
        ),
        candidates=_explain_candidates(
            turn.match_result,
            gateway=gateway,
            locale=locale,
            session_id=turn.state.session_id,
        ),
        human_handoff_required=(
            turn.match_result.human_handoff_required if turn.match_result else False
        ),
        handoff_reason=turn.match_result.handoff_reason if turn.match_result else None,
        disclaimer=DISCLAIMER,
    )


@router.post("/start", response_model=DialogueTurnResponse)
def start(
    payload: StartDialogueRequest,
    orchestrator: Annotated[DialogueOrchestrator, Depends(dialogue_orchestrator)],
    gateway: Annotated[AiGateway, Depends(ai_gateway)],
    catalog: Annotated[DialogueCatalogRepository, Depends(dialogue_catalog)],
) -> DialogueTurnResponse:
    turn = orchestrator.start(locale=payload.language, need=payload.need, now=datetime.now(UTC))
    return _turn_response(turn, gateway=gateway, catalog=catalog, locale=payload.language)


@router.post("/answer", response_model=DialogueTurnResponse)
def answer(
    payload: AnswerRequest,
    orchestrator: Annotated[DialogueOrchestrator, Depends(dialogue_orchestrator)],
    gateway: Annotated[AiGateway, Depends(ai_gateway)],
    catalog: Annotated[DialogueCatalogRepository, Depends(dialogue_catalog)],
) -> DialogueTurnResponse:
    question = _find_question(catalog, payload.question_key)
    now = datetime.now(UTC)

    try:
        if payload.declined:
            turn = orchestrator.decline_attribute(
                session_id=payload.session_id, key=question.attribute_key, now=now
            )
        else:
            value = None if payload.unknown else payload.value
            turn = orchestrator.confirm_attribute(
                session_id=payload.session_id,
                key=question.attribute_key,
                value=value,
                now=now,
            )
    except KeyError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error

    return _turn_response(turn, gateway=gateway, catalog=catalog, locale=turn.state.locale)
