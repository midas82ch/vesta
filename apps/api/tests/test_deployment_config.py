import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


class CaddyConfigurationTest(unittest.TestCase):
    def test_location_permission_is_allowed_for_vesta_itself(self) -> None:
        caddyfile = (REPOSITORY_ROOT / "infra" / "caddy" / "Caddyfile").read_text(
            encoding="utf-8"
        )

        self.assertIn("geolocation=(self)", caddyfile)
        self.assertNotIn("geolocation=()", caddyfile)


class ReleaseConfigurationTest(unittest.TestCase):
    def test_public_title_is_consistent_across_metadata_and_manifest(self) -> None:
        expected_title = '"Vesta - einfach Hilfe finden"'
        layout = (REPOSITORY_ROOT / "apps" / "web" / "app" / "layout.tsx").read_text(
            encoding="utf-8"
        )
        manifest = (
            REPOSITORY_ROOT / "apps" / "web" / "app" / "manifest.ts"
        ).read_text(encoding="utf-8")

        self.assertEqual(3, layout.count(expected_title))
        self.assertIn(f"name: {expected_title}", manifest)

    def test_api_migration_and_ingest_use_the_same_release_image(self) -> None:
        compose = (REPOSITORY_ROOT / "compose.prod.yaml").read_text(encoding="utf-8")

        self.assertEqual(3, compose.count("image: vesta-api:latest"))

    def test_public_locales_replace_standard_arabic_with_darija(self) -> None:
        i18n = (REPOSITORY_ROOT / "apps" / "web" / "lib" / "i18n.ts").read_text(
            encoding="utf-8"
        )

        self.assertIn(
            '["de", "fr", "en", "es", "pt", "ary"] as const',
            i18n,
        )
        self.assertIn('normalized === "ar"', i18n)
        self.assertIn('return "ary"', i18n)
        self.assertIn('locale === "ary" ? "rtl" : "ltr"', i18n)


if __name__ == "__main__":
    unittest.main()
