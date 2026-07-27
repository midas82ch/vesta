import sys
import unittest
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vesta_api.domain.ingestion_models import IngestionRun  # noqa: E402
from vesta_api.repositories.ingestion_runs import (  # noqa: E402
    InMemoryIngestionRunRepository,
)


def _run(**overrides: object) -> IngestionRun:
    defaults: dict[str, object] = {
        "id": "run-1",
        "offer_slug": "test-offer",
        "source_url": "https://example.org/offer",
        "status": "imported",
        "http_status": 200,
        "content_sha256": "abc123",
        "missing_evidence": (),
        "error": None,
        "checked_at": datetime(2026, 7, 27, 5, 33, tzinfo=UTC),
    }
    defaults.update(overrides)
    return IngestionRun(**defaults)  # type: ignore[arg-type]


class IngestionRunRepositoryTest(unittest.TestCase):
    def test_list_runs_newest_first(self) -> None:
        repo = InMemoryIngestionRunRepository()
        repo.add(_run(id="older", checked_at=datetime(2026, 7, 26, 5, 33, tzinfo=UTC)))
        repo.add(_run(id="newer", checked_at=datetime(2026, 7, 27, 5, 33, tzinfo=UTC)))

        runs = repo.list_runs(limit=10, offset=0)

        self.assertEqual(("newer", "older"), tuple(run.id for run in runs))

    def test_list_runs_filters_by_status(self) -> None:
        repo = InMemoryIngestionRunRepository()
        repo.add(_run(id="ok", status="imported"))
        repo.add(_run(id="missing", status="evidence_missing"))
        repo.add(_run(id="failed", status="fetch_failed", error="boom"))

        runs = repo.list_runs(limit=10, offset=0, status="fetch_failed")

        self.assertEqual(1, len(runs))
        self.assertEqual("failed", runs[0].id)
        self.assertEqual("boom", runs[0].error)

    def test_list_runs_respects_limit_and_offset(self) -> None:
        repo = InMemoryIngestionRunRepository()
        for index in range(5):
            repo.add(
                _run(
                    id=f"run-{index}",
                    checked_at=datetime(2026, 7, 20 + index, 5, 33, tzinfo=UTC),
                )
            )

        page = repo.list_runs(limit=2, offset=1)

        self.assertEqual(("run-3", "run-2"), tuple(run.id for run in page))

    def test_missing_evidence_round_trips_as_a_tuple(self) -> None:
        repo = InMemoryIngestionRunRepository()
        repo.add(_run(missing_evidence=("Öffnungszeiten", "Telefonnummer")))

        run = repo.list_runs(limit=1, offset=0)[0]

        self.assertEqual(("Öffnungszeiten", "Telefonnummer"), run.missing_evidence)


if __name__ == "__main__":
    unittest.main()
