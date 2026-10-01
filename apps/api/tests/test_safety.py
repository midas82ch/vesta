import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vesta_api.services.safety import (  # noqa: E402
    detect_safety_signal,
    no_match_resources,
    normalized_locale,
)


class SafetyDetectorTest(unittest.TestCase):
    def test_detects_explicit_violence_in_all_supported_languages(self) -> None:
        examples = {
            "de": "Ich werde bedroht",
            "fr": "Mon mari est violent",
            "en": "My partner is violent",
            "es": "Mi marido es violento",
            "pt": "O meu marido é violento",
            "ary": "راجلي كيهددني",
        }
        for locale, free_text in examples.items():
            with self.subTest(locale=locale):
                signal = detect_safety_signal(free_text, locale)
                self.assertIsNotNone(signal)

    def test_common_negations_do_not_trigger(self) -> None:
        examples = {
            "de": "Mein Mann ist nicht gewalttätig",
            "fr": "Mon mari n'est pas violent",
            "en": "My partner is not violent",
            "es": "Mi marido no es violento",
            "pt": "O meu marido não é violento",
            "ary": "راجلي ماشي عنيف",
        }
        for locale, free_text in examples.items():
            with self.subTest(locale=locale):
                self.assertIsNone(detect_safety_signal(free_text, locale))

    def test_detects_direct_danger_language_in_all_supported_languages(self) -> None:
        examples = {
            "de": "Ich bin in akuter Gefahr",
            "fr": "Je suis en danger",
            "en": "I am in immediate danger",
            "es": "Estoy en peligro",
            "pt": "Estou em perigo",
            "ary": "أنا فخطر",
        }
        for locale, free_text in examples.items():
            with self.subTest(locale=locale):
                self.assertIsNotNone(detect_safety_signal(free_text, locale))

    def test_negated_phrase_does_not_hide_a_separate_threat(self) -> None:
        signal = detect_safety_signal(
            "Mein Mann ist nicht gewalttätig, aber jemand bedroht mich.", "de"
        )

        self.assertIsNotNone(signal)

    def test_standard_arabic_locale_is_routed_to_darija_rules(self) -> None:
        self.assertEqual("ary", normalized_locale("ar-MA"))

    def test_contextual_no_match_numbers_are_kept_separate(self) -> None:
        youth = no_match_resources("de", youth=True, emotional_crisis=False)
        crisis = no_match_resources("de", youth=False, emotional_crisis=True)

        self.assertEqual(("147",), tuple(item["phone"] for item in youth))
        self.assertEqual(("143",), tuple(item["phone"] for item in crisis))
        self.assertNotIn("142", {item["phone"] for item in (*youth, *crisis)})
        self.assertNotIn("144", {item["phone"] for item in (*youth, *crisis)})


if __name__ == "__main__":
    unittest.main()
