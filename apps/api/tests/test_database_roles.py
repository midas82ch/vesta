import sys
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vesta_api.cli.provision_database_roles import (  # noqa: E402
    ROLES,
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


if __name__ == "__main__":
    unittest.main()
