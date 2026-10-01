from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

CategoryStatus = Literal["draft", "published", "archived"]
OfferOrigin = Literal["imported", "manual"]
OfferManagementMode = Literal["source", "manual"]
OfferLifecycle = Literal["draft", "published", "archived"]
OfferLocalizationStatus = Literal["machine_draft", "reviewed"]
ServiceStatus = Literal["draft", "published", "archived"]
ServiceGroup = Literal["basic_needs", "counselling", "addiction"]
ProviderApprovalStatus = Literal[
    "legacy_pending", "pending", "approved", "declined"
]

SUPPORTED_CATEGORY_LOCALES = ("de", "fr", "en", "es", "pt", "ary")
SUPPORTED_CATEGORY_ICONS = (
    "home",
    "food",
    "book",
    "health",
    "clothing",
    "shower",
    "support",
    "daytime",
    "other",
)
SUPPORTED_SERVICE_ICONS = (
    "meal",
    "groceries",
    "shower",
    "laundry",
    "clothing",
    "toilet",
    "locker",
    "chat",
    "housing",
    "wallet",
    "health",
    "mental-health",
    "legal",
    "support",
    "alcohol",
    "medication",
    "substances",
    "multiple",
    "question",
    "daytime",
    "other",
)


@dataclass(frozen=True)
class AdminCategory:
    key: str
    icon: str
    status: CategoryStatus
    sort_order: int
    revision: int
    localizations: dict[str, dict[str, str]]
    offer_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class CategoryWrite:
    icon: str
    status: CategoryStatus
    sort_order: int
    localizations: dict[str, dict[str, str]]
    revision: int | None = None


@dataclass(frozen=True)
class AdminServiceDefinition:
    key: str
    service_group: ServiceGroup
    icon: str
    status: ServiceStatus
    sort_order: int
    revision: int
    localizations: dict[str, dict[str, str]]
    offer_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class ServiceDefinitionWrite:
    service_group: ServiceGroup
    icon: str
    status: ServiceStatus
    sort_order: int
    localizations: dict[str, dict[str, str]]
    revision: int | None = None


@dataclass(frozen=True)
class AdminOffer:
    id: str
    slug: str
    name: str
    organization_name: str
    summary: str
    needs: tuple[str, ...]
    languages: tuple[str, ...]
    access_rules: dict[str, object]
    availability: str
    contact_note: str
    address: str | None
    latitude: float | None
    longitude: float | None
    source_label: str
    source_url: str | None
    verified_by: str
    verified_at: datetime
    expires_at: datetime
    origin: OfferOrigin
    management_mode: OfferManagementMode
    lifecycle: OfferLifecycle
    revision: int
    is_demo: bool
    updated_at: datetime
    localizations: dict[str, "OfferLocalization"] = field(default_factory=dict)
    services: tuple[str, ...] = ()
    provider_approval_status: ProviderApprovalStatus = "approved"
    provider_approval_reference: str | None = None
    provider_approval_scope: str | None = None
    provider_approval_evidence: str | None = None
    provider_approval_deadline: datetime | None = None
    source_draft: dict[str, object] | None = None
    source_draft_created_at: datetime | None = None


@dataclass(frozen=True)
class OfferLocalization:
    locale: str
    name: str
    summary: str
    contact_note: str
    status: OfferLocalizationStatus
    revision: int
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class OfferLocalizationWrite:
    name: str
    summary: str
    contact_note: str
    status: OfferLocalizationStatus
    revision: int | None = None


@dataclass(frozen=True)
class OfferWrite:
    name: str
    organization_name: str
    summary: str
    needs: tuple[str, ...]
    languages: tuple[str, ...]
    access_rules: dict[str, object]
    availability: str
    contact_note: str
    address: str | None
    latitude: float | None
    longitude: float | None
    source_label: str
    source_url: str | None
    expires_at: datetime
    slug: str | None = None
    management_mode: OfferManagementMode = "manual"
    revision: int | None = None
    services: tuple[str, ...] = ()
    provider_approval_status: ProviderApprovalStatus = "pending"
    provider_approval_reference: str | None = None
    provider_approval_scope: str | None = None
    provider_approval_evidence: str | None = None


@dataclass(frozen=True)
class ImportSettings:
    automatic_enabled: bool
    revision: int
    updated_at: datetime
    updated_by: str | None


@dataclass(frozen=True)
class AdminChange:
    id: str
    admin_username: str
    entity_type: str
    entity_id: str
    action: str
    before_data: dict[str, object] | None
    after_data: dict[str, object] | None
    created_at: datetime


@dataclass
class AdminCatalogState:
    categories: dict[str, AdminCategory] = field(default_factory=dict)
    services: dict[str, AdminServiceDefinition] = field(default_factory=dict)
    offers: dict[str, AdminOffer] = field(default_factory=dict)
    changes: list[AdminChange] = field(default_factory=list)
