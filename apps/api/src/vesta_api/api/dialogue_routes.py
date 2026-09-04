import json
import logging
import secrets
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from vesta_api.ai.fallback import TemplateGateway
from vesta_api.ai.gateway import AiGateway
from vesta_api.api.dialogue_schemas import (
    AnswerRequest,
    AttributeProposalResponse,
    DialogueTurnResponse,
    ExplainedCandidateResponse,
    ExplanationReasonResponse,
    ExplanationResponse,
    HandoffResourceResponse,
    InterpretRequest,
    InterpretResponse,
    QuestionOptionResponse,
    RenderedQuestionResponse,
    StartDialogueRequest,
)
from vesta_api.api.localization import disclaimer_for
from vesta_api.api.schemas import candidate_to_response
from vesta_api.domain.ai_models import ExplanationResult
from vesta_api.domain.dialogue_catalog import QuestionDefinition
from vesta_api.domain.models import MatchResult
from vesta_api.domain.workflow_audit_models import (
    NewWorkflowAuditEvent,
    WorkflowStage,
)
from vesta_api.repositories.dialogue_catalog import DialogueCatalogRepository
from vesta_api.repositories.workflow_audit_log import WorkflowAuditLogRepository
from vesta_api.services.dialogue_orchestrator import DialogueOrchestrator, DialogueTurnResult
from vesta_api.services.result_grounding import build_grounding_bundle
from vesta_api.services.safety import detect_safety_signal, safety_resources

router = APIRouter(prefix="/v1/dialogue")
logger = logging.getLogger(__name__)

def _validated_answer_value(
    question: QuestionDefinition,
    payload: AnswerRequest,
) -> object | None:
    if payload.declined and payload.unknown:
        raise HTTPException(status_code=422, detail="answer_state_is_ambiguous")
    if payload.declined or payload.unknown:
        if payload.value is not None:
            raise HTTPException(status_code=422, detail="answer_value_must_be_empty")
        return None

    if question.answer_type == "yes_no_unknown" and not isinstance(payload.value, bool):
        raise HTTPException(status_code=422, detail="boolean_answer_required")
    if question.answer_type == "single_choice" and not isinstance(payload.value, str):
        raise HTTPException(status_code=422, detail="choice_answer_required")

    return payload.value


def dialogue_orchestrator(request: Request) -> DialogueOrchestrator:
    return request.app.state.dialogue_orchestrator


def ai_gateway(request: Request) -> AiGateway:
    return request.app.state.ai_gateway


def dialogue_catalog(request: Request) -> DialogueCatalogRepository:
    return request.app.state.dialogue_catalog


def workflow_audit_log(request: Request) -> WorkflowAuditLogRepository:
    return request.app.state.workflow_audit_log


def _record_workflow_event(
    repository: WorkflowAuditLogRepository,
    *,
    workflow_id: str,
    stage: WorkflowStage,
    event_type: str,
    summary: str,
    payload: dict[str, object],
) -> None:
    try:
        repository.record(
            NewWorkflowAuditEvent(
                workflow_id=workflow_id,
                stage=stage,
                event_type=event_type,
                summary=summary,
                payload=payload,
            )
        )
    except Exception:
        logger.exception(
            "workflow_audit_record_failed: workflow_id=%s stage=%s event_type=%s",
            workflow_id,
            stage,
            event_type,
        )


@router.post("/interpret", response_model=InterpretResponse)
def interpret(
    payload: InterpretRequest,
    orchestrator: Annotated[DialogueOrchestrator, Depends(dialogue_orchestrator)],
    gateway: Annotated[AiGateway, Depends(ai_gateway)],
    catalog: Annotated[DialogueCatalogRepository, Depends(dialogue_catalog)],
    workflow_log: Annotated[WorkflowAuditLogRepository, Depends(workflow_audit_log)],
) -> InterpretResponse:
    workflow_id = secrets.token_urlsafe(18)
    _record_workflow_event(
        workflow_log,
        workflow_id=workflow_id,
        stage="input",
        event_type="free_text_submitted",
        summary=f"Eingabe: {payload.free_text[:240]}",
        payload={"free_text": payload.free_text, "language": payload.language},
    )
    safety_signal = detect_safety_signal(payload.free_text, payload.language)
    if safety_signal is not None:
        _record_workflow_event(
            workflow_log,
            workflow_id=workflow_id,
            stage="system",
            event_type="safety_signal_detected",
            summary="Deterministische Sicherheitsregel startet den Opferhilfe-Dialog.",
            payload={
                "safety_code": safety_signal.code,
                "detector_version": "2026-09-02",
            },
        )
        safety_turn = orchestrator.start_safety_review(
            locale=payload.language,
            now=datetime.now(UTC),
            session_id=workflow_id,
        )
        return InterpretResponse(
            workflow_id=workflow_id,
            need_key="victim_support",
            proposals=[],
            requires_confirmation=[],
            ambiguities=[],
            source="deterministic_safety",
            outcome="safety",
            safety_turn=_turn_response(
                safety_turn,
                gateway=gateway,
                catalog=catalog,
                locale=payload.language,
                workflow_log=workflow_log,
                location_used=False,
            ),
        )
    result = gateway.interpret(
        free_text=payload.free_text,
        locale=payload.language,
        needs=catalog.list_needs(),
        attributes=catalog.list_attributes(),
        session_id=workflow_id,
    )
    _record_workflow_event(
        workflow_log,
        workflow_id=workflow_id,
        stage="system",
        event_type="interpretation_validated",
        summary=(
            f"Systemlogik akzeptiert den Bedarf «{result.need_key}»."
            if result.need_key
            else "Systemlogik konnte noch keinen eindeutigen Bedarf ableiten."
        ),
        payload={
            "need_key": result.need_key,
            "proposals": [
                {
                    "key": proposal.key,
                    "value": proposal.value,
                    "confidence": proposal.confidence,
                }
                for proposal in result.proposals
            ],
            "requires_confirmation": list(result.requires_confirmation),
            "ambiguities": list(result.ambiguities),
            "source": result.source,
        },
    )
    return InterpretResponse(
        workflow_id=workflow_id,
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
    if not match_result.candidates:
        return []
    bundles = [build_grounding_bundle(candidate) for candidate in match_result.candidates]

    def cache_key(index: int) -> tuple[object, ...]:
        return _grounding_cache_key(bundles[index], locale)

    first_index_by_key: dict[tuple[object, ...], int] = {}
    for index in range(len(bundles)):
        first_index_by_key.setdefault(cache_key(index), index)

    def explain_index(index: int) -> ExplanationResult:
        return gateway.explain(
            bundle=bundles[index], locale=locale, session_id=session_id
        )

    explanations: dict[tuple[object, ...], ExplanationResult] = {}
    with ThreadPoolExecutor(max_workers=min(3, len(first_index_by_key))) as executor:
        futures = {
            key: executor.submit(explain_index, index)
            for key, index in first_index_by_key.items()
        }
        for key, future in futures.items():
            try:
                explanations[key] = future.result()
            except Exception:
                logger.exception("candidate_explanation_failed: session_id=%s", session_id)
                fallback_index = first_index_by_key[key]
                explanations[key] = TemplateGateway().explain(
                    bundle=bundles[fallback_index],
                    locale=locale,
                )

    explained: list[ExplainedCandidateResponse] = []
    for index, candidate in enumerate(match_result.candidates):
        explanation = explanations[cache_key(index)]
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


def _grounding_cache_key(bundle: object, locale: str) -> tuple[object, ...]:
    return (
        locale,
        tuple(
            (fact.id, fact.type, repr(fact.value))
            for fact in bundle.facts  # type: ignore[attr-defined]
        ),
        bundle.match_reasons,  # type: ignore[attr-defined]
        bundle.uncertainties,  # type: ignore[attr-defined]
        bundle.allowed_next_actions,  # type: ignore[attr-defined]
        bundle.forbidden_claims,  # type: ignore[attr-defined]
    )


def _record_explanation_deduplication(
    match_result: MatchResult | None,
    *,
    locale: str,
    workflow_log: WorkflowAuditLogRepository,
    workflow_id: str,
) -> None:
    if match_result is None or len(match_result.candidates) < 2:
        return
    bundles = [build_grounding_bundle(candidate) for candidate in match_result.candidates]
    unique_count = len({_grounding_cache_key(bundle, locale) for bundle in bundles})
    if unique_count == len(bundles):
        return
    _record_workflow_event(
        workflow_log,
        workflow_id=workflow_id,
        stage="system",
        event_type="ai_explanations_deduplicated",
        summary=(
            f"Systemlogik fasst {len(bundles)} Faktenpakete zu "
            f"{unique_count} AI-Erklärungen zusammen."
        ),
        payload={
            "candidate_count": len(bundles),
            "unique_fact_bundle_count": unique_count,
        },
    )


def _question_text(question: QuestionDefinition, locale: str) -> str:
    localization = question.localizations.get(locale) or question.localizations.get("de")
    if localization is None:
        return question.key
    return localization.get("canonical_text", question.key)


def _record_system_logic(
    turn: DialogueTurnResult,
    *,
    workflow_log: WorkflowAuditLogRepository,
    locale: str,
    location_used: bool,
) -> None:
    workflow_id = turn.state.session_id
    state_payload: dict[str, object] = {
        "need": turn.state.need,
        "locale": turn.state.locale,
        "attributes": [
            {
                "key": attribute.key,
                "value": attribute.value,
                "status": attribute.status,
                "source": attribute.source,
            }
            for attribute in turn.state.attributes
        ],
        "safety_status": turn.state.safety_status,
        "location_used": location_used,
    }

    if turn.question is not None:
        canonical_text = _question_text(turn.question, locale)
        _record_workflow_event(
            workflow_log,
            workflow_id=workflow_id,
            stage="system",
            event_type="question_selected",
            summary=f"Systemlogik wählt die nächste Frage: {canonical_text}",
            payload={
                **state_payload,
                "question": {
                    "key": turn.question.key,
                    "attribute_key": turn.question.attribute_key,
                    "answer_type": turn.question.answer_type,
                    "canonical_text": canonical_text,
                },
            },
        )
        return

    if turn.match_result is not None:
        candidate_count = len(turn.match_result.candidates)
        _record_workflow_event(
            workflow_log,
            workflow_id=workflow_id,
            stage="system",
            event_type="matching_completed",
            summary=(
                f"Systemlogik findet {candidate_count} "
                f"{'passendes Angebot' if candidate_count == 1 else 'passende Angebote'}."
            ),
            payload={
                **state_payload,
                "matching": {
                    "candidates": [
                        {
                            "rank": rank,
                            "offer_id": candidate.offer.id,
                            "offer_name": candidate.offer.name,
                            "reasons": list(candidate.reasons),
                            "uncertainties": list(candidate.uncertainties),
                            "distance_band": _distance_band(candidate.distance_meters),
                        }
                        for rank, candidate in enumerate(
                            turn.match_result.candidates, start=1
                        )
                    ],
                    "excluded_offers": [
                        {
                            "offer_id": excluded.offer_id,
                            "offer_name": excluded.offer_name,
                            "reason": excluded.reason,
                        }
                        for excluded in turn.match_result.excluded_offers
                    ],
                    "human_handoff_required": (
                        turn.match_result.human_handoff_required
                    ),
                    "handoff_reason": turn.match_result.handoff_reason,
                },
            },
        )
        return

    _record_workflow_event(
        workflow_log,
        workflow_id=workflow_id,
        stage="system",
        event_type="dialogue_state_evaluated",
        summary="Systemlogik hat den aktuellen Dialogzustand ausgewertet.",
        payload=state_payload,
    )


def _output_summary(response: DialogueTurnResponse) -> str:
    if response.question is not None:
        return f"Antwort an die Person: {response.question.text}"
    if response.candidates:
        candidate_count = len(response.candidates)
        return (
            f"Antwort an die Person enthält {candidate_count} "
            f"{'passendes Angebot' if candidate_count == 1 else 'passende Angebote'}."
        )
    if response.human_handoff_required:
        return "Antwort an die Person empfiehlt eine menschliche Weiterleitung."
    return "Antwort an die Person enthält derzeit kein passendes Angebot."


def _audit_output_payload(
    response: DialogueTurnResponse,
    *,
    location_used: bool,
) -> dict[str, object]:
    """Retain workflow shape without persisting location-derived distances."""

    payload = response.model_dump(mode="json")
    candidates = payload.get("candidates")
    if isinstance(candidates, list):
        for item in candidates:
            if not isinstance(item, dict):
                continue
            candidate = item.get("candidate")
            if isinstance(candidate, dict):
                candidate.pop("distance_meters", None)
                offer = candidate.get("offer")
                if isinstance(offer, dict):
                    offer.pop("directions_url", None)
    payload["location_used"] = location_used
    return payload


def _distance_band(distance_meters: int | None) -> str:
    if distance_meters is None:
        return "unknown"
    if distance_meters < 1_000:
        return "under_1_km"
    if distance_meters < 5_000:
        return "1_to_5_km"
    if distance_meters < 10_000:
        return "5_to_10_km"
    return "over_10_km"


def _turn_response(
    turn: DialogueTurnResult,
    *,
    gateway: AiGateway,
    catalog: DialogueCatalogRepository,
    locale: str,
    workflow_log: WorkflowAuditLogRepository,
    location_used: bool,
) -> DialogueTurnResponse:
    _record_system_logic(
        turn,
        workflow_log=workflow_log,
        locale=locale,
        location_used=location_used,
    )
    _record_explanation_deduplication(
        turn.match_result,
        locale=locale,
        workflow_log=workflow_log,
        workflow_id=turn.state.session_id,
    )
    handoff_reason = turn.match_result.handoff_reason if turn.match_result else None
    resources = (
        safety_resources(
            locale,
            immediate_danger=handoff_reason == "immediate_danger",
        )
        if handoff_reason in ("immediate_danger", "victim_support_recommended")
        else ()
    )
    response = DialogueTurnResponse(
        session_id=turn.state.session_id,
        ai_mode=gateway.mode,
        outcome=(
            "question"
            if turn.question is not None
            else "handoff"
            if turn.match_result and turn.match_result.human_handoff_required
            else "matches"
            if turn.match_result and turn.match_result.candidates
            else "no_match"
        ),
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
        handoff_reason=handoff_reason,
        handoff_resources=[HandoffResourceResponse(**resource) for resource in resources],
        disclaimer=disclaimer_for(locale),
    )
    _record_workflow_event(
        workflow_log,
        workflow_id=turn.state.session_id,
        stage="output",
        event_type="public_response_returned",
        summary=_output_summary(response),
        payload=_audit_output_payload(response, location_used=location_used),
    )
    return response


@router.post("/start", response_model=DialogueTurnResponse)
def start(
    payload: StartDialogueRequest,
    orchestrator: Annotated[DialogueOrchestrator, Depends(dialogue_orchestrator)],
    gateway: Annotated[AiGateway, Depends(ai_gateway)],
    catalog: Annotated[DialogueCatalogRepository, Depends(dialogue_catalog)],
    workflow_log: Annotated[WorkflowAuditLogRepository, Depends(workflow_audit_log)],
) -> DialogueTurnResponse:
    if payload.need not in {need.key for need in catalog.list_needs()}:
        raise HTTPException(status_code=422, detail="unknown_or_inactive_category")
    turn = orchestrator.start(
        locale=payload.language,
        need=payload.need,
        now=datetime.now(UTC),
        session_id=payload.workflow_id,
        user_location=(
            payload.user_location.to_domain()
            if payload.user_location is not None
            else None
        ),
    )
    _record_workflow_event(
        workflow_log,
        workflow_id=turn.state.session_id,
        stage="input",
        event_type="need_selected",
        summary=f"Eingabe: Bedarf «{payload.need}» ausgewählt.",
        payload={"need": payload.need, "language": payload.language},
    )
    return _turn_response(
        turn,
        gateway=gateway,
        catalog=catalog,
        locale=payload.language,
        workflow_log=workflow_log,
        location_used=payload.user_location is not None,
    )


@router.post("/answer", response_model=DialogueTurnResponse)
def answer(
    payload: AnswerRequest,
    orchestrator: Annotated[DialogueOrchestrator, Depends(dialogue_orchestrator)],
    gateway: Annotated[AiGateway, Depends(ai_gateway)],
    catalog: Annotated[DialogueCatalogRepository, Depends(dialogue_catalog)],
    workflow_log: Annotated[WorkflowAuditLogRepository, Depends(workflow_audit_log)],
) -> DialogueTurnResponse:
    question = _find_question(catalog, payload.question_key)
    validated_value = _validated_answer_value(question, payload)
    now = datetime.now(UTC)

    try:
        if question.attribute_key == "safety.immediate_danger":
            answer_status = (
                "declined"
                if payload.declined
                else "unknown"
                if payload.unknown
                else "confirmed"
            )
            immediate_danger = (
                payload.value if isinstance(payload.value, bool) else None
            )
            turn = orchestrator.resolve_safety_review(
                session_id=payload.session_id,
                immediate_danger=immediate_danger,
                status=answer_status,
                now=now,
            )
        elif payload.declined:
            turn = orchestrator.decline_attribute(
                session_id=payload.session_id,
                key=question.attribute_key,
                now=now,
                user_location=(
                    payload.user_location.to_domain()
                    if payload.user_location is not None
                    else None
                ),
            )
        elif payload.unknown:
            turn = orchestrator.mark_attribute_unknown(
                session_id=payload.session_id,
                key=question.attribute_key,
                now=now,
                user_location=(
                    payload.user_location.to_domain()
                    if payload.user_location is not None
                    else None
                ),
            )
        else:
            turn = orchestrator.confirm_attribute(
                session_id=payload.session_id,
                key=question.attribute_key,
                value=validated_value,
                now=now,
                user_location=(
                    payload.user_location.to_domain()
                    if payload.user_location is not None
                    else None
                ),
            )
    except KeyError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error

    if payload.declined:
        answer_summary = (
            f"Eingabe: Antwort auf «{_question_text(question, turn.state.locale)}» "
            "wurde abgelehnt."
        )
    elif payload.unknown:
        answer_summary = (
            f"Eingabe: Antwort auf «{_question_text(question, turn.state.locale)}» "
            "ist unbekannt."
        )
    else:
        answer_summary = (
            f"Eingabe: «{_question_text(question, turn.state.locale)}» = "
            f"{json.dumps(payload.value, ensure_ascii=False)}"
        )
    _record_workflow_event(
        workflow_log,
        workflow_id=turn.state.session_id,
        stage="input",
        event_type="answer_submitted",
        summary=answer_summary,
        payload={
            "question_key": payload.question_key,
            "attribute_key": question.attribute_key,
            "value": payload.value,
            "unknown": payload.unknown,
            "declined": payload.declined,
        },
    )

    return _turn_response(
        turn,
        gateway=gateway,
        catalog=catalog,
        locale=turn.state.locale,
        workflow_log=workflow_log,
        location_used=payload.user_location is not None,
    )
