import json
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

from sqlalchemy import Engine, text

from vesta_api.domain.models import (
    AccessRules,
    Availability,
    GeoPoint,
    Offer,
    OfferText,
    Source,
)
from vesta_api.repositories.admin_catalog import AdminCatalogRepository
from vesta_api.repositories.database import create_database_engine


class OfferRepository(Protocol):
    def list_offers(self) -> tuple[Offer, ...]: ...

    def healthcheck(self) -> None: ...

    def close(self) -> None: ...


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class JsonOfferRepository:
    def __init__(self, data_path: Path) -> None:
        self._data_path = data_path

    def list_offers(self) -> tuple[Offer, ...]:
        payload = json.loads(self._data_path.read_text(encoding="utf-8"))
        return tuple(self._to_offer(item) for item in payload["offers"])

    def healthcheck(self) -> None:
        self.list_offers()

    def close(self) -> None:
        return None


    @staticmethod
    def _to_offer(item: dict[str, object]) -> Offer:
        access = item["access"]
        source = item["source"]
        location = item.get("location")
        assert isinstance(access, dict)
        assert isinstance(source, dict)
        assert location is None or isinstance(location, dict)
        address = (
            str(location["address"])
            if location is not None and location.get("address")
            else None
        )

        return Offer(
            id=str(item["id"]),
            name=str(item["name"]),
            summary=str(item["summary"]),
            needs=tuple(str(value) for value in item["needs"]),
            languages=tuple(str(value).lower() for value in item["languages"]),
            access=AccessRules(
                accepts_dogs=access.get("accepts_dogs"),
                identity_document_required=access.get("identity_document_required"),
                accepted_genders=tuple(access.get("accepted_genders", [])),
                minimum_age=access.get("minimum_age"),
                maximum_age=access.get("maximum_age"),
            ),
            availability=Availability(str(item["availability"])),
            contact_note=str(item["contact_note"]),
            source=Source(
                label=str(source["label"]),
                url=str(source["url"]) if source.get("url") else None,
                verified_at=_parse_datetime(str(source["verified_at"])),
                expires_at=_parse_datetime(str(source["expires_at"])),
                verified_by=str(source["verified_by"]),
            ),
            location=(
                GeoPoint(
                    latitude=float(location["latitude"]),
                    longitude=float(location["longitude"]),
                    address=address,
                )
                if location is not None
                else None
            ),
            address=address,
            published=bool(item.get("published", False)),
            is_demo=bool(item.get("is_demo", False)),
            slug=str(item["slug"]) if item.get("slug") else None,
            organization_name=(
                str(item["organization_name"])
                if item.get("organization_name")
                else None
            ),
            updated_at=(
                _parse_datetime(str(item["updated_at"]))
                if item.get("updated_at")
                else None
            ),
        )


class AdminManagedOfferRepository:
    """Expose in-memory admin offer changes through public development matching."""

    def __init__(self, admin_catalog: AdminCatalogRepository) -> None:
        self._admin_catalog = admin_catalog

    def list_offers(self) -> tuple[Offer, ...]:
        offers: list[Offer] = []
        for item in self._admin_catalog.list_offers():
            access = item.access_rules
            location = (
                GeoPoint(
                    latitude=item.latitude,
                    longitude=item.longitude,
                    address=item.address,
                )
                if item.latitude is not None and item.longitude is not None
                else None
            )
            offers.append(
                Offer(
                    id=item.id,
                    slug=item.slug,
                    name=item.name,
                    organization_name=item.organization_name,
                    summary=item.summary,
                    needs=item.needs,
                    languages=item.languages,
                    access=AccessRules(
                        accepts_dogs=access.get("accepts_dogs"),  # type: ignore[arg-type]
                        identity_document_required=access.get(  # type: ignore[arg-type]
                            "identity_document_required"
                        ),
                        accepted_genders=tuple(access.get("accepted_genders", ())),  # type: ignore[arg-type]
                        minimum_age=access.get("minimum_age"),  # type: ignore[arg-type]
                        maximum_age=access.get("maximum_age"),  # type: ignore[arg-type]
                    ),
                    availability=Availability(item.availability),
                    contact_note=item.contact_note,
                    source=Source(
                        label=item.source_label,
                        url=item.source_url,
                        verified_at=item.verified_at,
                        expires_at=item.expires_at,
                        verified_by=item.verified_by,
                    ),
                    location=location,
                    address=item.address,
                    published=item.lifecycle == "published",
                    is_demo=item.is_demo,
                    updated_at=item.updated_at,
                    localizations={
                        locale: OfferText(
                            name=localization.name,
                            summary=localization.summary,
                            contact_note=localization.contact_note,
                        )
                        for locale, localization in item.localizations.items()
                        if localization.status == "reviewed"
                    },
                    localization_required=True,
                )
            )
        return tuple(offers)

    def healthcheck(self) -> None:
        self._admin_catalog.healthcheck()

    def close(self) -> None:
        return None


_LIST_OFFERS = text(
    """
    SELECT
        offer.id::text AS id,
        offer.slug,
        offer.name,
        offer.summary,
        offer.languages,
        offer.access_rules,
        offer.contact,
        ST_Y(offer.location::geometry) AS latitude,
        ST_X(offer.location::geometry) AS longitude,
        offer.availability::text AS availability,
        offer.published,
        offer.is_demo,
        offer.updated_at,
        organization.name AS organization_name,
        categories.needs,
        verification.source_label,
        verification.source_url,
        verification.verified_by,
        verification.verified_at,
        verification.expires_at,
        COALESCE(localizations.items, '{}'::jsonb) AS localizations
    FROM offers AS offer
    JOIN organizations AS organization ON organization.id = offer.organization_id
    JOIN LATERAL (
        SELECT
            source_label,
            source_url,
            verified_by,
            verified_at,
            expires_at
        FROM offer_verifications
        WHERE offer_id = offer.id
        ORDER BY verified_at DESC, created_at DESC
        LIMIT 1
    ) AS verification ON TRUE
    JOIN LATERAL (
        SELECT COALESCE(
            array_agg(category ORDER BY category),
            ARRAY[]::text[]
        ) AS needs
        FROM offer_categories
        WHERE offer_id = offer.id
    ) AS categories ON TRUE
    LEFT JOIN LATERAL (
        SELECT jsonb_object_agg(
            locale,
            jsonb_build_object(
                'name', name,
                'summary', summary,
                'contact_note', contact_note
            )
        ) AS items
        FROM offer_localizations
        WHERE offer_id = offer.id AND status = 'reviewed'
    ) AS localizations ON TRUE
    ORDER BY offer.name, offer.id
    """
)


def _postgres_row_to_offer(row: Mapping[str, Any]) -> Offer:
    access = row["access_rules"] or {}
    contact = row["contact"] or {}
    address = str(contact["address"]) if contact.get("address") else None

    return Offer(
        id=str(row["id"]),
        name=str(row["name"]),
        summary=str(row["summary"]),
        needs=tuple(str(value) for value in row["needs"]),
        languages=tuple(str(value).lower() for value in row["languages"]),
        access=AccessRules(
            accepts_dogs=access.get("accepts_dogs"),
            identity_document_required=access.get("identity_document_required"),
            accepted_genders=tuple(access.get("accepted_genders", [])),
            minimum_age=access.get("minimum_age"),
            maximum_age=access.get("maximum_age"),
        ),
        availability=Availability(str(row["availability"])),
        contact_note=str(contact.get("note", "")),
        source=Source(
            label=str(row["source_label"]),
            url=str(row["source_url"]) if row["source_url"] else None,
            verified_at=row["verified_at"],
            expires_at=row["expires_at"],
            verified_by=str(row["verified_by"]),
        ),
        location=(
            GeoPoint(
                latitude=float(row["latitude"]),
                longitude=float(row["longitude"]),
                address=address,
            )
            if row["latitude"] is not None and row["longitude"] is not None
            else None
        ),
        address=address,
        published=bool(row["published"]),
        is_demo=bool(row["is_demo"]),
        slug=str(row["slug"]),
        organization_name=str(row["organization_name"]),
        updated_at=row["updated_at"],
        localizations={
            str(locale): OfferText(
                name=str(values["name"]),
                summary=str(values["summary"]),
                contact_note=str(values["contact_note"]),
            )
            for locale, values in (row.get("localizations") or {}).items()
        },
        localization_required=True,
    )


class PostgresOfferRepository:
    def __init__(self, database_url: str, *, engine: Engine | None = None) -> None:
        self._engine = engine or create_database_engine(database_url)

    def list_offers(self) -> tuple[Offer, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(_LIST_OFFERS).mappings().all()
        return tuple(_postgres_row_to_offer(row) for row in rows)

    def healthcheck(self) -> None:
        with self._engine.connect() as connection:
            connection.execute(text("SELECT 1"))

    def close(self) -> None:
        self._engine.dispose()
