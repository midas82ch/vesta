import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vesta_api.domain.audit_models import NewAiAuditEntry  # noqa: E402
from vesta_api.repositories.ai_audit_log import InMemoryAiAuditLogRepository  # noqa: E402


def _entry(**overrides: object) -> NewAiAuditEntry:
    defaults: dict[str, object] = {
        "port": "explain",
        "provider": "openai",
        "model": "gpt-5.4-mini",
        "outcome": "ai",
        "request_text": "request",
        "response_text": "response",
        "session_id": "sess-1",
    }
    defaults.update(overrides)
    return NewAiAuditEntry(**defaults)  # type: ignore[arg-type]


class AiAuditLogRepositoryTest(unittest.TestCase):
    def test_record_and_list_entries_newest_first(self) -> None:
        repo = InMemoryAiAuditLogRepository()
        repo.record(_entry(session_id="sess-1"))
        time.sleep(0.02)
        repo.record(_entry(session_id="sess-2"))

        entries = repo.list_entries(limit=10, offset=0)

        self.assertEqual(2, len(entries))
        self.assertEqual("sess-2", entries[0].session_id)
        self.assertEqual("sess-1", entries[1].session_id)

    def test_list_entries_filters_by_port_outcome_and_session(self) -> None:
        repo = InMemoryAiAuditLogRepository()
        repo.record(_entry(port="interpret", outcome="ai", session_id="a"))
        repo.record(_entry(port="explain", outcome="fallback_error", session_id="b"))

        self.assertEqual(1, len(repo.list_entries(limit=10, offset=0, port="interpret")))
        self.assertEqual(
            1, len(repo.list_entries(limit=10, offset=0, outcome="fallback_error"))
        )
        self.assertEqual(1, len(repo.list_entries(limit=10, offset=0, session_id="b")))
        self.assertEqual(0, len(repo.list_entries(limit=10, offset=0, session_id="does-not-exist")))

    def test_get_entry_returns_full_detail(self) -> None:
        repo = InMemoryAiAuditLogRepository()
        repo.record(
            _entry(
                request_text="the prompt",
                response_text="the answer",
                violations=("unsupported_reason",),
                error_detail=None,
            )
        )
        entry_id = repo.list_entries(limit=10, offset=0)[0].id

        detail = repo.get_entry(entry_id)

        assert detail is not None
        self.assertEqual("the prompt", detail.request_text)
        self.assertEqual("the answer", detail.response_text)
        self.assertEqual(("unsupported_reason",), detail.violations)

    def test_get_entry_returns_none_for_unknown_id(self) -> None:
        repo = InMemoryAiAuditLogRepository()

        self.assertIsNone(repo.get_entry("does-not-exist"))

    def test_entries_have_no_automatic_expiry(self) -> None:
        repo = InMemoryAiAuditLogRepository()
        repo.record(_entry())
        entry_id = repo.list_entries(limit=10, offset=0)[0].id

        detail = repo.get_entry(entry_id)

        assert detail is not None
        self.assertFalse(hasattr(detail, "expires_at"))


if __name__ == "__main__":
    unittest.main()
