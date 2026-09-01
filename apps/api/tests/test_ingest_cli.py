import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vesta_api.cli.ingest_offers import main  # noqa: E402


class IngestOffersCliTest(unittest.TestCase):
    @patch("vesta_api.cli.ingest_offers.ingest_catalog")
    @patch("vesta_api.cli.ingest_offers.create_database_engine")
    @patch("vesta_api.cli.ingest_offers.load_catalog")
    @patch("vesta_api.cli.ingest_offers.settings")
    def test_disabled_automatic_import_records_a_skipped_run(
        self,
        settings: Mock,
        load_catalog: Mock,
        create_engine: Mock,
        ingest_catalog: Mock,
    ) -> None:
        settings.get_database_url.return_value = (
            "postgresql://example.invalid/vesta?sslmode=require"
        )
        load_catalog.return_value = Mock()
        connection = Mock()
        first_result = Mock()
        first_result.scalar_one.return_value = False
        connection.execute.side_effect = [first_result, Mock()]
        engine = MagicMock()
        create_engine.return_value = engine
        engine.begin.return_value.__enter__.return_value = connection

        main()

        ingest_catalog.assert_not_called()
        self.assertEqual(2, connection.execute.call_count)
        skipped_statement = str(connection.execute.call_args_list[1].args[0])
        self.assertIn("skipped_disabled", skipped_statement)
        engine.dispose.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
