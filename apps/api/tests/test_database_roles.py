import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.parse import unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vesta_api.cli.provision_database_roles import (  # noqa: E402
    ROLES,
    _ensure_login_role,
    database_url_for_user,
)

DIALOGUE_CATALOG_TABLES = frozenset(
    {
        "need_definitions",
        "need_localizations",
        "attribute_definitions",
        "attribute_options",
        "attribute_option_localizations",
        "question_definitions",
        "question_localizations",
    }
)


class DatabaseRolePrivilegesTest(unittest.TestCase):
    def test_vesta_app_can_read_the_dialogue_catalog_tables(self) -> None:
        # Regression test: the 20260726_0004 migration added these tables but
        # the restricted vesta_app role was never granted SELECT on them,
        # which crashed the API in production on the next restart even
        # though every local test and the migration itself passed.
        vesta_app = next(role for role in ROLES if role.username == "vesta_app")

        missing = DIALOGUE_CATALOG_TABLES - vesta_app.table_privileges.keys()
        self.assertEqual(set(), missing)

        for table in DIALOGUE_CATALOG_TABLES:
            self.assertIn("SELECT", vesta_app.table_privileges[table])

    def test_vesta_app_can_read_admin_users_and_write_the_ai_audit_log(self) -> None:
        # Same class of regression as above, this time for the 20260727_0005
        # migration (admin_users, ai_interaction_log).
        vesta_app = next(role for role in ROLES if role.username == "vesta_app")

        self.assertIn("admin_users", vesta_app.table_privileges)
        self.assertIn("SELECT", vesta_app.table_privileges["admin_users"])

        self.assertIn("ai_interaction_log", vesta_app.table_privileges)
        for privilege in ("SELECT", "INSERT"):
            self.assertIn(privilege, vesta_app.table_privileges["ai_interaction_log"])
        self.assertNotIn("DELETE", vesta_app.table_privileges["ai_interaction_log"])

        self.assertIn("dialogue_workflow_log", vesta_app.table_privileges)
        self.assertEqual(
            ("SELECT", "INSERT"),
            vesta_app.table_privileges["dialogue_workflow_log"],
        )

    def test_vesta_app_can_read_offer_ingestion_runs(self) -> None:
        # Same class of regression as above: the admin area needs to read
        # offer_ingestion_runs (20260725_0002), but only vesta_ingest ever
        # got granted access to it.
        vesta_app = next(role for role in ROLES if role.username == "vesta_app")

        self.assertIn("offer_ingestion_runs", vesta_app.table_privileges)
        self.assertEqual(
            ("SELECT",), vesta_app.table_privileges["offer_ingestion_runs"]
        )


class DatabaseRoleUrlTest(unittest.TestCase):
    def test_replaces_admin_credentials_and_preserves_tls(self) -> None:
        database_url = database_url_for_user(
            "postgresql://avnadmin:admin-secret@db.example:21699/defaultdb"
            "?sslmode=require",
            "vesta_app",
            "app:/?#[]@ secret",
        )
        parsed = urlsplit(database_url)

        self.assertEqual("vesta_app", parsed.username)
        self.assertEqual("app:/?#[]@ secret", unquote(parsed.password or ""))
        self.assertEqual("db.example", parsed.hostname)
        self.assertEqual(21699, parsed.port)
        self.assertEqual("/defaultdb", parsed.path)
        self.assertEqual("sslmode=require", parsed.query)
        self.assertNotIn("avnadmin", database_url)
        self.assertNotIn("admin-secret", database_url)


class DatabaseRoleProvisioningTest(unittest.TestCase):
    @patch("vesta_api.cli.provision_database_roles._role_exists", return_value=True)
    def test_existing_role_without_password_rotation_is_not_altered(
        self,
        _role_exists: Mock,
    ) -> None:
        connection = Mock()

        _ensure_login_role(
            connection,
            "vesta_app",
            "existing-password",
            reset_password=False,
        )

        connection.execute.assert_not_called()

    @patch("vesta_api.cli.provision_database_roles._role_exists", return_value=True)
    def test_existing_role_password_rotation_avoids_superuser_attributes(
        self,
        _role_exists: Mock,
    ) -> None:
        connection = Mock()

        _ensure_login_role(
            connection,
            "vesta_app",
            "new-password",
            reset_password=True,
        )

        query = repr(connection.execute.call_args.args[0])
        self.assertIn("ALTER ROLE", query)
        self.assertIn("LOGIN PASSWORD", query)
        self.assertNotIn("NOSUPERUSER", query)
        self.assertNotIn("NOREPLICATION", query)

    @patch("vesta_api.cli.provision_database_roles._role_exists", return_value=False)
    def test_new_role_receives_all_restrictive_attributes(
        self,
        _role_exists: Mock,
    ) -> None:
        connection = Mock()

        _ensure_login_role(
            connection,
            "vesta_app",
            "new-password",
            reset_password=True,
        )

        query = repr(connection.execute.call_args.args[0])
        self.assertIn("CREATE ROLE", query)
        self.assertIn("NOSUPERUSER", query)
        self.assertIn("NOREPLICATION", query)


if __name__ == "__main__":
    unittest.main()
