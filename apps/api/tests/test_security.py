import sys
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vesta_api.security import (  # noqa: E402
    AdminLoginAttemptStore,
    AdminSessionStore,
    verify_password,
    verify_password_or_dummy,
)

NOW = datetime(2026, 7, 27, 12, 0, tzinfo=UTC)


class PasswordVerificationTest(unittest.TestCase):
    def test_unknown_user_still_runs_scrypt_and_never_authenticates(self) -> None:
        with patch("vesta_api.security.hashlib.scrypt", return_value=b"x" * 32) as scrypt:
            valid = verify_password_or_dummy("secret", None)

        self.assertFalse(valid)
        scrypt.assert_called_once()

    def test_malformed_hash_is_rejected(self) -> None:
        self.assertFalse(verify_password("secret", "not-a-valid-hash"))
        self.assertFalse(verify_password("secret", "scrypt$not-hex$also-not-hex"))


class AdminLoginAttemptStoreTest(unittest.TestCase):
    def test_rate_limit_expires_and_can_be_cleared(self) -> None:
        store = AdminLoginAttemptStore(max_failures=2, window=timedelta(minutes=1))
        store.record_failure(" Vesta-Admin ", NOW)
        store.record_failure("vesta-admin", NOW + timedelta(seconds=1))

        self.assertEqual(59, store.retry_after_seconds("VESTA-ADMIN", NOW + timedelta(seconds=1)))

        store.clear("vesta-admin")
        self.assertIsNone(store.retry_after_seconds("vesta-admin", NOW + timedelta(seconds=1)))

        store.record_failure("vesta-admin", NOW)
        store.record_failure("vesta-admin", NOW + timedelta(seconds=1))
        self.assertIsNone(store.retry_after_seconds("vesta-admin", NOW + timedelta(seconds=61)))


class AdminSessionStoreTest(unittest.TestCase):
    def test_expired_session_is_rejected_and_removed(self) -> None:
        store = AdminSessionStore(ttl=timedelta(minutes=1))
        token = store.create("vesta-admin", NOW)

        self.assertIsNotNone(store.get(token, NOW + timedelta(seconds=59)))
        self.assertIsNone(store.get(token, NOW + timedelta(minutes=1)))
        self.assertIsNone(store.get(token, NOW + timedelta(minutes=2)))


if __name__ == "__main__":
    unittest.main()
