import sys
import unittest
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fastapi.testclient import TestClient  # noqa: E402

from vesta_api.api.admin_routes import (  # noqa: E402
    admin_login_attempt_store,
    admin_offer_repository,
    admin_session_store,
    admin_user_repository,
    ai_audit_log_repository,
    ingestion_run_repository,
    workflow_audit_log_repository,
)
from vesta_api.config import settings  # noqa: E402
from vesta_api.domain.audit_models import NewAiAuditEntry  # noqa: E402
from vesta_api.domain.ingestion_models import IngestionRun  # noqa: E402
from vesta_api.domain.workflow_audit_models import (  # noqa: E402
    NewWorkflowAuditEvent,
)
from vesta_api.main import app  # noqa: E402
from vesta_api.repositories.admin_users import InMemoryAdminUserRepository  # noqa: E402
from vesta_api.repositories.ai_audit_log import InMemoryAiAuditLogRepository  # noqa: E402
from vesta_api.repositories.ingestion_runs import (  # noqa: E402
    InMemoryIngestionRunRepository,
)
from vesta_api.repositories.offers import JsonOfferRepository  # noqa: E402
from vesta_api.repositories.workflow_audit_log import (  # noqa: E402
    InMemoryWorkflowAuditLogRepository,
)
from vesta_api.security import (  # noqa: E402
    AdminLoginAttemptStore,
    AdminSessionStore,
    hash_password,
)

TEST_USERNAME = "test-admin"
TEST_PASSWORD = "correct-horse-battery-staple"


class AdminRoutesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.users = InMemoryAdminUserRepository()
        self.users.create(username=TEST_USERNAME, password_hash=hash_password(TEST_PASSWORD))
        self.audit_log = InMemoryAiAuditLogRepository()
        self.workflow_log = InMemoryWorkflowAuditLogRepository()
        self.ingestion_runs = InMemoryIngestionRunRepository()
        self.offers = JsonOfferRepository(
            Path(__file__).resolve().parents[3] / "data" / "seed" / "offers.example.json"
        )
        self.sessions = AdminSessionStore()
        self.attempts = AdminLoginAttemptStore()

        app.dependency_overrides[admin_user_repository] = lambda: self.users
        app.dependency_overrides[admin_session_store] = lambda: self.sessions
        app.dependency_overrides[admin_login_attempt_store] = lambda: self.attempts
        app.dependency_overrides[ai_audit_log_repository] = lambda: self.audit_log
        app.dependency_overrides[workflow_audit_log_repository] = (
            lambda: self.workflow_log
        )
        app.dependency_overrides[ingestion_run_repository] = lambda: self.ingestion_runs
        app.dependency_overrides[admin_offer_repository] = lambda: self.offers

    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def test_list_requires_a_session(self) -> None:
        with TestClient(app) as client:
            response = client.get("/v1/admin/ai-audit-log")

        self.assertEqual(401, response.status_code)

    def test_login_rejects_wrong_password(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/v1/admin/login",
                json={"username": TEST_USERNAME, "password": "wrong"},
            )

        self.assertEqual(401, response.status_code)
        self.assertNotIn("set-cookie", response.headers)

    def test_login_rejects_inactive_user(self) -> None:
        user = self.users.get_by_username(TEST_USERNAME)
        assert user is not None
        inactive_users = Mock()
        inactive_users.get_by_username.return_value = replace(user, is_active=False)
        app.dependency_overrides[admin_user_repository] = lambda: inactive_users

        with TestClient(app) as client:
            response = client.post(
                "/v1/admin/login",
                json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            )

        self.assertEqual(401, response.status_code)
        self.assertNotIn("set-cookie", response.headers)

    def test_login_then_list_and_detail(self) -> None:
        self.audit_log.record(
            NewAiAuditEntry(
                port="explain",
                provider="openai",
                model="gpt-5.4-mini",
                outcome="ai",
                request_text="the prompt",
                response_text="the answer",
                session_id="sess-1",
            )
        )

        with TestClient(app) as client:
            login = client.post(
                "/v1/admin/login",
                json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            )
            self.assertEqual(200, login.status_code)
            self.assertIn("HttpOnly", login.headers["set-cookie"])
            self.assertIn("SameSite=strict", login.headers["set-cookie"])

            listing = client.get("/v1/admin/ai-audit-log")
            self.assertEqual(200, listing.status_code)
            entries = listing.json()["entries"]
            self.assertEqual(1, len(entries))
            self.assertEqual("sess-1", entries[0]["session_id"])

            detail = client.get(f"/v1/admin/ai-audit-log/{entries[0]['id']}")
            self.assertEqual(200, detail.status_code)
            self.assertEqual("the prompt", detail.json()["request_text"])
            self.assertEqual("the answer", detail.json()["response_text"])

    def test_detail_for_unknown_id_returns_404(self) -> None:
        with TestClient(app) as client:
            client.post(
                "/v1/admin/login",
                json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            )
            response = client.get("/v1/admin/ai-audit-log/does-not-exist")

        self.assertEqual(404, response.status_code)

    def test_login_then_list_and_open_workflow(self) -> None:
        for stage in ("input", "system", "output"):
            self.workflow_log.record(
                NewWorkflowAuditEvent(
                    workflow_id="workflow-1",
                    stage=stage,
                    event_type=f"{stage}_event",
                    summary=f"{stage} summary",
                    payload={"stage": stage},
                )
            )
        self.audit_log.record(
            NewAiAuditEntry(
                port="interpret",
                provider="openai",
                model="gpt-5.4-mini",
                outcome="ai",
                request_text="the prompt",
                response_text="the answer",
                session_id="workflow-1",
            )
        )

        with TestClient(app) as client:
            client.post(
                "/v1/admin/login",
                json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            )
            listing = client.get("/v1/admin/ai-audit-workflows")
            workflow_id = listing.json()["workflows"][0]["workflow_id"]
            detail = client.get(f"/v1/admin/ai-audit-workflows/{workflow_id}")

        self.assertEqual(200, listing.status_code)
        summary = listing.json()["workflows"][0]
        self.assertEqual("workflow-1", summary["workflow_id"])
        self.assertTrue(summary["complete"])
        self.assertEqual(1, summary["ai_call_count"])
        self.assertEqual(200, detail.status_code)
        self.assertEqual(
            ("input", "system", "output", "ai"),
            tuple(step["kind"] for step in detail.json()["steps"]),
        )
        ai_step = next(
            step for step in detail.json()["steps"] if step["kind"] == "ai"
        )
        self.assertEqual("AI · Eingabe verstehen", ai_step["label"])
        self.assertEqual("the prompt", ai_step["details"]["request_text"])

    def test_historical_ai_entry_is_available_as_partial_workflow(self) -> None:
        self.audit_log.record(
            NewAiAuditEntry(
                port="explain",
                provider="openai",
                model="gpt-5.4-mini",
                outcome="ai",
                request_text="historical prompt",
                response_text="historical answer",
                session_id=None,
            )
        )
        entry = self.audit_log.list_entries(limit=1, offset=0)[0]

        with TestClient(app) as client:
            client.post(
                "/v1/admin/login",
                json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            )
            listing = client.get("/v1/admin/ai-audit-workflows")
            workflow = listing.json()["workflows"][0]
            detail = client.get(
                f"/v1/admin/ai-audit-workflows/{workflow['workflow_id']}"
            )

        self.assertEqual(200, listing.status_code)
        self.assertEqual(f"legacy__{entry.id}", workflow["workflow_id"])
        self.assertFalse(workflow["complete"])
        self.assertEqual(200, detail.status_code)
        self.assertEqual(("ai",), tuple(step["kind"] for step in detail.json()["steps"]))
        self.assertEqual(
            "historical answer",
            detail.json()["steps"][0]["details"]["response_text"],
        )

    def test_workflow_endpoints_require_a_session(self) -> None:
        with TestClient(app) as client:
            listing = client.get("/v1/admin/ai-audit-workflows")
            detail = client.get("/v1/admin/ai-audit-workflows/workflow-1")

        self.assertEqual(401, listing.status_code)
        self.assertEqual(401, detail.status_code)

    def test_unknown_workflow_returns_404(self) -> None:
        with TestClient(app) as client:
            client.post(
                "/v1/admin/login",
                json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            )
            response = client.get("/v1/admin/ai-audit-workflows/does-not-exist")

        self.assertEqual(404, response.status_code)

    def test_workflow_list_rejects_invalid_pagination(self) -> None:
        with TestClient(app) as client:
            client.post(
                "/v1/admin/login",
                json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            )

            for query in ("limit=0", "limit=201", "offset=-1"):
                with self.subTest(query=query):
                    response = client.get(f"/v1/admin/ai-audit-workflows?{query}")
                    self.assertEqual(422, response.status_code)

    def test_logout_revokes_the_session(self) -> None:
        with TestClient(app) as client:
            client.post(
                "/v1/admin/login",
                json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            )
            client.post("/v1/admin/logout")
            response = client.get("/v1/admin/ai-audit-log")

        self.assertEqual(401, response.status_code)

    def test_sixth_failed_login_is_rate_limited(self) -> None:
        with TestClient(app) as client:
            for _ in range(5):
                response = client.post(
                    "/v1/admin/login",
                    json={"username": TEST_USERNAME, "password": "wrong"},
                )
                self.assertEqual(401, response.status_code)

            limited = client.post(
                "/v1/admin/login",
                json={"username": TEST_USERNAME, "password": "wrong"},
            )

        self.assertEqual(429, limited.status_code)
        self.assertGreater(int(limited.headers["retry-after"]), 0)

    def test_successful_login_clears_previous_failures(self) -> None:
        with TestClient(app) as client:
            client.post(
                "/v1/admin/login",
                json={"username": TEST_USERNAME, "password": "wrong"},
            )
            success = client.post(
                "/v1/admin/login",
                json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            )
            self.assertEqual(200, success.status_code)

            for _ in range(5):
                response = client.post(
                    "/v1/admin/login",
                    json={"username": TEST_USERNAME, "password": "wrong"},
                )

        self.assertEqual(401, response.status_code)

    def test_production_cookie_is_secure(self) -> None:
        with TestClient(app, base_url="https://testserver") as client:
            original_environment = settings.environment
            settings.environment = "production"
            try:
                response = client.post(
                    "/v1/admin/login",
                    json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
                )
            finally:
                settings.environment = original_environment

        self.assertEqual(200, response.status_code)
        self.assertIn("Secure", response.headers["set-cookie"])

    def test_list_rejects_invalid_pagination_and_filters(self) -> None:
        with TestClient(app) as client:
            client.post(
                "/v1/admin/login",
                json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            )

            for query in (
                "limit=0",
                "limit=201",
                "offset=-1",
                "port=unknown",
                "outcome=unknown",
            ):
                with self.subTest(query=query):
                    response = client.get(f"/v1/admin/ai-audit-log?{query}")
                    self.assertEqual(422, response.status_code)

    def test_ingestion_runs_requires_a_session(self) -> None:
        with TestClient(app) as client:
            response = client.get("/v1/admin/ingestion-runs")

        self.assertEqual(401, response.status_code)

    def test_login_then_list_ingestion_runs(self) -> None:
        self.ingestion_runs.add(
            IngestionRun(
                id="run-1",
                offer_slug="test-passantenheim-bern",
                source_url="https://example.org/passantenheim",
                status="imported",
                http_status=200,
                content_sha256="abc123",
                missing_evidence=(),
                error=None,
                checked_at=datetime(2026, 7, 27, 5, 33, tzinfo=UTC),
            )
        )
        self.ingestion_runs.add(
            IngestionRun(
                id="run-2",
                offer_slug="test-wohnberatung-bern",
                source_url="https://example.org/wohnberatung",
                status="evidence_missing",
                http_status=200,
                content_sha256="def456",
                missing_evidence=("Öffnungszeiten",),
                error=None,
                checked_at=datetime(2026, 7, 26, 5, 33, tzinfo=UTC),
            )
        )

        with TestClient(app) as client:
            client.post(
                "/v1/admin/login",
                json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            )
            response = client.get("/v1/admin/ingestion-runs")

        self.assertEqual(200, response.status_code)
        runs = response.json()["runs"]
        self.assertEqual(2, len(runs))
        # Newest first.
        self.assertEqual("run-1", runs[0]["id"])
        self.assertEqual("imported", runs[0]["status"])
        self.assertEqual(["Öffnungszeiten"], runs[1]["missing_evidence"])

    def test_ingestion_runs_filters_by_status(self) -> None:
        self.ingestion_runs.add(
            IngestionRun(
                id="run-1",
                offer_slug="test-a",
                source_url="https://example.org/a",
                status="imported",
                http_status=200,
                content_sha256=None,
                missing_evidence=(),
                error=None,
                checked_at=datetime(2026, 7, 27, 5, 33, tzinfo=UTC),
            )
        )
        self.ingestion_runs.add(
            IngestionRun(
                id="run-2",
                offer_slug="test-b",
                source_url="https://example.org/b",
                status="fetch_failed",
                http_status=None,
                content_sha256=None,
                missing_evidence=(),
                error="ConnectionError: timed out",
                checked_at=datetime(2026, 7, 27, 5, 34, tzinfo=UTC),
            )
        )

        with TestClient(app) as client:
            client.post(
                "/v1/admin/login",
                json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            )
            response = client.get("/v1/admin/ingestion-runs?status=fetch_failed")

        self.assertEqual(200, response.status_code)
        runs = response.json()["runs"]
        self.assertEqual(1, len(runs))
        self.assertEqual("run-2", runs[0]["id"])
        self.assertEqual("ConnectionError: timed out", runs[0]["error"])

    def test_ingestion_runs_rejects_invalid_pagination_and_status(self) -> None:
        with TestClient(app) as client:
            client.post(
                "/v1/admin/login",
                json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            )

            for query in ("limit=0", "limit=201", "offset=-1", "status=unknown"):
                with self.subTest(query=query):
                    response = client.get(f"/v1/admin/ingestion-runs?{query}")
                    self.assertEqual(422, response.status_code)

    def test_offers_require_a_session(self) -> None:
        with TestClient(app) as client:
            response = client.get("/v1/admin/offers")

        self.assertEqual(401, response.status_code)

    def test_login_then_list_all_offers(self) -> None:
        with TestClient(app) as client:
            client.post(
                "/v1/admin/login",
                json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            )
            response = client.get("/v1/admin/offers")

        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertEqual(3, payload["total"])
        self.assertEqual(50, payload["limit"])
        self.assertEqual(0, payload["offset"])
        self.assertEqual(3, len(payload["offers"]))
        offer = payload["offers"][0]
        self.assertEqual("demo-sleep", offer["id"])
        self.assertEqual(["sleep_tonight"], offer["needs"])
        self.assertTrue(offer["published"])
        self.assertTrue(offer["is_demo"])
        self.assertEqual("Vesta Testfixture", offer["source_label"])

    def test_offers_support_pagination(self) -> None:
        with TestClient(app) as client:
            client.post(
                "/v1/admin/login",
                json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            )
            response = client.get("/v1/admin/offers?limit=1&offset=1")

        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertEqual(3, payload["total"])
        self.assertEqual(1, payload["limit"])
        self.assertEqual(1, payload["offset"])
        self.assertEqual(1, len(payload["offers"]))
        self.assertEqual("demo-basic-needs", payload["offers"][0]["id"])

    def test_offers_reject_invalid_pagination(self) -> None:
        with TestClient(app) as client:
            client.post(
                "/v1/admin/login",
                json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            )

            for query in ("limit=0", "limit=201", "offset=-1"):
                with self.subTest(query=query):
                    response = client.get(f"/v1/admin/offers?{query}")
                    self.assertEqual(422, response.status_code)


if __name__ == "__main__":
    unittest.main()
