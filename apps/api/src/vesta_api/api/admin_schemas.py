import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator

from vesta_api.domain.admin_catalog_models import (
    SUPPORTED_CATEGORY_ICONS,
    SUPPORTED_CATEGORY_LOCALES,
)
from vesta_api.domain.models import normalize_accepted_genders


class AdminLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=1, max_length=200)


class AiAuditEntrySummaryResponse(BaseModel):
    id: str
    session_id: str | None
    port: str
    provider: str
    model: str
    outcome: str
    created_at: datetime


class AiAuditLogListResponse(BaseModel):
    entries: list[AiAuditEntrySummaryResponse]


class AiAuditEntryDetailResponse(BaseModel):
    id: str
    session_id: str | None
    port: str
    provider: str
    model: str
    outcome: str
    violations: list[str]
    error_detail: str | None
    request_text: str
    response_text: str | None
    created_at: datetime


class WorkflowAuditSummaryResponse(BaseModel):
    workflow_id: str
    started_at: datetime
    updated_at: datetime
    input_preview: str
    event_count: int
    ai_call_count: int
    complete: bool
    has_fallback: bool


class WorkflowAuditListResponse(BaseModel):
    workflows: list[WorkflowAuditSummaryResponse]


class WorkflowAuditStepResponse(BaseModel):
    id: str
    kind: str
    event_type: str
    label: str
    summary: str
    created_at: datetime
    provider: str | None = None
    model: str | None = None
    outcome: str | None = None
    details: dict[str, Any]


class WorkflowAuditDetailResponse(BaseModel):
    workflow_id: str
    started_at: datetime
    updated_at: datetime
    complete: bool
    steps: list[WorkflowAuditStepResponse]


class IngestionRunResponse(BaseModel):
    id: str
    offer_slug: str
    source_url: str
    status: str
    http_status: int | None
    content_sha256: str | None
    missing_evidence: list[str]
    error: str | None
    checked_at: datetime


class IngestionRunListResponse(BaseModel):
    runs: list[IngestionRunResponse]


class AdminOfferResponse(BaseModel):
    id: str
    slug: str
    name: str
    organization_name: str
    summary: str
    needs: list[str]
    languages: list[str]
    access_rules: dict[str, Any]
    availability: str
    lifecycle: Literal["draft", "published", "archived"]
    origin: Literal["imported", "manual"]
    management_mode: Literal["source", "manual"]
    revision: int
    is_demo: bool
    contact_note: str
    address: str | None
    latitude: float | None
    longitude: float | None
    source_label: str
    source_url: str | None
    verified_by: str
    verified_at: datetime
    expires_at: datetime
    updated_at: datetime
    localizations: dict[str, "OfferLocalizationResponse"] = Field(default_factory=dict)


class OfferLocalizationResponse(BaseModel):
    locale: str
    name: str
    summary: str
    contact_note: str
    status: Literal["machine_draft", "reviewed"]
    revision: int
    reviewed_by: str | None
    reviewed_at: datetime | None
    updated_at: datetime | None


class OfferLocalizationWriteRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    summary: str = Field(min_length=1, max_length=1_000)
    contact_note: str = Field(min_length=1, max_length=2_000)
    status: Literal["machine_draft", "reviewed"]
    revision: int | None = Field(default=None, ge=1)


class OfferImportJobCreateRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2_000)


class OfferImportJobResponse(BaseModel):
    id: str
    source_url: str
    normalized_url: str
    status: Literal[
        "queued",
        "fetching",
        "extracting",
        "translating",
        "ready_for_review",
        "failed",
    ]
    requested_by: str
    offer_id: str | None
    source_language: str | None
    content_sha256: str | None
    extracted_data: dict[str, Any] | None
    evidence: list[dict[str, str]]
    duplicate_offer_ids: list[str]
    error_code: str | None
    error_detail: str | None
    attempts: int
    lease_expires_at: datetime | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    updated_at: datetime


class OfferImportJobListResponse(BaseModel):
    jobs: list[OfferImportJobResponse]
    limit: int
    offset: int


class AdminOfferListResponse(BaseModel):
    offers: list[AdminOfferResponse]
    total: int
    limit: int
    offset: int


class CategoryLocalizationInput(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=300)


class AdminCategoryWriteRequest(BaseModel):
    icon: str
    status: Literal["draft", "published", "archived"] = "draft"
    sort_order: int = Field(ge=0, le=10_000)
    localizations: dict[str, CategoryLocalizationInput]
    revision: int | None = Field(default=None, ge=1)

    @field_validator("icon")
    @classmethod
    def validate_icon(cls, value: str) -> str:
        if value not in SUPPORTED_CATEGORY_ICONS:
            raise ValueError("unknown_category_icon")
        return value

    @model_validator(mode="after")
    def validate_locales(self) -> "AdminCategoryWriteRequest":
        expected = set(SUPPORTED_CATEGORY_LOCALES)
        actual = set(self.localizations)
        if actual != expected:
            missing = ",".join(sorted(expected - actual)) or "none"
            unexpected = ",".join(sorted(actual - expected)) or "none"
            raise ValueError(
                f"category_locales_invalid:missing={missing}:unexpected={unexpected}"
            )
        return self


class AdminCategoryResponse(BaseModel):
    key: str
    icon: str
    status: str
    sort_order: int
    revision: int
    localizations: dict[str, dict[str, str]]
    offer_count: int
    created_at: datetime | None
    updated_at: datetime | None


class AdminCategoryListResponse(BaseModel):
    categories: list[AdminCategoryResponse]


class AdminAccessRulesInput(BaseModel):
    accepts_dogs: bool | None = None
    identity_document_required: bool | None = None
    accepted_genders: list[str] = Field(default_factory=list, max_length=20)
    minimum_age: int | None = Field(default=None, ge=0, le=120)
    maximum_age: int | None = Field(default=None, ge=0, le=120)

    @field_validator("accepted_genders")
    @classmethod
    def normalize_gender_restrictions(cls, values: list[str]) -> list[str]:
        return list(normalize_accepted_genders(values))

    @model_validator(mode="after")
    def validate_age_range(self) -> "AdminAccessRulesInput":
        if (
            self.minimum_age is not None
            and self.maximum_age is not None
            and self.minimum_age > self.maximum_age
        ):
            raise ValueError("minimum_age_must_not_exceed_maximum_age")
        return self


class AdminOfferWriteRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    organization_name: str = Field(min_length=1, max_length=200)
    summary: str = Field(min_length=1, max_length=1_000)
    needs: list[str] = Field(min_length=1, max_length=50)
    languages: list[str] = Field(min_length=1, max_length=50)
    access_rules: AdminAccessRulesInput = Field(default_factory=AdminAccessRulesInput)
    availability: Literal["confirmed", "call_to_confirm", "unknown"]
    contact_note: str = Field(min_length=1, max_length=2_000)
    address: str | None = Field(default=None, max_length=500)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    source_label: str = Field(min_length=1, max_length=300)
    source_url: HttpUrl | None = None
    expires_at: datetime
    slug: str | None = Field(default=None, pattern=r"^[a-z0-9-]+$", max_length=200)
    management_mode: Literal["source", "manual"] = "manual"
    revision: int | None = Field(default=None, ge=1)

    @field_validator("needs")
    @classmethod
    def validate_needs(cls, values: list[str]) -> list[str]:
        pattern = r"^[a-z0-9_-]{1,100}$"
        if any(not re.fullmatch(pattern, value) for value in values):
            raise ValueError("invalid_category_key")
        return values

    @model_validator(mode="after")
    def validate_location(self) -> "AdminOfferWriteRequest":
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude_and_longitude_must_be_set_together")
        if len(set(self.needs)) != len(self.needs):
            raise ValueError("duplicate_categories_are_not_allowed")
        normalized_languages = [value.strip().lower() for value in self.languages]
        if any(not value or len(value) > 12 for value in normalized_languages):
            raise ValueError("invalid_language_code")
        if self.expires_at.tzinfo is None:
            raise ValueError("expires_at_requires_timezone")
        self.languages = normalized_languages
        return self


class AdminOfferLifecycleRequest(BaseModel):
    lifecycle: Literal["draft", "published", "archived"]
    revision: int = Field(ge=1)


class ImportSettingsResponse(BaseModel):
    automatic_enabled: bool
    revision: int
    updated_at: datetime
    updated_by: str | None


class ImportSettingsUpdateRequest(BaseModel):
    automatic_enabled: bool
    revision: int = Field(ge=1)


class AdminChangeResponse(BaseModel):
    id: str
    admin_username: str
    entity_type: str
    entity_id: str
    action: str
    before_data: dict[str, Any] | None
    after_data: dict[str, Any] | None
    created_at: datetime


class AdminChangeListResponse(BaseModel):
    changes: list[AdminChangeResponse]
