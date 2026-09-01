import json
import re
import unicodedata
from collections.abc import Mapping
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import uuid4

from sqlalchemy import Connection, Engine, text

from vesta_api.domain.admin_catalog_models import (
    AdminCatalogState,
    AdminCategory,
    AdminChange,
    AdminOffer,
    CategoryWrite,
    ImportSettings,
    OfferWrite,
)
from vesta_api.domain.admin_models import AdminUser
from vesta_api.repositories.database import create_database_engine


class CatalogNotFoundError(LookupError):
    pass


class CatalogConflictError(RuntimeError):
    pass


class CatalogValidationError(ValueError):
    pass


class AdminCatalogRepository(Protocol):
    def list_categories(self) -> tuple[AdminCategory, ...]: ...

    def create_category(self, write: CategoryWrite, admin: AdminUser) -> AdminCategory: ...

    def update_category(
        self, key: str, write: CategoryWrite, admin: AdminUser
    ) -> AdminCategory: ...

    def list_offers(self) -> tuple[AdminOffer, ...]: ...

    def get_offer(self, offer_id: str) -> AdminOffer | None: ...

    def create_offer(self, write: OfferWrite, admin: AdminUser) -> AdminOffer: ...

    def update_offer(
        self, offer_id: str, write: OfferWrite, admin: AdminUser
    ) -> AdminOffer: ...

    def set_offer_lifecycle(
        self,
        offer_id: str,
        lifecycle: str,
        revision: int,
        admin: AdminUser,
    ) -> AdminOffer: ...

    def get_import_settings(self) -> ImportSettings: ...

    def update_import_settings(
        self, enabled: bool, revision: int, admin: AdminUser
    ) -> ImportSettings: ...

    def list_changes(
        self, *, entity_type: str, entity_id: str, limit: int = 50
    ) -> tuple[AdminChange, ...]: ...

    def healthcheck(self) -> None: ...

    def close(self) -> None: ...


def _slugify(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-") or "category"


def _category_from_row(row: Mapping[str, Any]) -> AdminCategory:
    return AdminCategory(
        key=str(row["key"]),
        icon=str(row["icon"]),
        status=row["status"],
        sort_order=int(row["sort_order"]),
        revision=int(row["revision"]),
        localizations=dict(row["localizations"]),
        offer_count=int(row["offer_count"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _offer_from_row(row: Mapping[str, Any]) -> AdminOffer:
    contact = row["contact"] or {}
    archived_at = row["archived_at"]
    lifecycle = "archived" if archived_at else "published" if row["published"] else "draft"
    return AdminOffer(
        id=str(row["id"]),
        slug=str(row["slug"]),
        name=str(row["name"]),
        organization_name=str(row["organization_name"]),
        summary=str(row["summary"]),
        needs=tuple(row["needs"] or ()),
        languages=tuple(str(value).lower() for value in row["languages"]),
        access_rules=dict(row["access_rules"] or {}),
        availability=str(row["availability"]),
        contact_note=str(contact.get("note", "")),
        address=str(contact["address"]) if contact.get("address") else None,
        latitude=float(row["latitude"]) if row["latitude"] is not None else None,
        longitude=float(row["longitude"]) if row["longitude"] is not None else None,
        source_label=str(row["source_label"] or ""),
        source_url=str(row["source_url"]) if row["source_url"] else None,
        verified_by=str(row["verified_by"] or ""),
        verified_at=row["verified_at"],
        expires_at=row["expires_at"],
        origin=row["origin"],
        management_mode=row["management_mode"],
        lifecycle=lifecycle,
        revision=int(row["revision"]),
        is_demo=bool(row["is_demo"]),
        updated_at=row["updated_at"],
    )


_LIST_CATEGORIES = text(
    """
    SELECT n.key, n.icon, n.status, n.sort_order, n.revision,
           n.created_at, n.updated_at,
           COALESCE(jsonb_object_agg(
               nl.locale, jsonb_build_object(
                   'title', nl.title, 'description', nl.description
               )
           ) FILTER (WHERE nl.locale IS NOT NULL), '{}'::jsonb) AS localizations,
           COUNT(DISTINCT oc.offer_id) AS offer_count
    FROM need_definitions n
    LEFT JOIN need_localizations nl ON nl.need_id = n.id
    LEFT JOIN offer_categories oc ON oc.category = n.key
    GROUP BY n.id
    ORDER BY n.sort_order, n.key
    """
)

_LIST_ADMIN_OFFERS = text(
    """
    SELECT o.id::text AS id, o.slug, o.name, o.summary, o.languages,
           o.access_rules, o.contact, o.availability::text AS availability,
           o.published, o.is_demo, o.origin, o.management_mode,
           o.archived_at, o.revision, o.updated_at,
           ST_Y(o.location::geometry) AS latitude,
           ST_X(o.location::geometry) AS longitude,
           org.name AS organization_name,
           COALESCE(c.needs, ARRAY[]::text[]) AS needs,
           v.source_label, v.source_url, v.verified_by,
           COALESCE(v.verified_at, o.created_at) AS verified_at,
           COALESCE(v.expires_at, o.created_at) AS expires_at
    FROM offers o
    JOIN organizations org ON org.id = o.organization_id
    LEFT JOIN LATERAL (
        SELECT array_agg(category ORDER BY category) AS needs
        FROM offer_categories WHERE offer_id = o.id
    ) c ON TRUE
    LEFT JOIN LATERAL (
        SELECT source_label, source_url, verified_by, verified_at, expires_at
        FROM offer_verifications WHERE offer_id = o.id
        ORDER BY verified_at DESC, created_at DESC LIMIT 1
    ) v ON TRUE
    ORDER BY o.updated_at DESC, o.name
    """
)

_GET_ADMIN_OFFER = text(
    _LIST_ADMIN_OFFERS.text.replace(
        "ORDER BY o.updated_at DESC, o.name", "WHERE o.id = CAST(:offer_id AS uuid)"
    )
)


def _jsonable(value: object) -> object:
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "__dict__"):
        return {key: _jsonable(item) for key, item in vars(value).items()}
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _record_change(
    connection: Connection,
    *,
    admin: AdminUser,
    entity_type: str,
    entity_id: str,
    action: str,
    before: object | None,
    after: object | None,
) -> None:
    connection.execute(
        text(
            """
            INSERT INTO admin_change_log (
                id, admin_user_id, admin_username, entity_type,
                entity_id, action, before_data, after_data
            ) VALUES (
                :id, CAST(:admin_user_id AS uuid), :admin_username, :entity_type,
                :entity_id, :action, CAST(:before_data AS jsonb), CAST(:after_data AS jsonb)
            )
            """
        ),
        {
            "id": uuid4(),
            "admin_user_id": admin.id,
            "admin_username": admin.username,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "action": action,
            "before_data": json.dumps(_jsonable(before), ensure_ascii=False) if before else None,
            "after_data": json.dumps(_jsonable(after), ensure_ascii=False) if after else None,
        },
    )


class PostgresAdminCatalogRepository:
    def __init__(self, database_url: str, *, engine: Engine | None = None) -> None:
        self._engine = engine or create_database_engine(database_url)

    def list_categories(self) -> tuple[AdminCategory, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(_LIST_CATEGORIES).mappings().all()
        return tuple(_category_from_row(row) for row in rows)

    def _unique_key(self, connection: Connection, title: str) -> str:
        base = _slugify(title)
        candidate = base
        suffix = 2
        while connection.execute(
            text("SELECT 1 FROM need_definitions WHERE key = :key"), {"key": candidate}
        ).scalar_one_or_none():
            candidate = f"{base}-{suffix}"
            suffix += 1
        return candidate

    @staticmethod
    def _replace_localizations(
        connection: Connection, need_id: object, localizations: dict[str, dict[str, str]]
    ) -> None:
        connection.execute(
            text("DELETE FROM need_localizations WHERE need_id = :need_id"),
            {"need_id": need_id},
        )
        connection.execute(
            text(
                """
                INSERT INTO need_localizations (
                    need_id, locale, title, description
                ) VALUES (:need_id, :locale, :title, :description)
                """
            ),
            [
                {
                    "need_id": need_id,
                    "locale": locale,
                    "title": values["title"],
                    "description": values["description"],
                }
                for locale, values in localizations.items()
            ],
        )

    def create_category(self, write: CategoryWrite, admin: AdminUser) -> AdminCategory:
        with self._engine.begin() as connection:
            key = self._unique_key(connection, write.localizations["de"]["title"])
            need_id = uuid4()
            connection.execute(
                text(
                    """
                    INSERT INTO need_definitions (
                        id, key, status, sort_order, icon, revision, updated_at
                    ) VALUES (
                        :id, :key, :status, :sort_order, :icon, 1, now()
                    )
                    """
                ),
                {
                    "id": need_id,
                    "key": key,
                    "status": write.status,
                    "sort_order": write.sort_order,
                    "icon": write.icon,
                },
            )
            self._replace_localizations(connection, need_id, write.localizations)
            created = next(
                _category_from_row(row)
                for row in connection.execute(_LIST_CATEGORIES).mappings()
                if row["key"] == key
            )
            _record_change(
                connection,
                admin=admin,
                entity_type="category",
                entity_id=key,
                action="created",
                before=None,
                after=created,
            )
        return created

    def update_category(
        self, key: str, write: CategoryWrite, admin: AdminUser
    ) -> AdminCategory:
        assert write.revision is not None
        with self._engine.begin() as connection:
            rows = connection.execute(_LIST_CATEGORIES).mappings().all()
            before_row = next((row for row in rows if row["key"] == key), None)
            if before_row is None:
                raise CatalogNotFoundError("category_not_found")
            before = _category_from_row(before_row)
            if before.revision != write.revision:
                raise CatalogConflictError("category_was_modified")
            if write.status == "archived" and before.offer_count:
                raise CatalogValidationError("category_still_has_offers")
            result = connection.execute(
                text(
                    """
                    UPDATE need_definitions
                    SET icon = :icon, status = :status, sort_order = :sort_order,
                        revision = revision + 1, updated_at = now()
                    WHERE key = :key AND revision = :revision
                    RETURNING id
                    """
                ),
                {
                    "key": key,
                    "icon": write.icon,
                    "status": write.status,
                    "sort_order": write.sort_order,
                    "revision": write.revision,
                },
            ).scalar_one_or_none()
            if result is None:
                raise CatalogConflictError("category_was_modified")
            self._replace_localizations(connection, result, write.localizations)
            after = next(
                _category_from_row(row)
                for row in connection.execute(_LIST_CATEGORIES).mappings()
                if row["key"] == key
            )
            _record_change(
                connection,
                admin=admin,
                entity_type="category",
                entity_id=key,
                action="updated",
                before=before,
                after=after,
            )
        return after

    def list_offers(self) -> tuple[AdminOffer, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(_LIST_ADMIN_OFFERS).mappings().all()
        return tuple(_offer_from_row(row) for row in rows)

    def get_offer(self, offer_id: str) -> AdminOffer | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                _GET_ADMIN_OFFER, {"offer_id": offer_id}
            ).mappings().first()
        return _offer_from_row(row) if row is not None else None

    @staticmethod
    def _organization_id(connection: Connection, name: str) -> object:
        existing = connection.execute(
            text("SELECT id FROM organizations WHERE lower(name) = lower(:name) LIMIT 1"),
            {"name": name},
        ).scalar_one_or_none()
        if existing is not None:
            return existing
        organization_id = uuid4()
        connection.execute(
            text("INSERT INTO organizations (id, name) VALUES (:id, :name)"),
            {"id": organization_id, "name": name},
        )
        return organization_id

    def _unique_slug(self, connection: Connection, value: str) -> str:
        base = _slugify(value)
        candidate = base
        suffix = 2
        while connection.execute(
            text("SELECT 1 FROM offers WHERE slug = :slug"), {"slug": candidate}
        ).scalar_one_or_none():
            candidate = f"{base}-{suffix}"
            suffix += 1
        return candidate

    @staticmethod
    def _ensure_categories(connection: Connection, categories: tuple[str, ...]) -> None:
        rows = connection.execute(
            text(
                """
                SELECT key FROM need_definitions
                WHERE key = ANY(:keys) AND status = 'published'
                """
            ),
            {"keys": list(categories)},
        ).scalars().all()
        if set(rows) != set(categories):
            raise CatalogValidationError("unknown_or_inactive_category")

    @staticmethod
    def _write_categories(
        connection: Connection, offer_id: object, categories: tuple[str, ...]
    ) -> None:
        connection.execute(
            text("DELETE FROM offer_categories WHERE offer_id = :offer_id"),
            {"offer_id": offer_id},
        )
        connection.execute(
            text(
                "INSERT INTO offer_categories (offer_id, category) "
                "VALUES (:offer_id, :category)"
            ),
            [{"offer_id": offer_id, "category": item} for item in categories],
        )

    @staticmethod
    def _write_verification(
        connection: Connection, offer_id: object, write: OfferWrite, admin: AdminUser
    ) -> None:
        now = datetime.now(UTC)
        connection.execute(
            text(
                """
                INSERT INTO offer_verifications (
                    id, offer_id, source_label, source_url, verified_by,
                    verified_at, expires_at, notes
                ) VALUES (
                    :id, :offer_id, :source_label, :source_url, :verified_by,
                    :verified_at, :expires_at, :notes
                )
                """
            ),
            {
                "id": uuid4(),
                "offer_id": offer_id,
                "source_label": write.source_label,
                "source_url": write.source_url,
                "verified_by": admin.username,
                "verified_at": now,
                "expires_at": write.expires_at,
                "notes": "Manuell im geschützten Vesta-Adminbereich geprüft.",
            },
        )

    @staticmethod
    def _offer_parameters(write: OfferWrite) -> dict[str, object]:
        return {
            "name": write.name,
            "summary": write.summary,
            "languages": list(write.languages),
            "access_rules": json.dumps(write.access_rules, ensure_ascii=False),
            "contact": json.dumps(
                {"note": write.contact_note, "address": write.address},
                ensure_ascii=False,
            ),
            "latitude": write.latitude,
            "longitude": write.longitude,
            "availability": write.availability,
            "management_mode": write.management_mode,
        }

    def create_offer(self, write: OfferWrite, admin: AdminUser) -> AdminOffer:
        with self._engine.begin() as connection:
            self._ensure_categories(connection, write.needs)
            offer_id = uuid4()
            organization_id = self._organization_id(connection, write.organization_name)
            slug = self._unique_slug(connection, write.slug or write.name)
            connection.execute(
                text(
                    """
                    INSERT INTO offers (
                        id, organization_id, slug, name, summary, languages,
                        access_rules, contact, location, availability,
                        published, is_demo, origin, management_mode, revision,
                        updated_at
                    ) VALUES (
                        :id, :organization_id, :slug, :name, :summary, :languages,
                        CAST(:access_rules AS jsonb), CAST(:contact AS jsonb),
                        CASE WHEN CAST(:latitude AS double precision) IS NULL THEN NULL
                             ELSE ST_SetSRID(ST_MakePoint(
                                 CAST(:longitude AS double precision),
                                 CAST(:latitude AS double precision)
                             ), 4326)::geography END,
                        CAST(:availability AS offer_availability), false, false,
                        'manual', 'manual', 1, now()
                    )
                    """
                ),
                {
                    **self._offer_parameters(write),
                    "id": offer_id,
                    "organization_id": organization_id,
                    "slug": slug,
                },
            )
            self._write_categories(connection, offer_id, write.needs)
            self._write_verification(connection, offer_id, write, admin)
            row = connection.execute(
                _GET_ADMIN_OFFER, {"offer_id": str(offer_id)}
            ).mappings().one()
            created = _offer_from_row(row)
            _record_change(
                connection,
                admin=admin,
                entity_type="offer",
                entity_id=str(offer_id),
                action="created_as_draft",
                before=None,
                after=created,
            )
        return created

    def update_offer(
        self, offer_id: str, write: OfferWrite, admin: AdminUser
    ) -> AdminOffer:
        assert write.revision is not None
        with self._engine.begin() as connection:
            before_row = connection.execute(
                _GET_ADMIN_OFFER, {"offer_id": offer_id}
            ).mappings().first()
            if before_row is None:
                raise CatalogNotFoundError("offer_not_found")
            before = _offer_from_row(before_row)
            if before.revision != write.revision:
                raise CatalogConflictError("offer_was_modified")
            self._ensure_categories(connection, write.needs)
            organization_id = self._organization_id(connection, write.organization_name)
            result = connection.execute(
                text(
                    """
                    UPDATE offers SET
                        organization_id = :organization_id,
                        name = :name, summary = :summary, languages = :languages,
                        access_rules = CAST(:access_rules AS jsonb),
                        contact = CAST(:contact AS jsonb),
                        location = CASE
                            WHEN CAST(:latitude AS double precision) IS NULL THEN NULL
                            ELSE ST_SetSRID(ST_MakePoint(
                                CAST(:longitude AS double precision),
                                CAST(:latitude AS double precision)
                            ), 4326)::geography END,
                        availability = CAST(:availability AS offer_availability),
                        management_mode = :management_mode,
                        revision = revision + 1, updated_at = now()
                    WHERE id = CAST(:offer_id AS uuid) AND revision = :revision
                    RETURNING id
                    """
                ),
                {
                    **self._offer_parameters(write),
                    "organization_id": organization_id,
                    "offer_id": offer_id,
                    "revision": write.revision,
                },
            ).scalar_one_or_none()
            if result is None:
                raise CatalogConflictError("offer_was_modified")
            self._write_categories(connection, result, write.needs)
            self._write_verification(connection, result, write, admin)
            after = _offer_from_row(
                connection.execute(
                    _GET_ADMIN_OFFER, {"offer_id": offer_id}
                ).mappings().one()
            )
            _record_change(
                connection,
                admin=admin,
                entity_type="offer",
                entity_id=offer_id,
                action="updated",
                before=before,
                after=after,
            )
        return after

    def set_offer_lifecycle(
        self,
        offer_id: str,
        lifecycle: str,
        revision: int,
        admin: AdminUser,
    ) -> AdminOffer:
        if lifecycle not in {"draft", "published", "archived"}:
            raise CatalogValidationError("invalid_offer_lifecycle")
        with self._engine.begin() as connection:
            before_row = connection.execute(
                _GET_ADMIN_OFFER, {"offer_id": offer_id}
            ).mappings().first()
            if before_row is None:
                raise CatalogNotFoundError("offer_not_found")
            before = _offer_from_row(before_row)
            if before.revision != revision:
                raise CatalogConflictError("offer_was_modified")
            if lifecycle == "published":
                if not before.needs:
                    raise CatalogValidationError("offer_requires_category")
                if before.expires_at <= datetime.now(UTC):
                    raise CatalogValidationError("offer_verification_expired")
            result = connection.execute(
                text(
                    """
                    UPDATE offers SET
                        published = :published,
                        archived_at = CASE WHEN :archived THEN now() ELSE NULL END,
                        revision = revision + 1, updated_at = now()
                    WHERE id = CAST(:offer_id AS uuid) AND revision = :revision
                    RETURNING id
                    """
                ),
                {
                    "offer_id": offer_id,
                    "revision": revision,
                    "published": lifecycle == "published",
                    "archived": lifecycle == "archived",
                },
            ).scalar_one_or_none()
            if result is None:
                raise CatalogConflictError("offer_was_modified")
            after = _offer_from_row(
                connection.execute(
                    _GET_ADMIN_OFFER, {"offer_id": offer_id}
                ).mappings().one()
            )
            _record_change(
                connection,
                admin=admin,
                entity_type="offer",
                entity_id=offer_id,
                action=f"lifecycle_{lifecycle}",
                before=before,
                after=after,
            )
        return after

    def get_import_settings(self) -> ImportSettings:
        with self._engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT s.automatic_enabled, s.revision, s.updated_at,
                           u.username AS updated_by
                    FROM offer_import_settings s
                    LEFT JOIN admin_users u ON u.id = s.updated_by
                    WHERE s.id = 1
                    """
                )
            ).mappings().one()
        return ImportSettings(
            automatic_enabled=bool(row["automatic_enabled"]),
            revision=int(row["revision"]),
            updated_at=row["updated_at"],
            updated_by=str(row["updated_by"]) if row["updated_by"] else None,
        )

    def update_import_settings(
        self, enabled: bool, revision: int, admin: AdminUser
    ) -> ImportSettings:
        before = self.get_import_settings()
        with self._engine.begin() as connection:
            row = connection.execute(
                text(
                    """
                    UPDATE offer_import_settings SET
                        automatic_enabled = :enabled,
                        revision = revision + 1,
                        updated_at = now(), updated_by = CAST(:admin_id AS uuid)
                    WHERE id = 1 AND revision = :revision
                    RETURNING automatic_enabled, revision, updated_at
                    """
                ),
                {
                    "enabled": enabled,
                    "revision": revision,
                    "admin_id": admin.id,
                },
            ).mappings().first()
            if row is None:
                raise CatalogConflictError("import_settings_were_modified")
            after = ImportSettings(
                automatic_enabled=bool(row["automatic_enabled"]),
                revision=int(row["revision"]),
                updated_at=row["updated_at"],
                updated_by=admin.username,
            )
            _record_change(
                connection,
                admin=admin,
                entity_type="import_settings",
                entity_id="automatic",
                action="enabled" if enabled else "disabled",
                before=before,
                after=after,
            )
        return after

    def list_changes(
        self, *, entity_type: str, entity_id: str, limit: int = 50
    ) -> tuple[AdminChange, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT id::text AS id, admin_username, entity_type, entity_id,
                           action, before_data, after_data, created_at
                    FROM admin_change_log
                    WHERE entity_type = :entity_type AND entity_id = :entity_id
                    ORDER BY created_at DESC, id DESC LIMIT :limit
                    """
                ),
                {"entity_type": entity_type, "entity_id": entity_id, "limit": limit},
            ).mappings().all()
        return tuple(
            AdminChange(
                id=row["id"],
                admin_username=row["admin_username"],
                entity_type=row["entity_type"],
                entity_id=row["entity_id"],
                action=row["action"],
                before_data=dict(row["before_data"]) if row["before_data"] else None,
                after_data=dict(row["after_data"]) if row["after_data"] else None,
                created_at=row["created_at"],
            )
            for row in rows
        )

    def healthcheck(self) -> None:
        with self._engine.connect() as connection:
            connection.execute(text("SELECT 1"))

    def close(self) -> None:
        self._engine.dispose()


class InMemoryAdminCatalogRepository:
    """Small development/test implementation; production always uses PostgreSQL."""

    def __init__(self, state: AdminCatalogState | None = None) -> None:
        self.state = state or AdminCatalogState()
        self._refresh_offer_counts()
        self._import_settings = ImportSettings(
            automatic_enabled=True,
            revision=1,
            updated_at=datetime.now(UTC),
            updated_by=None,
        )

    def _refresh_offer_counts(self) -> None:
        for key, category in self.state.categories.items():
            self.state.categories[key] = replace(
                category,
                offer_count=sum(
                    key in offer.needs for offer in self.state.offers.values()
                ),
            )

    def _record_memory_change(
        self,
        *,
        admin: AdminUser,
        entity_type: str,
        entity_id: str,
        action: str,
        before: object | None,
        after: object | None,
    ) -> None:
        before_data = _jsonable(before) if before is not None else None
        after_data = _jsonable(after) if after is not None else None
        assert before_data is None or isinstance(before_data, dict)
        assert after_data is None or isinstance(after_data, dict)
        self.state.changes.insert(
            0,
            AdminChange(
                id=str(uuid4()),
                admin_username=admin.username,
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                before_data=before_data,
                after_data=after_data,
                created_at=datetime.now(UTC),
            ),
        )

    def list_categories(self) -> tuple[AdminCategory, ...]:
        return tuple(sorted(self.state.categories.values(), key=lambda item: item.sort_order))

    def create_category(self, write: CategoryWrite, admin: AdminUser) -> AdminCategory:
        key = _slugify(write.localizations["de"]["title"])
        if key in self.state.categories:
            raise CatalogConflictError("category_already_exists")
        category = AdminCategory(
            key=key,
            icon=write.icon,
            status=write.status,
            sort_order=write.sort_order,
            revision=1,
            localizations=write.localizations,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.state.categories[key] = category
        self._record_memory_change(
            admin=admin,
            entity_type="category",
            entity_id=key,
            action="created",
            before=None,
            after=category,
        )
        return category

    def update_category(
        self, key: str, write: CategoryWrite, admin: AdminUser
    ) -> AdminCategory:
        before = self.state.categories.get(key)
        if before is None:
            raise CatalogNotFoundError("category_not_found")
        if write.revision != before.revision:
            raise CatalogConflictError("category_was_modified")
        if write.status == "archived" and before.offer_count:
            raise CatalogValidationError("category_still_has_offers")
        category = AdminCategory(
            key=key,
            icon=write.icon,
            status=write.status,
            sort_order=write.sort_order,
            revision=before.revision + 1,
            localizations=write.localizations,
            offer_count=before.offer_count,
            created_at=before.created_at,
            updated_at=datetime.now(UTC),
        )
        self.state.categories[key] = category
        self._record_memory_change(
            admin=admin,
            entity_type="category",
            entity_id=key,
            action="updated",
            before=before,
            after=category,
        )
        return category

    def list_offers(self) -> tuple[AdminOffer, ...]:
        return tuple(self.state.offers.values())

    def get_offer(self, offer_id: str) -> AdminOffer | None:
        return self.state.offers.get(offer_id)

    def create_offer(self, write: OfferWrite, admin: AdminUser) -> AdminOffer:
        unknown = set(write.needs) - {
            item.key for item in self.state.categories.values() if item.status == "published"
        }
        if unknown:
            raise CatalogValidationError("unknown_or_inactive_category")
        now = datetime.now(UTC)
        offer_id = str(uuid4())
        offer = AdminOffer(
            id=offer_id,
            slug=_slugify(write.slug or write.name),
            name=write.name,
            organization_name=write.organization_name,
            summary=write.summary,
            needs=write.needs,
            languages=write.languages,
            access_rules=write.access_rules,
            availability=write.availability,
            contact_note=write.contact_note,
            address=write.address,
            latitude=write.latitude,
            longitude=write.longitude,
            source_label=write.source_label,
            source_url=write.source_url,
            verified_by=admin.username,
            verified_at=now,
            expires_at=write.expires_at,
            origin="manual",
            management_mode="manual",
            lifecycle="draft",
            revision=1,
            is_demo=False,
            updated_at=now,
        )
        self.state.offers[offer_id] = offer
        self._refresh_offer_counts()
        self._record_memory_change(
            admin=admin,
            entity_type="offer",
            entity_id=offer_id,
            action="created_as_draft",
            before=None,
            after=offer,
        )
        return offer

    def update_offer(
        self, offer_id: str, write: OfferWrite, admin: AdminUser
    ) -> AdminOffer:
        before = self.state.offers.get(offer_id)
        if before is None:
            raise CatalogNotFoundError("offer_not_found")
        if write.revision != before.revision:
            raise CatalogConflictError("offer_was_modified")
        unknown = set(write.needs) - {
            item.key for item in self.state.categories.values() if item.status == "published"
        }
        if unknown:
            raise CatalogValidationError("unknown_or_inactive_category")
        updated = replace(
            before,
            name=write.name,
            organization_name=write.organization_name,
            summary=write.summary,
            needs=write.needs,
            languages=write.languages,
            access_rules=write.access_rules,
            availability=write.availability,
            contact_note=write.contact_note,
            address=write.address,
            latitude=write.latitude,
            longitude=write.longitude,
            source_label=write.source_label,
            source_url=write.source_url,
            verified_by=admin.username,
            verified_at=datetime.now(UTC),
            expires_at=write.expires_at,
            management_mode=write.management_mode,
            revision=before.revision + 1,
            updated_at=datetime.now(UTC),
        )
        self.state.offers[offer_id] = updated
        self._refresh_offer_counts()
        self._record_memory_change(
            admin=admin,
            entity_type="offer",
            entity_id=offer_id,
            action="updated",
            before=before,
            after=updated,
        )
        return updated

    def set_offer_lifecycle(
        self, offer_id: str, lifecycle: str, revision: int, admin: AdminUser
    ) -> AdminOffer:
        if lifecycle not in {"draft", "published", "archived"}:
            raise CatalogValidationError("invalid_offer_lifecycle")
        before = self.state.offers.get(offer_id)
        if before is None:
            raise CatalogNotFoundError("offer_not_found")
        if revision != before.revision:
            raise CatalogConflictError("offer_was_modified")
        if lifecycle == "published" and before.expires_at <= datetime.now(UTC):
            raise CatalogValidationError("offer_verification_expired")
        updated = replace(
            before,
            lifecycle=lifecycle,
            revision=revision + 1,
            updated_at=datetime.now(UTC),
        )
        self.state.offers[offer_id] = updated
        self._record_memory_change(
            admin=admin,
            entity_type="offer",
            entity_id=offer_id,
            action=f"lifecycle_{lifecycle}",
            before=before,
            after=updated,
        )
        return updated

    def get_import_settings(self) -> ImportSettings:
        return self._import_settings

    def update_import_settings(
        self, enabled: bool, revision: int, admin: AdminUser
    ) -> ImportSettings:
        if revision != self._import_settings.revision:
            raise CatalogConflictError("import_settings_were_modified")
        before = self._import_settings
        self._import_settings = ImportSettings(
            automatic_enabled=enabled,
            revision=revision + 1,
            updated_at=datetime.now(UTC),
            updated_by=admin.username,
        )
        self._record_memory_change(
            admin=admin,
            entity_type="import_settings",
            entity_id="automatic",
            action="enabled" if enabled else "disabled",
            before=before,
            after=self._import_settings,
        )
        return self._import_settings

    def list_changes(
        self, *, entity_type: str, entity_id: str, limit: int = 50
    ) -> tuple[AdminChange, ...]:
        return tuple(
            item
            for item in self.state.changes
            if item.entity_type == entity_type and item.entity_id == entity_id
        )[:limit]

    def healthcheck(self) -> None:
        return None

    def close(self) -> None:
        return None
