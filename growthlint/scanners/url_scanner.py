"""URL scanner for fetching and analyzing live web pages."""

from __future__ import annotations

import requests

from growthlint.models import PageData
from growthlint.scanners.dom_parser import parse_html
from growthlint.utils.http import create_session, fetch_url


def scan_url(url: str, session: requests.Session | None = None) -> PageData:
    """Fetch a URL and parse it into PageData."""
    if session is None:
        session = create_session()

    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    response = fetch_url(url, session)
    page_data = parse_html(response.text, url=str(response.url))
    return page_data
