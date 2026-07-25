import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vesta_api.repositories.dialogue_catalog import (  # noqa: E402
    JsonDialogueCatalogRepository,
)

CATALOG_PATH = (
    Path(__file__).resolve().parents[3] / "data" / "seed" / "dialogue_catalog.json"
)

EXPECTED_ATTRIBUTE_KEYS = {
    "person.has_dog",
    "person.has_identity_document",
    "person.gender",
    "person.age",
}


class DialogueCatalogTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = JsonDialogueCatalogRepository(CATALOG_PATH)

    def test_lists_three_needs_in_sort_order(self) -> None:
        needs = self.repository.list_needs()

        self.assertEqual(
            ["sleep_tonight", "basic_needs", "counselling"],
            [need.key for need in needs],
        )
        for need in needs:
            self.assertIn("de", need.localizations)
            self.assertIn("fr", need.localizations)
            self.assertIn("en", need.localizations)
            self.assertIn("ar", need.localizations)

    def test_lists_all_attributes_backing_todays_hardcoded_access_rules(self) -> None:
        attributes = self.repository.list_attributes()

        self.assertEqual(EXPECTED_ATTRIBUTE_KEYS, {a.key for a in attributes})

    def test_gender_attribute_has_localized_options(self) -> None:
        attribute = self.repository.get_attribute("person.gender")

        assert attribute is not None
        self.assertEqual(attribute.value_type, "enum")
        self.assertEqual({"finta", "other"}, {o.value for o in attribute.options})
        finta = next(o for o in attribute.options if o.value == "finta")
        self.assertEqual("Frau / FINTA", finta.localizations["de"]["label"])

    def test_unknown_attribute_returns_none(self) -> None:
        self.assertIsNone(self.repository.get_attribute("person.does_not_exist"))

    def test_questions_are_sorted_by_priority_and_reference_known_attributes(
        self,
    ) -> None:
        questions = self.repository.list_questions()
        attribute_keys = {a.key for a in self.repository.list_attributes()}

        self.assertEqual(
            sorted(questions, key=lambda q: q.priority), list(questions)
        )
        for question in questions:
            self.assertIn(question.attribute_key, attribute_keys)
            self.assertIn("de", question.localizations)
            canonical = question.localizations["de"]["canonical_text"]
            self.assertTrue(canonical)

    def test_healthcheck_reads_the_file(self) -> None:
        self.repository.healthcheck()


if __name__ == "__main__":
    unittest.main()
