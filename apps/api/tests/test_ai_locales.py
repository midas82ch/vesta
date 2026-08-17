import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vesta_api.ai.locales import ai_locale_name  # noqa: E402


class AiLocaleNameTest(unittest.TestCase):
    def test_supported_new_locales_have_explicit_model_instructions(self) -> None:
        self.assertEqual("Español (es-ES)", ai_locale_name("es"))
        self.assertEqual("Português europeu (pt-PT)", ai_locale_name("pt"))
        self.assertIn("Moroccan Darija", ai_locale_name("ary"))

    def test_unknown_locale_is_preserved(self) -> None:
        self.assertEqual("xx", ai_locale_name("xx"))


if __name__ == "__main__":
    unittest.main()
