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
    SUPPORTED_CATEGORY_LOCALES,
    AdminCatalogState,
    AdminCategory,
    AdminChange,
    AdminOffer,
    AdminServiceDefinition,
    CategoryWrite,
    ImportSettings,
    OfferLocalization,
    OfferLocalizationWrite,
    OfferWrite,
    ServiceDefinitionWrite,
)
from vesta_api.domain.admin_models import AdminUser
from vesta_api.repositories.database import create_database_engine


class CatalogNotFoundError(LookupError):
    pass


class CatalogConflictError(RuntimeError):
    pass


class CatalogValidationError(ValueError):
    pass


def _services_cover_public_needs(
    needs: tuple[str, ...],
    services: tuple[str, ...],
    service_groups: Mapping[str, str],
) -> bool:
    selected_groups = {
        service_groups[key] for key in services if key in service_groups
    }
    if "basic_needs" in needs and "basic_needs" not in selected_groups:
        return False
    if "counselling" in needs and "counselling" not in selected_groups:
        return False
    if "daytime_stay" in needs and "daytime_no_purchase" not in services:
        return False
    return True


class AdminCatalogRepository(Protocol):
    def list_categories(self) -> tuple[AdminCategory, ...]: ...

    def create_category(self, write: CategoryWrite, admin: AdminUser) -> AdminCategory: ...

    def update_category(
        self, key: str, write: CategoryWrite, admin: AdminUser
    ) -> AdminCategory: ...

    def list_services(self) -> tuple[AdminServiceDefinition, ...]: ...

    def create_service(
        self, write: ServiceDefinitionWrite, admin: AdminUser
    ) -> AdminServiceDefinition: ...

    def update_service(
        self, key: str, write: ServiceDefinitionWrite, admin: AdminUser
    ) -> AdminServiceDefinition: ...

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

    def put_offer_localization(
        self,
        offer_id: str,
        locale: str,
        write: OfferLocalizationWrite,
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


def _service_from_row(row: Mapping[str, Any]) -> AdminServiceDefinition:
    return AdminServiceDefinition(
        key=str(row["key"]),
        service_group=row["service_group"],
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
    localizations = {
        locale: OfferLocalization(
            locale=locale,
            name=str(values["name"]),
            summary=str(values["summary"]),
            contact_note=str(values["contact_note"]),
            status=values["status"],
            revision=int(values["revision"]),
            reviewed_by=(str(values["reviewed_by"]) if values.get("reviewed_by") else None),
            reviewed_at=values.get("reviewed_at"),
            updated_at=values.get("updated_at"),
        )
        for locale, values in (row.get("localizations") or {}).items()
    }
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
        localizations=localizations,
        services=tuple(row.get("services") or ()),
        provider_approval_status=row.get("provider_approval_status") or "pending",
        provider_approval_reference=row.get("provider_approval_reference"),
        provider_approval_scope=row.get("provider_approval_scope"),
        provider_approval_evidence=row.get("provider_approval_evidence"),
        provider_approval_deadline=row.get("provider_approval_deadline"),
        source_draft=(
            dict(row["source_draft"]) if row.get("source_draft") else None
        ),
        source_draft_created_at=row.get("source_draft_created_at"),
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

_LIST_SERVICES = text(
    """
    SELECT s.key, s.service_group, s.icon, s.status, s.sort_order, s.revision,
           s.created_at, s.updated_at,
           COALESCE(jsonb_object_agg(
               sl.locale, jsonb_build_object(
                   'label', sl.label, 'description', sl.description
               )
           ) FILTER (WHERE sl.locale IS NOT NULL), '{}'::jsonb) AS localizations,
           COUNT(DISTINCT os.offer_id) FILTER (WHERE os.status = 'confirmed')
               AS offer_count
    FROM service_definitions s
    LEFT JOIN service_localizations sl ON sl.service_key = s.key
    LEFT JOIN offer_services os ON os.service_key = s.key
    GROUP BY s.key
    ORDER BY s.service_group, s.sort_order, s.key
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
           COALESCE(s.services, ARRAY[]::text[]) AS services,
           COALESCE(l.localizations, '{}'::jsonb) AS localizations,
           v.source_label, v.source_url, v.verified_by,
           COALESCE(v.verified_at, o.created_at) AS verified_at,
           COALESCE(v.expires_at, o.created_at) AS expires_at,
           COALESCE(pa.status, 'pending') AS provider_approval_status,
           pa.contact_reference AS provider_approval_reference,
           pa.scope_note AS provider_approval_scope,
           pa.decision_evidence AS provider_approval_evidence,
           pa.legacy_deadline AS provider_approval_deadline,
           sr.extracted_data AS source_draft,
           sr.created_at AS source_draft_created_at
    FROM offers o
    JOIN organizations org ON org.id = o.organization_id
    LEFT JOIN LATERAL (
        SELECT array_agg(category ORDER BY category) AS needs
        FROM offer_categories WHERE offer_id = o.id
    ) c ON TRUE
    LEFT JOIN LATERAL (
        SELECT array_agg(service_key ORDER BY service_key) AS services
        FROM offer_services
        WHERE offer_id = o.id
    ) s ON TRUE
    LEFT JOIN LATERAL (
        SELECT jsonb_object_agg(
            ol.locale, jsonb_build_object(
                'name', ol.name,
                'summary', ol.summary,
                'contact_note', ol.contact_note,
                'status', ol.status,
                'revision', ol.revision,
                'reviewed_by', reviewer.username,
                'reviewed_at', ol.reviewed_at,
                'updated_at', ol.updated_at
            )
        ) AS localizations
        FROM offer_localizations ol
        LEFT JOIN admin_users reviewer ON reviewer.id = ol.reviewed_by
        WHERE ol.offer_id = o.id
    ) l ON TRUE
    LEFT JOIN LATERAL (
        SELECT source_label, source_url, verified_by, verified_at, expires_at
        FROM offer_verifications WHERE offer_id = o.id
        ORDER BY verified_at DESC, created_at DESC LIMIT 1
    ) v ON TRUE
    LEFT JOIN provider_approvals pa ON pa.offer_id = o.id
    LEFT JOIN LATERAL (
        SELECT extracted_data, created_at
        FROM offer_source_revisions
        WHERE offer_id = o.id AND status = 'pending_review'
        ORDER BY created_at DESC LIMIT 1
    ) sr ON TRUE
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
        if write.status != "draft":
            raise CatalogValidationError("new_category_must_start_as_draft")
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
            if write.status == "published" and before.status != "published":
                eligible_offer = connection.execute(
                    text(
                        """
                        SELECT 1
                        FROM offer_categories oc
                        JOIN offers o ON o.id = oc.offer_id
                        JOIN offer_verifications v ON v.offer_id = o.id
                        JOIN offer_localizations l
                          ON l.offer_id = o.id
                         AND l.locale = 'de'
                         AND l.status = 'reviewed'
                        WHERE oc.category = :key
                          AND o.archived_at IS NULL
                          AND v.expires_at > now()
                        LIMIT 1
                        """
                    ),
                    {"key": key},
                ).scalar_one_or_none()
                if eligible_offer is None:
                    raise CatalogValidationError(
                        "category_requires_reviewed_offer_before_publish"
                    )
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

    def list_services(self) -> tuple[AdminServiceDefinition, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(_LIST_SERVICES).mappings().all()
        return tuple(_service_from_row(row) for row in rows)

    @staticmethod
    def _replace_service_localizations(
        connection: Connection,
        key: str,
        localizations: dict[str, dict[str, str]],
    ) -> None:
        connection.execute(
            text("DELETE FROM service_localizations WHERE service_key = :key"),
            {"key": key},
        )
        connection.execute(
            text(
                """
                INSERT INTO service_localizations (
                    service_key, locale, label, description
                ) VALUES (:key, :locale, :label, :description)
                """
            ),
            [
                {
                    "key": key,
                    "locale": locale,
                    "label": values["label"],
                    "description": values.get("description", ""),
                }
                for locale, values in localizations.items()
            ],
        )

    @staticmethod
    def _sync_service_question_option(
        connection: Connection,
        key: str,
        write: ServiceDefinitionWrite,
    ) -> None:
        attribute_keys = {
            "basic_needs": "request.services.basic",
            "counselling": "request.services.counselling",
            "addiction": "request.services.addiction",
        }
        connection.execute(
            text(
                """
                DELETE FROM attribute_options
                WHERE value = :key
                  AND attribute_id IN (
                      SELECT id FROM attribute_definitions
                      WHERE key LIKE 'request.services.%'
                  )
                """
            ),
            {"key": key},
        )
        if write.status != "published" or key == "daytime_no_purchase":
            return
        option_id = uuid4()
        connection.execute(
            text(
                """
                INSERT INTO attribute_options (
                    id, attribute_id, value, sort_order, icon
                )
                SELECT :id, id, :value, :sort_order, :icon
                FROM attribute_definitions WHERE key = :attribute_key
                """
            ),
            {
                "id": option_id,
                "value": key,
                "sort_order": write.sort_order,
                "icon": write.icon,
                "attribute_key": attribute_keys[write.service_group],
            },
        )
        connection.execute(
            text(
                """
                INSERT INTO attribute_option_localizations (
                    option_id, locale, label, explanation
                ) VALUES (:option_id, :locale, :label, :explanation)
                """
            ),
            [
                {
                    "option_id": option_id,
                    "locale": locale,
                    "label": values["label"],
                    "explanation": values.get("description", ""),
                }
                for locale, values in write.localizations.items()
            ],
        )

    def create_service(
        self, write: ServiceDefinitionWrite, admin: AdminUser
    ) -> AdminServiceDefinition:
        if write.status != "draft":
            raise CatalogValidationError("new_service_must_start_as_draft")
        with self._engine.begin() as connection:
            base = _slugify(write.localizations["de"]["label"])
            key = base
            suffix = 2
            while connection.execute(
                text("SELECT 1 FROM service_definitions WHERE key = :key"),
                {"key": key},
            ).scalar_one_or_none():
                key = f"{base}-{suffix}"
                suffix += 1
            connection.execute(
                text(
                    """
                    INSERT INTO service_definitions (
                        key, service_group, icon, status, sort_order
                    ) VALUES (:key, :service_group, :icon, :status, :sort_order)
                    """
                ),
                {
                    "key": key,
                    "service_group": write.service_group,
                    "icon": write.icon,
                    "status": write.status,
                    "sort_order": write.sort_order,
                },
            )
            self._replace_service_localizations(connection, key, write.localizations)
            self._sync_service_question_option(connection, key, write)
            created = next(
                _service_from_row(row)
                for row in connection.execute(_LIST_SERVICES).mappings()
                if row["key"] == key
            )
            _record_change(
                connection,
                admin=admin,
                entity_type="service_definition",
                entity_id=key,
                action="created",
                before=None,
                after=created,
            )
        return created

    def update_service(
        self, key: str, write: ServiceDefinitionWrite, admin: AdminUser
    ) -> AdminServiceDefinition:
        assert write.revision is not None
        with self._engine.begin() as connection:
            row = next(
                (
                    item
                    for item in connection.execute(_LIST_SERVICES).mappings()
                    if item["key"] == key
                ),
                None,
            )
            if row is None:
                raise CatalogNotFoundError("service_not_found")
            before = _service_from_row(row)
            if before.revision != write.revision:
                raise CatalogConflictError("service_was_modified")
            if write.status == "archived" and before.offer_count:
                raise CatalogValidationError("service_still_has_offers")
            if write.status == "published":
                published_count = connection.execute(
                    text(
                        """
                        SELECT count(*) FROM service_definitions
                        WHERE service_group = :service_group
                          AND status = 'published' AND key <> :key
                          AND key <> 'daytime_no_purchase'
                        """
                    ),
                    {"service_group": write.service_group, "key": key},
                ).scalar_one()
                if published_count >= 7:
                    raise CatalogValidationError("service_group_limit_reached")
            result = connection.execute(
                text(
                    """
                    UPDATE service_definitions
                    SET service_group = :service_group, icon = :icon,
                        status = :status, sort_order = :sort_order,
                        revision = revision + 1, updated_at = now()
                    WHERE key = :key AND revision = :revision
                    RETURNING key
                    """
                ),
                {
                    "key": key,
                    "service_group": write.service_group,
                    "icon": write.icon,
                    "status": write.status,
                    "sort_order": write.sort_order,
                    "revision": write.revision,
                },
            ).scalar_one_or_none()
            if result is None:
                raise CatalogConflictError("service_was_modified")
            self._replace_service_localizations(connection, key, write.localizations)
            self._sync_service_question_option(connection, key, write)
            after = next(
                _service_from_row(item)
                for item in connection.execute(_LIST_SERVICES).mappings()
                if item["key"] == key
            )
            _record_change(
                connection,
                admin=admin,
                entity_type="service_definition",
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
    def _upsert_german_localization(
        connection: Connection, offer_id: object, write: OfferWrite, admin: AdminUser
    ) -> None:
        connection.execute(
            text(
                """
                INSERT INTO offer_localizations (
                    offer_id, locale, name, summary, contact_note, status,
                    revision, reviewed_by, reviewed_at, updated_at
                ) VALUES (
                    :offer_id, 'de', :name, :summary, :contact_note, 'reviewed',
                    1, CAST(:admin_id AS uuid), now(), now()
                )
                ON CONFLICT (offer_id, locale) DO UPDATE SET
                    name = EXCLUDED.name, summary = EXCLUDED.summary,
                    contact_note = EXCLUDED.contact_note, status = 'reviewed',
                    revision = offer_localizations.revision + 1,
                    reviewed_by = EXCLUDED.reviewed_by, reviewed_at = now(),
                    updated_at = now()
                """
            ),
            {
                "offer_id": offer_id,
                "name": write.name,
                "summary": write.summary,
                "contact_note": write.contact_note,
                "admin_id": admin.id,
            },
        )

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
                WHERE key = ANY(:keys) AND status <> 'archived'
                """
            ),
            {"keys": list(categories)},
        ).scalars().all()
        if set(rows) != set(categories):
            raise CatalogValidationError("unknown_or_inactive_category")

    @staticmethod
    def _ensure_services(connection: Connection, services: tuple[str, ...]) -> None:
        if not services:
            return
        rows = connection.execute(
            text(
                """
                SELECT key FROM service_definitions
                WHERE key = ANY(:keys) AND status <> 'archived'
                """
            ),
            {"keys": list(services)},
        ).scalars().all()
        if set(rows) != set(services):
            raise CatalogValidationError("unknown_or_inactive_service")

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
    def _write_services(
        connection: Connection,
        offer_id: object,
        services: tuple[str, ...],
        write: OfferWrite,
    ) -> None:
        connection.execute(
            text("DELETE FROM offer_services WHERE offer_id = :offer_id"),
            {"offer_id": offer_id},
        )
        if not services:
            return
        connection.execute(
            text(
                """
                INSERT INTO offer_services (
                    offer_id, service_key, status, evidence_url,
                    evidence_note, verified_at
                ) VALUES (
                    :offer_id, :service_key, 'confirmed', :evidence_url,
                    :evidence_note, now()
                )
                """
            ),
            [
                {
                    "offer_id": offer_id,
                    "service_key": service,
                    "evidence_url": write.source_url,
                    "evidence_note": f"Im Adminbereich bestätigte Leistung: {service}",
                }
                for service in services
            ],
        )

    @staticmethod
    def _write_provider_approval(
        connection: Connection,
        offer_id: object,
        write: OfferWrite,
        admin: AdminUser,
    ) -> None:
        approved = write.provider_approval_status == "approved"
        connection.execute(
            text(
                """
                INSERT INTO provider_approvals (
                    offer_id, status, contact_reference, scope_note,
                    approved_at, approved_by, decision_evidence,
                    legacy_deadline, revision, updated_at
                ) VALUES (
                    :offer_id, :status, :contact_reference, :scope_note,
                    CASE WHEN :approved THEN now() ELSE NULL END,
                    CASE WHEN :approved THEN CAST(:admin_id AS uuid) ELSE NULL END,
                    :decision_evidence,
                    CASE WHEN :status = 'legacy_pending'
                         THEN now() + interval '90 days' ELSE NULL END,
                    1, now()
                )
                ON CONFLICT (offer_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    contact_reference = EXCLUDED.contact_reference,
                    scope_note = EXCLUDED.scope_note,
                    approved_at = EXCLUDED.approved_at,
                    approved_by = EXCLUDED.approved_by,
                    decision_evidence = EXCLUDED.decision_evidence,
                    legacy_deadline = CASE
                        WHEN EXCLUDED.status = 'legacy_pending'
                        THEN COALESCE(provider_approvals.legacy_deadline,
                                      EXCLUDED.legacy_deadline)
                        ELSE NULL
                    END,
                    revision = provider_approvals.revision + 1,
                    updated_at = now()
                """
            ),
            {
                "offer_id": offer_id,
                "status": write.provider_approval_status,
                "contact_reference": write.provider_approval_reference,
                "scope_note": write.provider_approval_scope,
                "decision_evidence": write.provider_approval_evidence,
                "approved": approved,
                "admin_id": admin.id,
            },
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
            self._ensure_services(connection, write.services)
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
            self._write_services(connection, offer_id, write.services, write)
            self._write_provider_approval(connection, offer_id, write, admin)
            self._write_verification(connection, offer_id, write, admin)
            self._upsert_german_localization(connection, offer_id, write, admin)
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
            self._ensure_services(connection, write.services)
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
            self._write_services(connection, result, write.services, write)
            self._write_provider_approval(connection, result, write, admin)
            self._write_verification(connection, result, write, admin)
            self._upsert_german_localization(connection, result, write, admin)
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
                german = before.localizations.get("de")
                if german is None or german.status != "reviewed":
                    raise CatalogValidationError("reviewed_german_localization_required")
                published_categories = set(
                    connection.execute(
                        text(
                            "SELECT key FROM need_definitions "
                            "WHERE key = ANY(:keys) AND status = 'published'"
                        ),
                        {"keys": list(before.needs)},
                    ).scalars()
                )
                if published_categories != set(before.needs):
                    raise CatalogValidationError("offer_requires_published_categories")
                service_groups = {
                    str(row["key"]): str(row["service_group"])
                    for row in connection.execute(
                        text(
                            "SELECT key, service_group FROM service_definitions "
                            "WHERE key = ANY(:keys) AND status = 'published'"
                        ),
                        {"keys": list(before.services)},
                    ).mappings()
                }
                if not _services_cover_public_needs(
                    before.needs, before.services, service_groups
                ):
                    raise CatalogValidationError("offer_requires_confirmed_services")
                approval_valid = before.provider_approval_status == "approved" or (
                    before.provider_approval_status == "legacy_pending"
                    and before.provider_approval_deadline is not None
                    and before.provider_approval_deadline > datetime.now(UTC)
                )
                if not approval_valid:
                    raise CatalogValidationError("provider_approval_required")
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

    def put_offer_localization(
        self,
        offer_id: str,
        locale: str,
        write: OfferLocalizationWrite,
        admin: AdminUser,
    ) -> AdminOffer:
        if locale not in SUPPORTED_CATEGORY_LOCALES:
            raise CatalogValidationError("unsupported_offer_locale")
        with self._engine.begin() as connection:
            before_row = connection.execute(
                _GET_ADMIN_OFFER, {"offer_id": offer_id}
            ).mappings().first()
            if before_row is None:
                raise CatalogNotFoundError("offer_not_found")
            before = _offer_from_row(before_row)
            existing = before.localizations.get(locale)
            if existing is not None and write.revision != existing.revision:
                raise CatalogConflictError("offer_localization_was_modified")
            if existing is None and write.revision is not None:
                raise CatalogConflictError("offer_localization_was_modified")
            connection.execute(
                text(
                    """
                    INSERT INTO offer_localizations (
                        offer_id, locale, name, summary, contact_note, status,
                        revision, reviewed_by, reviewed_at, updated_at
                    ) VALUES (
                        CAST(:offer_id AS uuid), :locale, :name, :summary,
                        :contact_note, :status, 1,
                        CASE WHEN :reviewed THEN CAST(:admin_id AS uuid) ELSE NULL END,
                        CASE WHEN :reviewed THEN now() ELSE NULL END, now()
                    )
                    ON CONFLICT (offer_id, locale) DO UPDATE SET
                        name = EXCLUDED.name, summary = EXCLUDED.summary,
                        contact_note = EXCLUDED.contact_note, status = EXCLUDED.status,
                        revision = offer_localizations.revision + 1,
                        reviewed_by = EXCLUDED.reviewed_by,
                        reviewed_at = EXCLUDED.reviewed_at, updated_at = now()
                    """
                ),
                {
                    "offer_id": offer_id,
                    "locale": locale,
                    "name": write.name,
                    "summary": write.summary,
                    "contact_note": write.contact_note,
                    "status": write.status,
                    "reviewed": write.status == "reviewed",
                    "admin_id": admin.id,
                },
            )
            if locale == "de":
                connection.execute(
                    text(
                        """
                        UPDATE offers SET name = :name, summary = :summary,
                            contact = jsonb_set(contact, '{note}', to_jsonb(CAST(:note AS text))),
                            revision = revision + 1, updated_at = now()
                        WHERE id = CAST(:offer_id AS uuid)
                        """
                    ),
                    {
                        "offer_id": offer_id,
                        "name": write.name,
                        "summary": write.summary,
                        "note": write.contact_note,
                    },
                )
            after = _offer_from_row(
                connection.execute(
                    _GET_ADMIN_OFFER, {"offer_id": offer_id}
                ).mappings().one()
            )
            _record_change(
                connection,
                admin=admin,
                entity_type="offer_localization",
                entity_id=f"{offer_id}:{locale}",
                action="reviewed" if write.status == "reviewed" else "machine_draft_saved",
                before=existing,
                after=after.localizations[locale],
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
        for key, service in self.state.services.items():
            self.state.services[key] = replace(
                service,
                offer_count=sum(
                    key in offer.services for offer in self.state.offers.values()
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
        if write.status != "draft":
            raise CatalogValidationError("new_category_must_start_as_draft")
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
        if write.status == "published" and before.status != "published":
            eligible_offer = any(
                key in offer.needs
                and offer.lifecycle != "archived"
                and offer.expires_at > datetime.now(UTC)
                and offer.localizations.get("de") is not None
                and offer.localizations["de"].status == "reviewed"
                for offer in self.state.offers.values()
            )
            if not eligible_offer:
                raise CatalogValidationError(
                    "category_requires_reviewed_offer_before_publish"
                )
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

    def list_services(self) -> tuple[AdminServiceDefinition, ...]:
        return tuple(
            sorted(
                self.state.services.values(),
                key=lambda item: (item.service_group, item.sort_order),
            )
        )

    def create_service(
        self, write: ServiceDefinitionWrite, admin: AdminUser
    ) -> AdminServiceDefinition:
        if write.status != "draft":
            raise CatalogValidationError("new_service_must_start_as_draft")
        key = _slugify(write.localizations["de"]["label"])
        if key in self.state.services:
            raise CatalogConflictError("service_already_exists")
        service = AdminServiceDefinition(
            key=key,
            service_group=write.service_group,
            icon=write.icon,
            status=write.status,
            sort_order=write.sort_order,
            revision=1,
            localizations=write.localizations,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.state.services[key] = service
        self._record_memory_change(
            admin=admin,
            entity_type="service_definition",
            entity_id=key,
            action="created",
            before=None,
            after=service,
        )
        return service

    def update_service(
        self, key: str, write: ServiceDefinitionWrite, admin: AdminUser
    ) -> AdminServiceDefinition:
        before = self.state.services.get(key)
        if before is None:
            raise CatalogNotFoundError("service_not_found")
        if write.revision != before.revision:
            raise CatalogConflictError("service_was_modified")
        if write.status == "archived" and before.offer_count:
            raise CatalogValidationError("service_still_has_offers")
        if write.status == "published":
            published_count = sum(
                item.key != key
                and item.key != "daytime_no_purchase"
                and item.service_group == write.service_group
                and item.status == "published"
                for item in self.state.services.values()
            )
            if published_count >= 7:
                raise CatalogValidationError("service_group_limit_reached")
        service = replace(
            before,
            service_group=write.service_group,
            icon=write.icon,
            status=write.status,
            sort_order=write.sort_order,
            revision=before.revision + 1,
            localizations=write.localizations,
            updated_at=datetime.now(UTC),
        )
        self.state.services[key] = service
        self._record_memory_change(
            admin=admin,
            entity_type="service_definition",
            entity_id=key,
            action="updated",
            before=before,
            after=service,
        )
        return service

    def list_offers(self) -> tuple[AdminOffer, ...]:
        return tuple(self.state.offers.values())

    def get_offer(self, offer_id: str) -> AdminOffer | None:
        return self.state.offers.get(offer_id)

    def create_offer(self, write: OfferWrite, admin: AdminUser) -> AdminOffer:
        unknown = set(write.needs) - {
            item.key for item in self.state.categories.values() if item.status != "archived"
        }
        if unknown:
            raise CatalogValidationError("unknown_or_inactive_category")
        unknown_services = set(write.services) - {
            item.key for item in self.state.services.values() if item.status != "archived"
        }
        if unknown_services:
            raise CatalogValidationError("unknown_or_inactive_service")
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
            localizations={
                "de": OfferLocalization(
                    locale="de",
                    name=write.name,
                    summary=write.summary,
                    contact_note=write.contact_note,
                    status="reviewed",
                    revision=1,
                    reviewed_by=admin.username,
                    reviewed_at=now,
                    updated_at=now,
                )
            },
            services=write.services,
            provider_approval_status=write.provider_approval_status,
            provider_approval_reference=write.provider_approval_reference,
            provider_approval_scope=write.provider_approval_scope,
            provider_approval_evidence=write.provider_approval_evidence,
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
            item.key for item in self.state.categories.values() if item.status != "archived"
        }
        if unknown:
            raise CatalogValidationError("unknown_or_inactive_category")
        unknown_services = set(write.services) - {
            item.key for item in self.state.services.values() if item.status != "archived"
        }
        if unknown_services:
            raise CatalogValidationError("unknown_or_inactive_service")
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
            services=write.services,
            provider_approval_status=write.provider_approval_status,
            provider_approval_reference=write.provider_approval_reference,
            provider_approval_scope=write.provider_approval_scope,
            provider_approval_evidence=write.provider_approval_evidence,
            localizations={
                **before.localizations,
                "de": OfferLocalization(
                    locale="de",
                    name=write.name,
                    summary=write.summary,
                    contact_note=write.contact_note,
                    status="reviewed",
                    revision=before.localizations.get(
                        "de",
                        OfferLocalization("de", "", "", "", "reviewed", 0),
                    ).revision
                    + 1,
                    reviewed_by=admin.username,
                    reviewed_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                ),
            },
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
        if lifecycle == "published":
            german = before.localizations.get("de")
            if german is None or german.status != "reviewed":
                raise CatalogValidationError("reviewed_german_localization_required")
            unpublished = {
                need
                for need in before.needs
                if self.state.categories.get(need) is None
                or self.state.categories[need].status != "published"
            }
            if unpublished:
                raise CatalogValidationError("offer_requires_published_categories")
            service_groups = {
                key: service.service_group
                for key, service in self.state.services.items()
                if service.status == "published"
            }
            if not _services_cover_public_needs(
                before.needs, before.services, service_groups
            ):
                raise CatalogValidationError("offer_requires_confirmed_services")
            approval_valid = before.provider_approval_status == "approved" or (
                before.provider_approval_status == "legacy_pending"
                and before.provider_approval_deadline is not None
                and before.provider_approval_deadline > datetime.now(UTC)
            )
            if not approval_valid:
                raise CatalogValidationError("provider_approval_required")
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

    def put_offer_localization(
        self,
        offer_id: str,
        locale: str,
        write: OfferLocalizationWrite,
        admin: AdminUser,
    ) -> AdminOffer:
        if locale not in SUPPORTED_CATEGORY_LOCALES:
            raise CatalogValidationError("unsupported_offer_locale")
        before = self.state.offers.get(offer_id)
        if before is None:
            raise CatalogNotFoundError("offer_not_found")
        existing = before.localizations.get(locale)
        if existing is not None and write.revision != existing.revision:
            raise CatalogConflictError("offer_localization_was_modified")
        if existing is None and write.revision is not None:
            raise CatalogConflictError("offer_localization_was_modified")
        now = datetime.now(UTC)
        localization = OfferLocalization(
            locale=locale,
            name=write.name,
            summary=write.summary,
            contact_note=write.contact_note,
            status=write.status,
            revision=(existing.revision + 1) if existing else 1,
            reviewed_by=admin.username if write.status == "reviewed" else None,
            reviewed_at=now if write.status == "reviewed" else None,
            updated_at=now,
        )
        changes: dict[str, object] = {
            "localizations": {**before.localizations, locale: localization},
            "revision": before.revision + (1 if locale == "de" else 0),
            "updated_at": now,
        }
        if locale == "de":
            changes.update(
                name=write.name,
                summary=write.summary,
                contact_note=write.contact_note,
            )
        after = replace(before, **changes)
        self.state.offers[offer_id] = after
        self._record_memory_change(
            admin=admin,
            entity_type="offer_localization",
            entity_id=f"{offer_id}:{locale}",
            action="reviewed" if write.status == "reviewed" else "machine_draft_saved",
            before=existing,
            after=localization,
        )
        return after

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
