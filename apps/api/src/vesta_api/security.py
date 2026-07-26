import hashlib
import hmac
import math
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta

SESSION_COOKIE_NAME = "vesta_admin_session"
SESSION_TTL = timedelta(hours=8)
LOGIN_MAX_FAILURES = 5
LOGIN_FAILURE_WINDOW = timedelta(minutes=15)

_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SALT_BYTES = 16
_KEY_LENGTH = 32
_DUMMY_PASSWORD_HASH = (
    "scrypt$00112233445566778899aabbccddeeff$"
    "38a7e627259438770f8f4edd4d8ad0a53e069aae4636902fac0a0a764234a24f"
)


def hash_password(password: str) -> str:
    salt = os.urandom(_SALT_BYTES)
    derived = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_KEY_LENGTH,
    )
    return f"scrypt${salt.hex()}${derived.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        scheme, salt_hex, derived_hex = stored_hash.split("$")
        if scheme != "scrypt":
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(derived_hex)
        candidate = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=_SCRYPT_N,
            r=_SCRYPT_R,
            p=_SCRYPT_P,
            dklen=len(expected),
        )
    except ValueError:
        return False
    return hmac.compare_digest(candidate, expected)


def verify_password_or_dummy(password: str, stored_hash: str | None) -> bool:
    """Always perform one scrypt verification, including unknown usernames."""

    valid = verify_password(password, stored_hash or _DUMMY_PASSWORD_HASH)
    return stored_hash is not None and valid


@dataclass(frozen=True)
class AdminSession:
    username: str
    expires_at: datetime


class AdminSessionStore:
    """In-memory, short-lived admin login session store.

    Same shape as ``DialogueSessionStore``: the prototype runs on a single
    instance, so there is no need for a shared/persistent session backend.
    """

    def __init__(self, ttl: timedelta = SESSION_TTL) -> None:
        self._sessions: dict[str, AdminSession] = {}
        self._ttl = ttl

    def create(self, username: str, now: datetime) -> str:
        token = secrets.token_urlsafe(32)
        self._sessions[token] = AdminSession(username=username, expires_at=now + self._ttl)
        return token

    def get(self, token: str, now: datetime) -> AdminSession | None:
        session = self._sessions.get(token)
        if session is None:
            return None
        if session.expires_at <= now:
            del self._sessions[token]
            return None
        return session

    def delete(self, token: str) -> None:
        self._sessions.pop(token, None)


class AdminLoginAttemptStore:
    """In-memory throttling for the single-instance prototype."""

    def __init__(
        self,
        *,
        max_failures: int = LOGIN_MAX_FAILURES,
        window: timedelta = LOGIN_FAILURE_WINDOW,
    ) -> None:
        self._failures: dict[str, list[datetime]] = {}
        self._max_failures = max_failures
        self._window = window

    @staticmethod
    def _key(username: str) -> str:
        return username.strip().casefold()

    def _active_failures(self, username: str, now: datetime) -> list[datetime]:
        key = self._key(username)
        cutoff = now - self._window
        active = [attempt for attempt in self._failures.get(key, []) if attempt > cutoff]
        if active:
            self._failures[key] = active
        else:
            self._failures.pop(key, None)
        return active

    def retry_after_seconds(self, username: str, now: datetime) -> int | None:
        active = self._active_failures(username, now)
        if len(active) < self._max_failures:
            return None
        retry_at = active[0] + self._window
        return max(1, math.ceil((retry_at - now).total_seconds()))

    def record_failure(self, username: str, now: datetime) -> None:
        key = self._key(username)
        active = self._active_failures(username, now)
        active.append(now)
        self._failures[key] = active

    def clear(self, username: str) -> None:
        self._failures.pop(self._key(username), None)
