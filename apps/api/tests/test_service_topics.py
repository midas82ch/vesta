import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vesta_api.services.service_topics import detect_service_topics  # noqa: E402


class ServiceTopicDetectionTest(unittest.TestCase):
    def test_detects_topics_in_all_supported_languages(self) -> None:
        cases = (
            ("de", "Ich brauche Hilfe mit meinen Schulden.", "finances"),
            ("fr", "Je cherche de l’aide pour une dépendance.", "addiction"),
            ("en", "I am homeless and need advice.", "housing"),
            ("es", "Necesito una ducha.", "hygiene"),
            ("pt", "Preciso de ajuda médica.", "medical"),
            ("ary", "محتاج محامي يعاوني", "legal"),
        )

        for locale, text, expected in cases:
            with self.subTest(locale=locale):
                self.assertIn(expected, detect_service_topics(text, locale))

    def test_does_not_confuse_german_search_with_addiction(self) -> None:
        self.assertNotIn(
            "addiction",
            detect_service_topics("Ich suche eine allgemeine Beratung.", "de"),
        )


if __name__ == "__main__":
    unittest.main()
