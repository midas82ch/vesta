from datetime import UTC, datetime, timedelta
from threading import Lock

_lock = Lock()
_last_timestamp: datetime | None = None


def monotonic_audit_time() -> datetime:
    """Return a UTC timestamp that is strictly increasing in this process."""

    global _last_timestamp
    with _lock:
        current = datetime.now(UTC)
        if _last_timestamp is not None and current <= _last_timestamp:
            current = _last_timestamp + timedelta(microseconds=1)
        _last_timestamp = current
        return current
