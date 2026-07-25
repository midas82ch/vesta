import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vesta_api.ingestion.web_offers import (  # noqa: E402
    evaluate_evidence,
    html_to_text,
    load_catalog,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


class OfferCatalogTest(unittest.TestCase):
    def test_catalog_contains_only_explicit_test_offers(self) -> None:
        catalog = load_catalog(
            REPOSITORY_ROOT / "data" / "sources" / "bern_offers.json"
        )

        self.assertEqual(7, len(catalog.offers))
        self.assertEqual(7, len({offer.slug for offer in catalog.offers}))
        self.assertTrue(
            all(offer.name.startswith("Testangebot:") for offer in catalog.offers)
        )
        self.assertTrue(
            all(str(offer.source.url).startswith("https://") for offer in catalog.offers)
        )

    def test_visible_text_excludes_scripts_and_styles(self) -> None:
        text = html_to_text(
            """
            <html>
              <style>.hidden { display: none; }</style>
              <body><h1>Passantenheim Bern</h1><p>60 Notschlafbetten</p></body>
              <script>window.secret = "not evidence";</script>
            </html>
            """
        )

        self.assertIn("Passantenheim Bern", text)
        self.assertIn("60 Notschlafbetten", text)
        self.assertNotIn("window.secret", text)

    def test_evidence_check_normalizes_case_and_whitespace(self) -> None:
        result = evaluate_evidence(
            "CONTACT  Anlaufstelle\nHodlerstrasse 22",
            ["contact anlaufstelle", "Hodlerstrasse 22"],
        )

        self.assertTrue(result.accepted)
        self.assertEqual((), result.missing)

    def test_evidence_check_reports_missing_phrases(self) -> None:
        result = evaluate_evidence(
            "CONTACT Anlaufstelle",
            ["CONTACT Anlaufstelle", "Hodlerstrasse 22"],
        )

        self.assertFalse(result.accepted)
        self.assertEqual(("Hodlerstrasse 22",), result.missing)


if __name__ == "__main__":
    unittest.main()
