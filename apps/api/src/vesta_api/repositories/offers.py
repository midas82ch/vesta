import json
from datetime import datetime
from pathlib import Path
from typing import Protocol

from vesta_api.domain.models import AccessRules, Availability, Need, Offer, Source


class OfferRepository(Protocol):
    def list_offers(self) -> tuple[Offer, ...]: ...


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class JsonOfferRepository:
    def __init__(self, data_path: Path) -> None:
        self._data_path = data_path

    def list_offers(self) -> tuple[Offer, ...]:
        payload = json.loads(self._data_path.read_text(encoding="utf-8"))
        return tuple(self._to_offer(item) for item in payload["offers"])

    @staticmethod
    def _to_offer(item: dict[str, object]) -> Offer:
        access = item["access"]
        source = item["source"]
        assert isinstance(access, dict)
        assert isinstance(source, dict)

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
            published=bool(item.get("published", False)),
            is_demo=bool(item.get("is_demo", False)),
        )
