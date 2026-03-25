import ipaddress
import socket
from urllib.parse import urlsplit, urlunsplit


ALLOWED_WEB_SCHEMES = frozenset({"http", "https"})
ALLOWED_LOGO_HOSTS = frozenset({"raw.githubusercontent.com"})


class UnsafeUrlError(ValueError):
    """Raised when a URL is invalid or targets a non-public network location."""


def validate_public_url(
    url: str,
    *,
    allowed_schemes: frozenset[str] = ALLOWED_WEB_SCHEMES,
    allowed_hosts: frozenset[str] | None = None,
) -> str:
    raw_url = (url or "").strip()
    if not raw_url:
        raise UnsafeUrlError("Please enter a valid URL.")

    parsed = urlsplit(raw_url)
    scheme = parsed.scheme.lower()
    if scheme not in allowed_schemes:
        allowed_list = ", ".join(sorted(allowed_schemes))
        raise UnsafeUrlError(f"URL must use one of the allowed schemes: {allowed_list}.")

    if not parsed.netloc or not parsed.hostname:
        raise UnsafeUrlError("URL must include a valid host.")

    if parsed.username or parsed.password:
        raise UnsafeUrlError("Credentials in URLs are not allowed.")

    try:
        port = parsed.port
    except ValueError as exc:
        raise UnsafeUrlError("URL contains an invalid port.") from exc

    hostname = parsed.hostname.rstrip(".").lower()
    try:
        hostname = hostname.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise UnsafeUrlError("URL host is invalid.") from exc

    if hostname == "localhost" or hostname.endswith(".local"):
        raise UnsafeUrlError("Local or internal hosts are not allowed.")

    if allowed_hosts is not None and hostname not in allowed_hosts:
        raise UnsafeUrlError("URL host is not in the allowed list.")

    _ensure_public_host(hostname)

    normalized_netloc = _build_netloc(hostname, port)
    normalized_path = parsed.path or "/"
    return urlunsplit((scheme, normalized_netloc, normalized_path, parsed.query, ""))


def validate_logo_url(url: str) -> str:
    return validate_public_url(
        url,
        allowed_schemes=frozenset({"https"}),
        allowed_hosts=ALLOWED_LOGO_HOSTS,
    )


def _build_netloc(hostname: str, port: int | None) -> str:
    host = f"[{hostname}]" if ":" in hostname else hostname
    return f"{host}:{port}" if port else host


def _ensure_public_host(hostname: str) -> None:
    for address in _resolve_ip_addresses(hostname):
        if not address.is_global:
            raise UnsafeUrlError(
                "Private, loopback, link-local, or reserved IP addresses are not allowed."
            )


def _resolve_ip_addresses(
    hostname: str,
) -> set[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    try:
        return {ipaddress.ip_address(hostname)}
    except ValueError:
        pass

    try:
        info = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise UnsafeUrlError(f"Unable to resolve host: {hostname}") from exc

    addresses = {ipaddress.ip_address(result[4][0]) for result in info}
    if not addresses:
        raise UnsafeUrlError(f"Unable to resolve host: {hostname}")

    return addresses
