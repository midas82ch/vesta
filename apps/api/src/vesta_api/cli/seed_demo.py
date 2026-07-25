import json
from datetime import datetime
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import Engine, text

from vesta_api.config import settings
from vesta_api.repositories.database import create_database_engine

_UPSERT_ORGANIZATION = text(
    """
    INSERT INTO organizations (id, name)
    VALUES (:id, :name)
    ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name
    """
)

_UPSERT_OFFER = text(
    """
    INSERT INTO offers (
        id,
        organization_id,
        slug,
        name,
        summary,
        languages,
        access_rules,
        contact,
        availability,
        published,
        is_demo,
        updated_at
    )
    VALUES (
        :id,
        :organization_id,
        :slug,
        :name,
        :summary,
        :languages,
        CAST(:access_rules AS jsonb),
        CAST(:contact AS jsonb),
        CAST(:availability AS offer_availability),
        :published,
        :is_demo,
        now()
    )
    ON CONFLICT (id) DO UPDATE SET
        organization_id = EXCLUDED.organization_id,
        slug = EXCLUDED.slug,
        name = EXCLUDED.name,
        summary = EXCLUDED.summary,
        languages = EXCLUDED.languages,
        access_rules = EXCLUDED.access_rules,
        contact = EXCLUDED.contact,
        availability = EXCLUDED.availability,
        published = EXCLUDED.published,
        is_demo = EXCLUDED.is_demo,
        updated_at = now()
    """
)

_DELETE_CATEGORIES = text(
    "DELETE FROM offer_categories WHERE offer_id = :offer_id"
)
_INSERT_CATEGORY = text(
    """
    INSERT INTO offer_categories (offer_id, category)
    VALUES (:offer_id, :category)
    ON CONFLICT DO NOTHING
    """
)
_UPSERT_VERIFICATION = text(
    """
    INSERT INTO offer_verifications (
        id,
        offer_id,
        source_label,
        source_url,
        verified_by,
        verified_at,
        expires_at,
        notes
    )
    VALUES (
        :id,
        :offer_id,
        :source_label,
        :source_url,
        :verified_by,
        :verified_at,
        :expires_at,
        :notes
    )
    ON CONFLICT (id) DO UPDATE SET
        source_label = EXCLUDED.source_label,
        source_url = EXCLUDED.source_url,
        verified_by = EXCLUDED.verified_by,
        verified_at = EXCLUDED.verified_at,
        expires_at = EXCLUDED.expires_at,
        notes = EXCLUDED.notes
    """
)


def _datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def seed_demo_offers(engine: Engine, data_path: Path) -> int:
    payload = json.loads(data_path.read_text(encoding="utf-8"))
    organization_id = uuid5(NAMESPACE_URL, "https://vesta.example/demo-organization")

    with engine.begin() as connection:
        connection.execute(
            _UPSERT_ORGANIZATION,
            {"id": organization_id, "name": "Vesta Demo-Daten"},
        )

        for item in payload["offers"]:
            slug = str(item["id"])
            offer_id = uuid5(NAMESPACE_URL, f"https://vesta.example/offers/{slug}")
            access = item["access"]
            source = item["source"]

            connection.execute(
                _UPSERT_OFFER,
                {
                    "id": offer_id,
                    "organization_id": organization_id,
                    "slug": slug,
                    "name": item["name"],
                    "summary": item["summary"],
                    "languages": item["languages"],
                    "access_rules": json.dumps(access),
                    "contact": json.dumps({"note": item["contact_note"]}),
                    "availability": item["availability"],
                    "published": item.get("published", False),
                    "is_demo": item.get("is_demo", False),
                },
            )
            connection.execute(_DELETE_CATEGORIES, {"offer_id": offer_id})
            categories = [
                {"offer_id": offer_id, "category": category}
                for category in item["needs"]
            ]
            if categories:
                connection.execute(_INSERT_CATEGORY, categories)

            verification_id = uuid5(
                NAMESPACE_URL,
                (
                    "https://vesta.example/verifications/"
                    f"{slug}/{source['verified_at']}"
                ),
            )
            connection.execute(
                _UPSERT_VERIFICATION,
                {
                    "id": verification_id,
                    "offer_id": offer_id,
                    "source_label": source["label"],
                    "source_url": source.get("url"),
                    "verified_by": source["verified_by"],
                    "verified_at": _datetime(source["verified_at"]),
                    "expires_at": _datetime(source["expires_at"]),
                    "notes": "Automatisch importierter Demo-Datensatz.",
                },
            )

    return len(payload["offers"])


def main() -> None:
    database_url = settings.get_database_url()
    if database_url is None:
        raise RuntimeError("DATABASE_URL is required to seed demo offers")

    engine = create_database_engine(database_url)
    try:
        count = seed_demo_offers(engine, settings.offer_data_path)
    finally:
        engine.dispose()
    print(f"Seeded {count} demo offers.")


if __name__ == "__main__":
    main()
