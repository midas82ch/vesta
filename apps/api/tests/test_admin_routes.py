import sys
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fastapi.testclient import TestClient  # noqa: E402

from vesta_api.api.admin_routes import (  # noqa: E402
    admin_login_attempt_store,
    admin_session_store,
    admin_user_repository,
    ai_audit_log_repository,
)
from vesta_api.config import settings  # noqa: E402
from vesta_api.domain.audit_models import NewAiAuditEntry  # noqa: E402
from vesta_api.main import app  # noqa: E402
from vesta_api.repositories.admin_users import InMemoryAdminUserRepository  # noqa: E402
from vesta_api.repositories.ai_audit_log import InMemoryAiAuditLogRepository  # noqa: E402
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
        self.sessions = AdminSessionStore()
        self.attempts = AdminLoginAttemptStore()

        app.dependency_overrides[admin_user_repository] = lambda: self.users
        app.dependency_overrides[admin_session_store] = lambda: self.sessions
        app.dependency_overrides[admin_login_attempt_store] = lambda: self.attempts
        app.dependency_overrides[ai_audit_log_repository] = lambda: self.audit_log

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


if __name__ == "__main__":
    unittest.main()
