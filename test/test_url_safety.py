from ipaddress import ip_address

import pytest

import src.url_safety as url_safety


def test_validate_public_url_normalizes_safe_urls(monkeypatch):
    monkeypatch.setattr(
        url_safety,
        "_resolve_ip_addresses",
        lambda hostname: {ip_address("93.184.216.34")},
    )

    assert (
        url_safety.validate_public_url("HTTPS://Example.COM")
        == "https://example.com/"
    )


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/admin",
        "http://169.254.169.254/latest/meta-data/",
    ],
)
def test_validate_public_url_rejects_non_public_ip_ranges(url):
    with pytest.raises(
        url_safety.UnsafeUrlError,
        match="Private, loopback, link-local, or reserved IP addresses are not allowed.",
    ):
        url_safety.validate_public_url(url)


def test_validate_logo_url_rejects_non_allowlisted_hosts():
    with pytest.raises(
        url_safety.UnsafeUrlError, match="URL host is not in the allowed list."
    ):
        url_safety.validate_logo_url("https://example.com/logo.png")
