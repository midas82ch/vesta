import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Protocol

from sqlalchemy import Engine, text

from vesta_api.domain.dialogue_catalog import (
    AttributeDefinition,
    AttributeOption,
    NeedDefinition,
    QuestionDefinition,
)
from vesta_api.repositories.admin_catalog import AdminCatalogRepository
from vesta_api.repositories.database import create_database_engine


class DialogueCatalogRepository(Protocol):
    def list_needs(self) -> tuple[NeedDefinition, ...]: ...

    def list_attributes(self) -> tuple[AttributeDefinition, ...]: ...

    def get_attribute(self, key: str) -> AttributeDefinition | None: ...

    def list_questions(self) -> tuple[QuestionDefinition, ...]: ...

    def healthcheck(self) -> None: ...

    def close(self) -> None: ...


def _options_from_payload(payload: list[dict[str, object]]) -> tuple[AttributeOption, ...]:
    return tuple(
        AttributeOption(
            value=str(item["value"]),
            sort_order=int(item["sort_order"]),  # type: ignore[arg-type]
            localizations=dict(item.get("localizations", {})),  # type: ignore[arg-type]
        )
        for item in payload
    )


class JsonDialogueCatalogRepository:
    def __init__(self, data_path: Path) -> None:
        self._data_path = data_path

    def _payload(self) -> dict[str, Any]:
        return json.loads(self._data_path.read_text(encoding="utf-8"))

    def list_needs(self) -> tuple[NeedDefinition, ...]:
        payload = self._payload()
        return tuple(
            NeedDefinition(
                key=str(item["key"]),
                sort_order=int(item["sort_order"]),
                localizations=dict(item["localizations"]),
                icon=str(item.get("icon", "other")),
            )
            for item in sorted(payload["needs"], key=lambda item: item["sort_order"])
        )

    def list_attributes(self) -> tuple[AttributeDefinition, ...]:
        payload = self._payload()
        return tuple(
            AttributeDefinition(
                key=str(item["key"]),
                value_type=item["value_type"],
                confirmation_required=bool(item["confirmation_required"]),
                skippable=bool(item["skippable"]),
                options=_options_from_payload(item.get("options", [])),
            )
            for item in payload["attributes"]
        )

    def get_attribute(self, key: str) -> AttributeDefinition | None:
        for attribute in self.list_attributes():
            if attribute.key == key:
                return attribute
        return None

    def list_questions(self) -> tuple[QuestionDefinition, ...]:
        payload = self._payload()
        return tuple(
            QuestionDefinition(
                key=str(item["key"]),
                attribute_key=str(item["attribute_key"]),
                answer_type=item["answer_type"],
                priority=int(item["priority"]),
                ai_rephrasing_allowed=bool(item["ai_rephrasing_allowed"]),
                localizations=dict(item["localizations"]),
            )
            for item in sorted(payload["questions"], key=lambda item: item["priority"])
        )

    def healthcheck(self) -> None:
        self._payload()

    def close(self) -> None:
        return None


class AdminManagedDialogueCatalogRepository:
    """Expose in-memory admin category changes through the public dev catalog."""

    def __init__(
        self,
        base: DialogueCatalogRepository,
        admin_catalog: AdminCatalogRepository,
    ) -> None:
        self._base = base
        self._admin_catalog = admin_catalog

    def list_needs(self) -> tuple[NeedDefinition, ...]:
        return tuple(
            NeedDefinition(
                key=category.key,
                sort_order=category.sort_order,
                localizations=category.localizations,
                icon=category.icon,
            )
            for category in self._admin_catalog.list_categories()
            if category.status == "published"
        )

    def list_attributes(self) -> tuple[AttributeDefinition, ...]:
        return self._base.list_attributes()

    def get_attribute(self, key: str) -> AttributeDefinition | None:
        return self._base.get_attribute(key)

    def list_questions(self) -> tuple[QuestionDefinition, ...]:
        return self._base.list_questions()

    def healthcheck(self) -> None:
        self._base.healthcheck()

    def close(self) -> None:
        self._base.close()


_LIST_NEEDS = text(
    """
    SELECT
        n.key,
        n.sort_order,
        n.icon,
        COALESCE(
            jsonb_object_agg(nl.locale, jsonb_build_object(
                'title', nl.title, 'description', nl.description
            )) FILTER (WHERE nl.locale IS NOT NULL),
            '{}'::jsonb
        ) AS localizations
    FROM need_definitions AS n
    LEFT JOIN need_localizations AS nl ON nl.need_id = n.id
    WHERE n.status = 'published'
    GROUP BY n.id, n.key, n.sort_order, n.icon
    ORDER BY n.sort_order
    """
)

_LIST_ATTRIBUTES = text(
    """
    SELECT
        a.key,
        a.value_type,
        a.confirmation_required,
        a.skippable,
        COALESCE(opts.options, '[]'::jsonb) AS options
    FROM attribute_definitions AS a
    LEFT JOIN LATERAL (
        SELECT jsonb_agg(
            jsonb_build_object(
                'value', o.value,
                'sort_order', o.sort_order,
                'localizations', COALESCE(ol.localizations, '{}'::jsonb)
            )
            ORDER BY o.sort_order
        ) AS options
        FROM attribute_options AS o
        LEFT JOIN LATERAL (
            SELECT jsonb_object_agg(
                aol.locale, jsonb_build_object(
                    'label', aol.label, 'explanation', aol.explanation
                )
            ) AS localizations
            FROM attribute_option_localizations AS aol
            WHERE aol.option_id = o.id
        ) AS ol ON TRUE
        WHERE o.attribute_id = a.id
    ) AS opts ON TRUE
    WHERE a.status = 'published'
    ORDER BY a.key
    """
)

_LIST_QUESTIONS = text(
    """
    SELECT
        q.key,
        ad.key AS attribute_key,
        q.answer_type,
        q.priority,
        q.ai_rephrasing_allowed,
        COALESCE(loc.localizations, '{}'::jsonb) AS localizations
    FROM question_definitions AS q
    JOIN attribute_definitions AS ad ON ad.id = q.attribute_definition_id
    LEFT JOIN LATERAL (
        SELECT jsonb_object_agg(
            ql.locale, jsonb_build_object(
                'canonical_text', ql.canonical_text,
                'help_text', ql.help_text,
                'unknown_label', ql.unknown_label,
                'decline_label', ql.decline_label
            )
        ) AS localizations
        FROM question_localizations AS ql
        WHERE ql.question_id = q.id
    ) AS loc ON TRUE
    WHERE q.status = 'published'
    ORDER BY q.priority
    """
)


def _row_to_need(row: Mapping[str, Any]) -> NeedDefinition:
    return NeedDefinition(
        key=str(row["key"]),
        sort_order=int(row["sort_order"]),
        localizations=dict(row["localizations"]),
        icon=str(row["icon"]),
    )


def _row_to_attribute(row: Mapping[str, Any]) -> AttributeDefinition:
    return AttributeDefinition(
        key=str(row["key"]),
        value_type=row["value_type"],
        confirmation_required=bool(row["confirmation_required"]),
        skippable=bool(row["skippable"]),
        options=_options_from_payload(row["options"]),
    )


def _row_to_question(row: Mapping[str, Any]) -> QuestionDefinition:
    return QuestionDefinition(
        key=str(row["key"]),
        attribute_key=str(row["attribute_key"]),
        answer_type=row["answer_type"],
        priority=int(row["priority"]),
        ai_rephrasing_allowed=bool(row["ai_rephrasing_allowed"]),
        localizations=dict(row["localizations"]),
    )


class PostgresDialogueCatalogRepository:
    def __init__(self, database_url: str, *, engine: Engine | None = None) -> None:
        self._engine = engine or create_database_engine(database_url)

    def list_needs(self) -> tuple[NeedDefinition, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(_LIST_NEEDS).mappings().all()
        return tuple(_row_to_need(row) for row in rows)

    def list_attributes(self) -> tuple[AttributeDefinition, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(_LIST_ATTRIBUTES).mappings().all()
        return tuple(_row_to_attribute(row) for row in rows)

    def get_attribute(self, key: str) -> AttributeDefinition | None:
        for attribute in self.list_attributes():
            if attribute.key == key:
                return attribute
        return None

    def list_questions(self) -> tuple[QuestionDefinition, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(_LIST_QUESTIONS).mappings().all()
        return tuple(_row_to_question(row) for row in rows)

    def healthcheck(self) -> None:
        with self._engine.connect() as connection:
            connection.execute(text("SELECT 1"))

    def close(self) -> None:
        self._engine.dispose()
