from pydantic import BaseModel, Field

from vesta_api.api.schemas import CandidateResponse
from vesta_api.domain.models import Need


class InterpretRequest(BaseModel):
    free_text: str = Field(min_length=1, max_length=2000)
    language: str = Field(default="de", min_length=2, max_length=12)


class AttributeProposalResponse(BaseModel):
    key: str
    value: object | None
    confidence: str


class InterpretResponse(BaseModel):
    need_key: str | None
    proposals: list[AttributeProposalResponse]
    requires_confirmation: list[str]
    ambiguities: list[str]
    source: str


class StartDialogueRequest(BaseModel):
    need: Need
    language: str = Field(default="de", min_length=2, max_length=12)


class AnswerRequest(BaseModel):
    session_id: str
    question_key: str
    value: object | None = None
    unknown: bool = False
    declined: bool = False


class QuestionOptionResponse(BaseModel):
    value: str
    label: str


class RenderedQuestionResponse(BaseModel):
    question_key: str
    attribute_key: str
    text: str
    help_text: str | None
    unknown_label: str
    decline_label: str
    options: list[QuestionOptionResponse]
    source: str


class ExplanationReasonResponse(BaseModel):
    text: str
    supported_by: list[str]


class ExplanationResponse(BaseModel):
    headline: str
    reasons: list[ExplanationReasonResponse]
    clarification: ExplanationReasonResponse | None
    next_action: str | None
    source: str


class ExplainedCandidateResponse(BaseModel):
    candidate: CandidateResponse
    explanation: ExplanationResponse | None


class DialogueTurnResponse(BaseModel):
    session_id: str
    ai_mode: str
    question: RenderedQuestionResponse | None
    candidates: list[ExplainedCandidateResponse]
    human_handoff_required: bool
    handoff_reason: str | None
    disclaimer: str
