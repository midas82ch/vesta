import hashlib
import http.client
import ipaddress
import socket
import ssl
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import PurePosixPath
from typing import Protocol
from urllib.parse import SplitResult, quote, urljoin, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

USER_AGENT = "VestaOfferImporter/1.0 (+https://www.vesta-app.ch/impressum)"
MAX_PAGE_BYTES = 2 * 1024 * 1024
MAX_REDIRECTS = 3
TIMEOUT_SECONDS = 15


class SafeUrlError(ValueError):
    def __init__(self, code: str, detail: str | None = None) -> None:
        super().__init__(detail or code)
        self.code = code


@dataclass(frozen=True)
class SafeFetchedPage:
    final_url: str
    status_code: int
    text: str
    content_sha256: str


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._ignored = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "svg"}:
            self._ignored += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self._ignored:
            self._ignored -= 1

    def handle_data(self, data: str) -> None:
        if not self._ignored and data.strip():
            self.parts.append(data.strip())


def html_to_plain_text(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    return "\n".join(parser.parts)


def normalize_offer_url(value: str) -> str:
    raw = value.strip()
    try:
        parsed = urlsplit(raw)
        port = parsed.port
    except ValueError as error:
        raise SafeUrlError("invalid_url") from error
    if parsed.scheme.lower() != "https":
        raise SafeUrlError("https_required")
    if not parsed.hostname or parsed.username is not None or parsed.password is not None:
        raise SafeUrlError("invalid_url")
    if port not in (None, 443):
        raise SafeUrlError("https_port_443_required")
    try:
        hostname = parsed.hostname.encode("idna").decode("ascii").lower()
    except UnicodeError as error:
        raise SafeUrlError("invalid_hostname") from error
    if hostname == "localhost" or hostname.endswith(".localhost"):
        raise SafeUrlError("blocked_address")
    try:
        literal = ipaddress.ip_address(hostname.strip("[]"))
    except ValueError:
        literal = None
    if literal is not None and not literal.is_global:
        raise SafeUrlError("blocked_address")
    source_path = parsed.path or "/"
    normalized_path = quote(
        str(PurePosixPath(source_path)), safe="/%:@-._~!$&'()*+,;="
    )
    if source_path.endswith("/") and normalized_path != "/":
        normalized_path = f"{normalized_path}/"
    normalized = SplitResult(
        scheme="https",
        netloc=f"[{hostname}]" if ":" in hostname else hostname,
        path=normalized_path,
        query=parsed.query,
        fragment="",
    )
    return urlunsplit(normalized)


class AddressResolver(Protocol):
    def __call__(self, hostname: str) -> tuple[str, ...]: ...


def resolve_public_addresses(hostname: str) -> tuple[str, ...]:
    try:
        records = socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)
    except socket.gaierror as error:
        raise SafeUrlError("dns_resolution_failed") from error
    addresses = tuple(dict.fromkeys(record[4][0] for record in records))
    if not addresses:
        raise SafeUrlError("dns_resolution_failed")
    for address in addresses:
        try:
            parsed = ipaddress.ip_address(address)
        except ValueError as error:
            raise SafeUrlError("invalid_dns_address") from error
        if not parsed.is_global:
            raise SafeUrlError("blocked_address")
    return addresses


class _PinnedHttpsConnection(http.client.HTTPSConnection):
    def __init__(self, hostname: str, address: str, *, timeout: int) -> None:
        super().__init__(hostname, port=443, timeout=timeout, context=ssl.create_default_context())
        self._address = address

    def connect(self) -> None:
        raw_socket = socket.create_connection((self._address, 443), self.timeout)
        self.sock = self._context.wrap_socket(raw_socket, server_hostname=self.host)


@dataclass(frozen=True)
class _HttpResult:
    status: int
    headers: dict[str, str]
    body: bytes


class SafeUrlFetcher:
    def __init__(self, *, resolver: AddressResolver = resolve_public_addresses) -> None:
        self._resolver = resolver

    def _request(self, url: str, *, max_bytes: int) -> _HttpResult:
        normalized = normalize_offer_url(url)
        parsed = urlsplit(normalized)
        assert parsed.hostname is not None
        addresses = self._resolver(parsed.hostname)
        if not addresses:
            raise SafeUrlError("dns_resolution_failed")
        for address in addresses:
            parsed_address = ipaddress.ip_address(address)
            if not parsed_address.is_global:
                raise SafeUrlError("blocked_address")
        path = parsed.path or "/"
        if parsed.query:
            path = f"{path}?{parsed.query}"
        connection = _PinnedHttpsConnection(
            parsed.hostname,
            addresses[0],
            timeout=TIMEOUT_SECONDS,
        )
        try:
            connection.request(
                "GET",
                path,
                headers={
                    "Accept": "text/html,application/xhtml+xml,text/plain",
                    "Host": parsed.netloc,
                    "User-Agent": USER_AGENT,
                    "Connection": "close",
                },
            )
            response = connection.getresponse()
            body = response.read(max_bytes + 1)
            if len(body) > max_bytes:
                raise SafeUrlError("response_too_large")
            return _HttpResult(
                status=response.status,
                headers={key.lower(): value for key, value in response.getheaders()},
                body=body,
            )
        except (OSError, TimeoutError, http.client.HTTPException) as error:
            raise SafeUrlError("network_error", str(error)) from error
        finally:
            connection.close()

    def _robots_allows(self, url: str) -> bool:
        parsed = urlsplit(url)
        robots_url = urlunsplit(("https", parsed.netloc, "/robots.txt", "", ""))
        result = self._request(robots_url, max_bytes=256 * 1024)
        if result.status in {401, 403}:
            return False
        if result.status >= 400:
            return True
        parser = RobotFileParser()
        parser.set_url(robots_url)
        parser.parse(result.body.decode("utf-8", errors="replace").splitlines())
        return parser.can_fetch(USER_AGENT, url)

    def fetch(self, source_url: str) -> SafeFetchedPage:
        current = normalize_offer_url(source_url)
        if not self._robots_allows(current):
            raise SafeUrlError("robots_disallowed")
        for redirect_count in range(MAX_REDIRECTS + 1):
            result = self._request(current, max_bytes=MAX_PAGE_BYTES)
            if result.status in {301, 302, 303, 307, 308}:
                if redirect_count == MAX_REDIRECTS:
                    raise SafeUrlError("too_many_redirects")
                location = result.headers.get("location")
                if not location:
                    raise SafeUrlError("redirect_without_location")
                current = normalize_offer_url(urljoin(current, location))
                if not self._robots_allows(current):
                    raise SafeUrlError("robots_disallowed")
                continue
            if result.status >= 400:
                raise SafeUrlError("http_error", f"HTTP {result.status}")
            content_type = result.headers.get("content-type", "").split(";", 1)[0].lower()
            if content_type not in {"text/html", "application/xhtml+xml"}:
                raise SafeUrlError("unsupported_content_type")
            charset = "utf-8"
            content_type_header = result.headers.get("content-type", "")
            if "charset=" in content_type_header.lower():
                charset = content_type_header.lower().split("charset=", 1)[1].split(";", 1)[0]
            html = result.body.decode(charset, errors="replace")
            return SafeFetchedPage(
                final_url=current,
                status_code=result.status,
                text=html_to_plain_text(html),
                content_sha256=hashlib.sha256(result.body).hexdigest(),
            )
        raise SafeUrlError("too_many_redirects")
