import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fastapi.testclient import TestClient  # noqa: E402

from vesta_api.api.routes import offer_repository  # noqa: E402
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
