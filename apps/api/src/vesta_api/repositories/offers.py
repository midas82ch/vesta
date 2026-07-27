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
    Need,
    Offer,
    Source,
)
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

        return Offer(
            id=str(item["id"]),
            name=str(item["name"]),
            summary=str(item["summary"]),
            needs=tuple(Need(value) for value in item["needs"]),
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
                    address=(
                        str(location["address"])
                        if location.get("address")
                        else None
                    ),
                )
                if location is not None
                else None
            ),
            published=bool(item.get("published", False)),
            is_demo=bool(item.get("is_demo", False)),
        )


_LIST_OFFERS = text(
    """
    SELECT
        offer.id::text AS id,
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
        categories.needs,
        verification.source_label,
        verification.source_url,
        verification.verified_by,
        verification.verified_at,
        verification.expires_at
    FROM offers AS offer
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
    ORDER BY offer.name, offer.id
    """
)


def _postgres_row_to_offer(row: Mapping[str, Any]) -> Offer:
    access = row["access_rules"] or {}
    contact = row["contact"] or {}

    return Offer(
        id=str(row["id"]),
        name=str(row["name"]),
        summary=str(row["summary"]),
        needs=tuple(Need(value) for value in row["needs"]),
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
                address=(
                    str(contact["address"])
                    if contact.get("address")
                    else None
                ),
            )
            if row["latitude"] is not None and row["longitude"] is not None
            else None
        ),
        published=bool(row["published"]),
        is_demo=bool(row["is_demo"]),
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
