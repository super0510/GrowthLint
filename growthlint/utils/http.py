"""HTTP utilities for GrowthLint."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from growthlint.config import DEFAULT_TIMEOUT, DEFAULT_USER_AGENT, MAX_RETRIES


class SSRFError(ValueError):
    """Raised when a URL resolves to a private/internal IP address."""


def validate_url(url: str) -> None:
    """Validate that a URL does not point to a private/internal IP address.

    Prevents SSRF attacks by blocking requests to loopback, private,
    link-local, and reserved IP ranges.
    """
    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        raise SSRFError(f"Invalid URL (no hostname): {url}")

    try:
        resolved = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        raise SSRFError(f"Cannot resolve hostname: {hostname}")

    for _, _, _, _, sockaddr in resolved:
        ip = ipaddress.ip_address(sockaddr[0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise SSRFError(
                f"URL resolves to internal/private IP ({ip}): {url}"
            )


def create_session() -> requests.Session:
    """Create a requests session with retry logic and proper headers."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })

    retry_strategy = Retry(
        total=MAX_RETRIES,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


def fetch_url(url: str, session: requests.Session | None = None) -> requests.Response:
    """Fetch a URL with proper error handling and SSRF protection."""
    validate_url(url)

    if session is None:
        session = create_session()

    response = session.get(url, timeout=DEFAULT_TIMEOUT, allow_redirects=True)
    response.raise_for_status()
    return response
