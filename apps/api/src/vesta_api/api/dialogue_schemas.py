from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from vesta_api.api.schemas import CandidateResponse, UserLocationInput
from vesta_api.domain.models import ServiceTopic


class InterpretRequest(BaseModel):
    free_text: str = Field(min_length=1, max_length=2000)
    language: str = Field(default="de", min_length=2, max_length=12)


class AttributeProposalResponse(BaseModel):
    key: str
    value: object | None
    confidence: str


class InterpretResponse(BaseModel):
    workflow_id: str
    need_key: str | None
    proposals: list[AttributeProposalResponse]
    requires_confirmation: list[str]
    ambiguities: list[str]
    service_topics: list[ServiceTopic] = Field(default_factory=list)
    source: str
    outcome: Literal["interpreted", "safety"] = "interpreted"
    safety_turn: DialogueTurnResponse | None = None


class StartDialogueRequest(BaseModel):
    need: str = Field(pattern=r"^[a-z0-9_-]+$", min_length=1, max_length=100)
    language: str = Field(default="de", min_length=2, max_length=12)
    workflow_id: str | None = Field(default=None, min_length=8, max_length=200)
    user_location: UserLocationInput | None = None
    service_topics: list[ServiceTopic] = Field(default_factory=list, max_length=9)


class AnswerRequest(BaseModel):
    session_id: str
    question_key: str
    value: object | None = None
    unknown: bool = False
    declined: bool = False
    user_location: UserLocationInput | None = None


class QuestionOptionResponse(BaseModel):
    value: str
    label: str


class RenderedQuestionResponse(BaseModel):
    question_key: str
    attribute_key: str
    answer_type: str
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


class HandoffResourceResponse(BaseModel):
    kind: str
    name: str
    phone: str
    url: str
    description: str


class ExplainedCandidateResponse(BaseModel):
    candidate: CandidateResponse
    explanation: ExplanationResponse | None


class DialogueTurnResponse(BaseModel):
    session_id: str
    ai_mode: str
    outcome: Literal["question", "matches", "no_match", "handoff"]
    question: RenderedQuestionResponse | None
    candidates: list[ExplainedCandidateResponse]
    human_handoff_required: bool
    handoff_reason: str | None
    handoff_resources: list[HandoffResourceResponse] = Field(default_factory=list)
    disclaimer: str
