import sys
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vesta_api.cli.provision_database_roles import (  # noqa: E402
    database_url_for_user,
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


if __name__ == "__main__":
    unittest.main()
