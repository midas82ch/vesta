import sys
import unittest
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vesta_api.domain.admin_models import AdminUser  # noqa: E402
from vesta_api.ingestion.offer_import_ai import (  # noqa: E402
    ExtractedOffer,
    LocalizedOfferDraft,
)
from vesta_api.ingestion.offer_import_worker import OfferImportProcessor  # noqa: E402
from vesta_api.ingestion.safe_url import (  # noqa: E402
    MAX_PAGE_BYTES,
    SafeFetchedPage,
    SafeUrlError,
    SafeUrlFetcher,
    _HttpResult,
    normalize_offer_url,
)
from vesta_api.repositories.offer_import_jobs import (  # noqa: E402
    _CLAIM_NEXT,
    _INSERT_QUEUE_CHANGE,
    InMemoryOfferImportJobRepository,
)


class SafeUrlTest(unittest.TestCase):
    def test_queue_audit_casts_url_before_building_json(self) -> None:
        self.assertIn("CAST(:source_url AS text)", str(_INSERT_QUEUE_CHANGE))

    def test_worker_locks_only_the_import_job_row(self) -> None:
        statement = str(_CLAIM_NEXT)
        self.assertIn("FOR UPDATE SKIP LOCKED", statement)
        self.assertIn("FOR UPDATE OF j", statement)

    def test_normalizes_https_and_removes_fragment(self) -> None:
        self.assertEqual(
            "https://example.org/offer?q=1",
            normalize_offer_url(" HTTPS://Example.ORG/offer?q=1#private "),
        )

    def test_preserves_a_meaningful_trailing_slash(self) -> None:
        self.assertEqual(
            "https://example.org/offer/",
            normalize_offer_url("https://example.org/offer/"),
        )

    def test_rejects_unsafe_url_shapes(self) -> None:
        unsafe = (
            "http://example.org/",
            "https://user:secret@example.org/",
            "https://example.org:8443/",
            "https://127.0.0.1/",
            "https://10.0.0.1/",
            "https://169.254.169.254/latest/meta-data/",
            "https://[::1]/",
            "https://[fc00::1]/",
        )
        for value in unsafe:
            with self.subTest(url=value), self.assertRaises(SafeUrlError):
                normalize_offer_url(value)

    def test_rejects_private_dns_answers_before_connecting(self) -> None:
        fetcher = SafeUrlFetcher(resolver=lambda _host: ("10.0.0.8",))

        with self.assertRaisesRegex(SafeUrlError, "blocked_address"):
            fetcher._request("https://example.org/", max_bytes=100)

    def test_accepts_a_public_ipv6_literal(self) -> None:
        self.assertEqual(
            "https://[2606:2800:220:1:248:1893:25c8:1946]/",
            normalize_offer_url("https://[2606:2800:220:1:248:1893:25c8:1946]/"),
        )

    def test_redirect_is_revalidated_and_limited(self) -> None:
        class FakeFetcher(SafeUrlFetcher):
            def __init__(self) -> None:
                super().__init__()
                self.requested: list[str] = []

            def _request(self, url: str, *, max_bytes: int) -> _HttpResult:
                self.requested.append(url)
                if url.endswith("/robots.txt"):
                    return _HttpResult(404, {}, b"")
                if "first.example" in url:
                    return _HttpResult(302, {"location": "https://second.example/page"}, b"")
                return _HttpResult(
                    200,
                    {"content-type": "text/html; charset=utf-8"},
                    b"<p>Offer</p>",
                )

        fetcher = FakeFetcher()
        result = fetcher.fetch("https://first.example/page")

        self.assertEqual("https://second.example/page", result.final_url)
        self.assertIn("https://second.example/robots.txt", fetcher.requested)
        self.assertEqual("Offer", result.text)

    def test_robots_txt_can_block_the_import(self) -> None:
        class RobotsBlockedFetcher(SafeUrlFetcher):
            def _request(self, url: str, *, max_bytes: int) -> _HttpResult:
                del max_bytes
                if url.endswith("/robots.txt"):
                    return _HttpResult(
                        200,
                        {"content-type": "text/plain"},
                        b"User-agent: *\nDisallow: /private",
                    )
                return _HttpResult(200, {"content-type": "text/html"}, b"<p>Offer</p>")

        with self.assertRaisesRegex(SafeUrlError, "robots_disallowed"):
            RobotsBlockedFetcher().fetch("https://example.org/private")

    def test_rejects_non_html_content(self) -> None:
        class PdfFetcher(SafeUrlFetcher):
            def _request(self, url: str, *, max_bytes: int) -> _HttpResult:
                del max_bytes
                if url.endswith("/robots.txt"):
                    return _HttpResult(404, {}, b"")
                return _HttpResult(200, {"content-type": "application/pdf"}, b"PDF")

        with self.assertRaisesRegex(SafeUrlError, "unsupported_content_type"):
            PdfFetcher().fetch("https://example.org/offer.pdf")

    def test_stops_after_three_redirects(self) -> None:
        class LoopingFetcher(SafeUrlFetcher):
            def _request(self, url: str, *, max_bytes: int) -> _HttpResult:
                del max_bytes
                if url.endswith("/robots.txt"):
                    return _HttpResult(404, {}, b"")
                return _HttpResult(302, {"location": "/next"}, b"")

        with self.assertRaisesRegex(SafeUrlError, "too_many_redirects"):
            LoopingFetcher().fetch("https://example.org/start")

    def test_enforces_the_two_megabyte_limit_while_reading(self) -> None:
        class FakeResponse:
            status = 200

            @staticmethod
            def read(size: int) -> bytes:
                return b"x" * size

            @staticmethod
            def getheaders() -> list[tuple[str, str]]:
                return [("content-type", "text/html")]

        class FakeConnection:
            def request(self, *_args: object, **_kwargs: object) -> None:
                return None

            @staticmethod
            def getresponse() -> FakeResponse:
                return FakeResponse()

            def close(self) -> None:
                return None

        fetcher = SafeUrlFetcher(resolver=lambda _host: ("93.184.216.34",))
        with patch(
            "vesta_api.ingestion.safe_url._PinnedHttpsConnection",
            return_value=FakeConnection(),
        ), self.assertRaisesRegex(SafeUrlError, "response_too_large"):
            fetcher._request("https://example.org/", max_bytes=MAX_PAGE_BYTES)


EXTRACTED = ExtractedOffer(
    source_language="de",
    organization_name="Hilfswerk",
    name="Beratung",
    summary="Vertrauliche Beratung.",
    languages=("de",),
    needs=("counselling",),
    availability="call_to_confirm",
    contact_note="Telefon auf der Quelle.",
    address=None,
    accepts_dogs=None,
    identity_document_required=None,
    accepted_genders=(),
    minimum_age=None,
    maximum_age=None,
    evidence=({"field": "name", "excerpt": "Beratung"},),
)


class ExtractedOfferTest(unittest.TestCase):
    def test_normalizes_all_gender_marker_to_no_restriction(self) -> None:
        extracted = replace(
            EXTRACTED,
            accepted_genders=(" ALL ", "finta"),
        )

        self.assertEqual((), extracted.accepted_genders)


class FakeFetcher:
    def fetch(self, _url: str) -> SafeFetchedPage:
        return SafeFetchedPage(
            final_url="https://example.org/offer",
            status_code=200,
            text="Beratung",
            content_sha256="abc123",
        )


class FailingFetcher:
    def __init__(self, code: str) -> None:
        self.code = code

    def fetch(self, _url: str) -> SafeFetchedPage:
        raise SafeUrlError(self.code)


class FakeAi:
    def extract(self, **_kwargs: object) -> ExtractedOffer:
        return EXTRACTED

    def translate(self, **_kwargs: object) -> tuple[LocalizedOfferDraft, ...]:
        return tuple(
            LocalizedOfferDraft(locale, "Beratung", "Beschreibung", "Kontakt")
            for locale in ("de", "fr", "en", "es", "pt", "ary")
        )


class FakeStore:
    def __init__(self, duplicates: tuple[str, ...] = ()) -> None:
        self.duplicates = duplicates
        self.saved = False

    def find_duplicates(self, **_kwargs: object) -> tuple[str, ...]:
        return self.duplicates

    def save_draft(self, **_kwargs: object) -> str:
        self.saved = True
        return "11111111-1111-1111-1111-111111111111"


class OfferImportProcessorTest(unittest.TestCase):
    def _jobs(self) -> InMemoryOfferImportJobRepository:
        jobs = InMemoryOfferImportJobRepository()
        admin = AdminUser("admin-id", "admin", "hash", True, datetime.now(UTC))
        jobs.create("https://example.org/offer", "https://example.org/offer", admin)
        return jobs

    def test_processes_source_into_reviewable_draft(self) -> None:
        jobs = self._jobs()
        store = FakeStore()
        processor = OfferImportProcessor(
            jobs=jobs,
            fetcher=FakeFetcher(),  # type: ignore[arg-type]
            ai=FakeAi(),  # type: ignore[arg-type]
            store=store,  # type: ignore[arg-type]
        )

        self.assertTrue(processor.process_next())

        job = jobs.list(limit=1, offset=0)[0]
        self.assertEqual("ready_for_review", job.status)
        self.assertTrue(store.saved)
        self.assertEqual("de", job.source_language)

    def test_reports_duplicate_without_overwriting_offer(self) -> None:
        jobs = self._jobs()
        store = FakeStore(("existing-offer",))
        processor = OfferImportProcessor(
            jobs=jobs,
            fetcher=FakeFetcher(),  # type: ignore[arg-type]
            ai=FakeAi(),  # type: ignore[arg-type]
            store=store,  # type: ignore[arg-type]
        )

        processor.process_next()

        job = jobs.list(limit=1, offset=0)[0]
        self.assertEqual(("existing-offer",), job.duplicate_offer_ids)
        self.assertFalse(store.saved)

    def test_retries_transient_errors_at_most_three_times(self) -> None:
        jobs = self._jobs()
        processor = OfferImportProcessor(
            jobs=jobs,
            fetcher=FailingFetcher("network_error"),  # type: ignore[arg-type]
            ai=FakeAi(),  # type: ignore[arg-type]
            store=FakeStore(),  # type: ignore[arg-type]
        )

        for expected_attempt in (1, 2):
            self.assertTrue(processor.process_next())
            job = jobs.list(limit=1, offset=0)[0]
            self.assertEqual("queued", job.status)
            self.assertEqual(expected_attempt, job.attempts)

        self.assertTrue(processor.process_next())
        failed = jobs.list(limit=1, offset=0)[0]
        self.assertEqual("failed", failed.status)
        self.assertEqual(3, failed.attempts)

    def test_does_not_retry_a_permanent_fetch_error(self) -> None:
        jobs = self._jobs()
        processor = OfferImportProcessor(
            jobs=jobs,
            fetcher=FailingFetcher("robots_disallowed"),  # type: ignore[arg-type]
            ai=FakeAi(),  # type: ignore[arg-type]
            store=FakeStore(),  # type: ignore[arg-type]
        )

        processor.process_next()

        failed = jobs.list(limit=1, offset=0)[0]
        self.assertEqual("failed", failed.status)
        self.assertEqual(1, failed.attempts)

    def test_an_expired_lease_is_reclaimed_after_worker_restart(self) -> None:
        jobs = self._jobs()
        first_claim = jobs.claim_next(lease=timedelta(minutes=5))
        assert first_claim is not None
        jobs._replace(
            first_claim,
            lease_expires_at=datetime.now(UTC) - timedelta(seconds=1),
        )

        reclaimed = jobs.claim_next(lease=timedelta(minutes=5))

        assert reclaimed is not None
        self.assertEqual(2, reclaimed.attempts)
        self.assertEqual("fetching", reclaimed.status)


if __name__ == "__main__":
    unittest.main()
