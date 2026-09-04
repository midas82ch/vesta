import sys
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vesta_api.config import Settings  # noqa: E402
from vesta_api.domain.models import Availability, Need  # noqa: E402
from vesta_api.repositories.database import sqlalchemy_database_url  # noqa: E402
from vesta_api.repositories.offers import _postgres_row_to_offer  # noqa: E402


class DatabaseConfigurationTest(unittest.TestCase):
    def test_normalizes_standard_postgresql_uri(self) -> None:
        self.assertEqual(
            "postgresql+psycopg://user:secret@database.example/vesta"
            "?sslmode=require",
            sqlalchemy_database_url(
                "postgresql://user:secret@database.example/vesta"
                "?sslmode=require"
            ),
        )

    def test_reads_database_url_from_secret_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            secret_file = Path(temporary_directory) / "database-url"
            secret_file.write_text(
                "postgresql://user:secret@database.example/vesta"
                "?sslmode=require\n",
                encoding="utf-8",
            )
            settings = Settings(
                _env_file=None,
                VESTA_ENV="production",
                DATABASE_URL_FILE=secret_file,
            )

            database_url = settings.get_database_url()

        self.assertEqual(
            "postgresql://user:secret@database.example/vesta?sslmode=require",
            database_url,
        )

    def test_rejects_unencrypted_production_database_url(self) -> None:
        settings = Settings(
            _env_file=None,
            VESTA_ENV="production",
            DATABASE_URL="postgresql://user:secret@database.example/vesta",
        )

        with self.assertRaisesRegex(RuntimeError, "sslmode"):
            settings.get_database_url()

    def test_reads_separate_admin_database_url_from_secret_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            secret_file = Path(temporary_directory) / "database-admin-write-url"
            secret_file.write_text(
                "postgresql://vesta_admin:secret@database.example/vesta"
                "?sslmode=verify-full\n",
                encoding="utf-8",
            )
            settings = Settings(
                _env_file=None,
                VESTA_ENV="production",
                ADMIN_DATABASE_URL_FILE=secret_file,
            )

            database_url = settings.get_admin_database_url()

        self.assertEqual(
            "postgresql://vesta_admin:secret@database.example/vesta"
            "?sslmode=verify-full",
            database_url,
        )

    def test_rejects_unencrypted_production_admin_database_url(self) -> None:
        settings = Settings(
            _env_file=None,
            VESTA_ENV="production",
            ADMIN_DATABASE_URL="postgresql://vesta_admin:secret@database.example/vesta",
        )

        with self.assertRaisesRegex(RuntimeError, "ADMIN_DATABASE_URL"):
            settings.get_admin_database_url()

    def test_reads_openai_api_key_from_secret_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            secret_file = Path(temporary_directory) / "openai-api-key"
            secret_file.write_text("test-key\n", encoding="utf-8")
            settings = Settings(
                _env_file=None,
                OPENAI_API_KEY="inline-key-must-not-win",
                OPENAI_API_KEY_FILE=secret_file,
            )

            api_key = settings.get_openai_api_key()

        self.assertEqual("test-key", api_key)

    def test_empty_openai_secret_file_disables_live_gateway(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            secret_file = Path(temporary_directory) / "openai-api-key"
            secret_file.write_text("", encoding="utf-8")
            settings = Settings(
                _env_file=None,
                OPENAI_API_KEY_FILE=secret_file,
            )

            self.assertIsNone(settings.get_openai_api_key())


class PostgresOfferMappingTest(unittest.TestCase):
    def test_maps_database_row_to_domain_offer(self) -> None:
        verified_at = datetime(2026, 7, 25, tzinfo=UTC)
        expires_at = datetime(2027, 1, 1, tzinfo=UTC)

        offer = _postgres_row_to_offer(
            {
                "id": "9c995262-bffd-4c94-8d1e-dc260dd94bea",
                "slug": "testangebot",
                "name": "Testangebot",
                "organization_name": "Testorganisation",
                "summary": "Nur für den Test.",
                "needs": ["sleep_tonight"],
                "languages": ["DE", "fr"],
                "access_rules": {
                    "accepts_dogs": True,
                    "identity_document_required": False,
                },
                "contact": {
                    "note": "Vorher anrufen.",
                    "address": "Muristrasse 6, 3006 Bern",
                },
                "latitude": 46.944359,
                "longitude": 7.459041,
                "availability": "confirmed",
                "source_label": "Testquelle",
                "source_url": "https://example.org/source",
                "verified_by": "test-team",
                "verified_at": verified_at,
                "expires_at": expires_at,
                "published": True,
                "is_demo": False,
                "updated_at": verified_at,
            }
        )

        self.assertEqual("testangebot", offer.slug)
        self.assertEqual("Testorganisation", offer.organization_name)
        self.assertEqual(verified_at, offer.updated_at)
        self.assertEqual((Need.SLEEP_TONIGHT,), offer.needs)
        self.assertEqual(("de", "fr"), offer.languages)
        self.assertEqual(Availability.CONFIRMED, offer.availability)
        self.assertTrue(offer.access.accepts_dogs)
        self.assertEqual("Vorher anrufen.", offer.contact_note)
        self.assertEqual("Muristrasse 6, 3006 Bern", offer.address)
        assert offer.location is not None
        self.assertEqual("Muristrasse 6, 3006 Bern", offer.location.address)
        self.assertAlmostEqual(46.944359, offer.location.latitude)
        self.assertEqual(expires_at, offer.source.expires_at)

    def test_preserves_postal_address_without_coordinates(self) -> None:
        verified_at = datetime(2026, 7, 25, tzinfo=UTC)

        offer = _postgres_row_to_offer(
            {
                "id": "b63864bb-17ec-4286-bf9f-649f890e7ced",
                "slug": "pluto-notschlafstelle-bern",
                "name": "Notschlafstelle für junge Menschen in Bern",
                "organization_name": "Pluto",
                "summary": "Niederschwellige Notschlafstelle.",
                "needs": ["sleep_tonight"],
                "languages": ["de"],
                "access_rules": {"minimum_age": 14, "maximum_age": 23},
                "contact": {
                    "note": "Vorher Kontakt aufnehmen.",
                    "address": "Studerstrasse 44, 3004 Bern",
                },
                "latitude": None,
                "longitude": None,
                "availability": "call_to_confirm",
                "source_label": "Pluto",
                "source_url": "https://www.pluto-bern.ch/",
                "verified_by": "admin",
                "verified_at": verified_at,
                "expires_at": datetime(2027, 1, 1, tzinfo=UTC),
                "published": True,
                "is_demo": False,
                "updated_at": verified_at,
            }
        )

        self.assertEqual("Studerstrasse 44, 3004 Bern", offer.address)
        self.assertIsNone(offer.location)


if __name__ == "__main__":
    unittest.main()
