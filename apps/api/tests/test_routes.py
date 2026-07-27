import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fastapi.testclient import TestClient  # noqa: E402

from vesta_api.api.routes import offer_repository  # noqa: E402
from vesta_api.api.schemas import UserLocationInput  # noqa: E402
from vesta_api.main import app  # noqa: E402


class UnavailableRepository:
    def healthcheck(self) -> None:
        raise ConnectionError("database is unavailable")


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
        self.assertEqual(1, len(payload["candidates"]))
        self.assertTrue(payload["candidates"][0]["offer"]["is_demo"])
        self.assertIsNone(payload["candidates"][0]["distance_meters"])
        self.assertIsNone(payload["candidates"][0]["offer"]["address"])
        self.assertIsNone(payload["candidates"][0]["offer"]["directions_url"])

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

    def test_rejects_age_below_six(self) -> None:
        with TestClient(app) as client:
            for age in (-1, 0, 5):
                with self.subTest(age=age):
                    response = client.post(
                        "/v1/matches",
                        json={
                            "need": "sleep_tonight",
                            "language": "de",
                            "age": age,
                        },
                    )

                    self.assertEqual(422, response.status_code)

    def test_accepts_age_six(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/v1/matches",
                json={
                    "need": "sleep_tonight",
                    "language": "de",
                    "age": 6,
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
        self.assertEqual("safety_rule_triggered", payload["handoff_reason"])


if __name__ == "__main__":
    unittest.main()
