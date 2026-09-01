from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

CategoryStatus = Literal["draft", "published", "archived"]
OfferOrigin = Literal["imported", "manual"]
OfferManagementMode = Literal["source", "manual"]
OfferLifecycle = Literal["draft", "published", "archived"]

SUPPORTED_CATEGORY_LOCALES = ("de", "fr", "en", "es", "pt", "ary")
SUPPORTED_CATEGORY_ICONS = (
    "home",
    "food",
    "book",
    "health",
    "clothing",
    "shower",
    "support",
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
    offers: dict[str, AdminOffer] = field(default_factory=dict)
    changes: list[AdminChange] = field(default_factory=list)
