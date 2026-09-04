import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vesta_api.api.localization import disclaimer_for  # noqa: E402


class ApiLocalizationTest(unittest.TestCase):
    def test_each_supported_locale_has_its_own_disclaimer(self) -> None:
        locales = ("de", "fr", "en", "es", "pt", "ary")
        disclaimers = {locale: disclaimer_for(locale) for locale in locales}

        self.assertEqual(6, len(set(disclaimers.values())))
        self.assertIn("reserviert", disclaimers["de"])
        self.assertIn("réserve", disclaimers["fr"])
        self.assertIn("reserve", disclaimers["en"])
        self.assertIn("reserva", disclaimers["es"])
        self.assertIn("reserva", disclaimers["pt"])
        self.assertIn("ما كتحجز", disclaimers["ary"])

    def test_legacy_arabic_and_unknown_locale_fallbacks(self) -> None:
        self.assertEqual(disclaimer_for("ary"), disclaimer_for("ar"))
        self.assertEqual(disclaimer_for("ary"), disclaimer_for("ar-MA"))
        self.assertEqual(disclaimer_for("de"), disclaimer_for("xx"))


if __name__ == "__main__":
    unittest.main()
