import sys
import unittest
from pathlib import Path
from unittest.mock import Mock
from uuid import NAMESPACE_URL, uuid4, uuid5

from pydantic import ValidationError  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vesta_api.ingestion.web_offers import (  # noqa: E402
    LEGACY_ID_NAMESPACE,
    CatalogLocation,
    _resolve_offer_id,
    evaluate_evidence,
    html_to_text,
    load_catalog,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


class OfferCatalogTest(unittest.TestCase):
    def test_catalog_contains_unique_verified_offers(self) -> None:
        catalog = load_catalog(
            REPOSITORY_ROOT / "data" / "sources" / "bern_offers.json"
        )

        self.assertEqual(7, len(catalog.offers))
        self.assertEqual(7, len({offer.slug for offer in catalog.offers}))
        self.assertFalse(
            any(offer.slug.startswith("test-") for offer in catalog.offers)
        )
        self.assertTrue(
            all(str(offer.source.url).startswith("https://") for offer in catalog.offers)
        )
        self.assertTrue(all(offer.location is not None for offer in catalog.offers))
        self.assertEqual(
            6,
            len(
                {
                    offer.location.address
                    for offer in catalog.offers
                    if offer.location is not None
                }
            ),
        )

    def test_existing_legacy_offer_id_is_reused_for_clean_slug(self) -> None:
        existing_id = uuid4()
        connection = Mock()
        connection.execute.return_value.scalar_one_or_none.return_value = existing_id

        offer_id = _resolve_offer_id(connection, "passantenheim-bern")

        self.assertEqual(existing_id, offer_id)
        parameters = connection.execute.call_args.args[1]
        self.assertEqual("passantenheim-bern", parameters["slug"])
        self.assertEqual("test-passantenheim-bern", parameters["legacy_slug"])

    def test_new_clean_slug_gets_a_stable_id_without_test_prefix(self) -> None:
        connection = Mock()
        connection.execute.return_value.scalar_one_or_none.return_value = None

        offer_id = _resolve_offer_id(connection, "new-offer-bern")

        self.assertEqual(
            uuid5(
                NAMESPACE_URL,
                f"{LEGACY_ID_NAMESPACE}/offers/new-offer-bern",
            ),
            offer_id,
        )

    def test_catalog_location_requires_a_complete_valid_point(self) -> None:
        with self.assertRaises(ValidationError):
            CatalogLocation.model_validate(
                {
                    "address": "Teststrasse 1, 3000 Bern",
                    "latitude": 46.95,
                }
            )

        with self.assertRaises(ValidationError):
            CatalogLocation.model_validate(
                {
                    "address": "Teststrasse 1, 3000 Bern",
                    "latitude": 91,
                    "longitude": 7.44,
                }
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
