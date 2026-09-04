import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fastapi.testclient import TestClient  # noqa: E402

from vesta_api.api.routes import (  # noqa: E402
    dialogue_catalog_repository,
    matching_service,
    offer_repository,
)
from vesta_api.api.schemas import UserLocationInput  # noqa: E402
from vesta_api.domain.dialogue_catalog import NeedDefinition  # noqa: E402
from vesta_api.main import app  # noqa: E402
from vesta_api.services.matching import MatchingService  # noqa: E402


class UnavailableRepository:
    def healthcheck(self) -> None:
        raise ConnectionError("database is unavailable")


class EmptyOfferRepository:
    def list_offers(self) -> tuple[()]:
        return ()


class RoutesTest(unittest.TestCase):
    def test_health(self) -> None:
        with TestClient(app) as client:
            response = client.get("/health")

        self.assertEqual(200, response.status_code)
        self.assertEqual({"status": "ok"}, response.json())

    def test_ready_checks_repository(self) -> None:
        with TestClient(app) as client:
            response = client.get("/ready")

        self.assertEqual(200, response.status_code)
        self.assertEqual({"status": "ready"}, response.json())

    def test_ready_reports_unavailable_database(self) -> None:
        app.dependency_overrides[offer_repository] = UnavailableRepository
        try:
            with TestClient(app) as client:
                response = client.get("/ready")
        finally:
            app.dependency_overrides.clear()

        self.assertEqual(503, response.status_code)
        self.assertEqual({"detail": "database_unavailable"}, response.json())

    def test_match_returns_explicit_demo_result(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/v1/matches",
                json={
                    "need": "basic_needs",
                    "language": "fr",
                    "dog": True,
                    "has_identity_document": False,
                    "risk_flags": [],
                },
            )

        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertEqual("matches", payload["outcome"])
        self.assertEqual(1, len(payload["candidates"]))
        self.assertTrue(payload["candidates"][0]["offer"]["is_demo"])
        self.assertIsNone(payload["candidates"][0]["distance_meters"])
        self.assertIsNone(payload["candidates"][0]["offer"]["address"])
        self.assertIsNone(payload["candidates"][0]["offer"]["directions_url"])
        self.assertTrue(payload["disclaimer"].startswith("Prends directement contact"))

    def test_match_can_return_an_explicit_no_offer_outcome(self) -> None:
        app.dependency_overrides[matching_service] = lambda: MatchingService(
            EmptyOfferRepository()
        )
        try:
            with TestClient(app) as client:
                response = client.post(
                    "/v1/matches",
                    json={"need": "basic_needs", "language": "de"},
                )
        finally:
            app.dependency_overrides.clear()

        self.assertEqual(200, response.status_code)
        self.assertEqual("no_match", response.json()["outcome"])
        self.assertEqual([], response.json()["candidates"])
        self.assertFalse(response.json()["human_handoff_required"])

    def test_match_rejects_an_unknown_or_inactive_category(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/v1/matches",
                json={"need": "category_without_offers", "language": "de"},
            )

        self.assertEqual(422, response.status_code)
        self.assertEqual("unknown_or_inactive_category", response.json()["detail"])

    def test_public_category_catalog_is_localized_and_has_icons(self) -> None:
        with TestClient(app) as client:
            response = client.get("/v1/catalog/categories?language=fr")

        self.assertEqual(200, response.status_code)
        categories = response.json()["categories"]
        self.assertEqual(4, len(categories))
        self.assertEqual(
            {"sleep_tonight", "basic_needs", "counselling", "victim_support"},
            {category["key"] for category in categories},
        )
        self.assertTrue(all(category["title"] for category in categories))
        self.assertTrue(all(category["description"] for category in categories))
        self.assertEqual(
            {"home", "food", "book", "support"},
            {category["icon"] for category in categories},
        )

    def test_public_category_catalog_includes_a_new_repository_category(self) -> None:
        category = NeedDefinition(
            key="legal_help",
            sort_order=40,
            icon="support",
            localizations={
                "de": {"title": "Rechtshilfe", "description": "Hilfe bei Rechtsfragen"},
                "fr": {"title": "Aide juridique", "description": "Conseils juridiques"},
            },
        )
        catalog = Mock()
        catalog.list_needs.return_value = (category,)
        app.dependency_overrides[dialogue_catalog_repository] = lambda: catalog
        try:
            with TestClient(app) as client:
                response = client.get("/v1/catalog/categories?language=fr")
        finally:
            app.dependency_overrides.clear()

        self.assertEqual(200, response.status_code)
        self.assertEqual(
            {
                "key": "legal_help",
                "title": "Aide juridique",
                "description": "Conseils juridiques",
                "icon": "support",
            },
            response.json()["categories"][0],
        )

    def test_rejects_invalid_user_location(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/v1/matches",
                json={
                    "need": "basic_needs",
                    "language": "de",
                    "user_location": {
                        "latitude": 91,
                        "longitude": 7.447,
                    },
                },
            )

        self.assertEqual(422, response.status_code)

    def test_rejects_non_boolean_adult_status(self) -> None:
        with TestClient(app) as client:
            for value in (-1, 0, 18, "yes"):
                with self.subTest(value=value):
                    response = client.post(
                        "/v1/matches",
                        json={
                            "need": "sleep_tonight",
                            "language": "de",
                            "is_adult": value,
                        },
                    )

                    self.assertEqual(422, response.status_code)

    def test_accepts_boolean_adult_status(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/v1/matches",
                json={
                    "need": "sleep_tonight",
                    "language": "de",
                    "is_adult": True,
                },
            )

        self.assertEqual(200, response.status_code)

    def test_reduces_location_precision_before_matching(self) -> None:
        location = UserLocationInput(
            latitude=46.948123,
            longitude=7.447456,
        )

        self.assertEqual(46.948, location.latitude)
        self.assertEqual(7.447, location.longitude)

    def test_risk_flag_prevents_normal_matching(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/v1/matches",
                json={
                    "need": "sleep_tonight",
                    "language": "de",
                    "risk_flags": ["severe_injury"],
                },
            )

        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertEqual([], payload["candidates"])
        self.assertTrue(payload["human_handoff_required"])
        self.assertEqual("handoff", payload["outcome"])
        self.assertEqual("safety_rule_triggered", payload["handoff_reason"])


if __name__ == "__main__":
    unittest.main()
