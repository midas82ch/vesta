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


if __name__ == "__main__":
    unittest.main()
