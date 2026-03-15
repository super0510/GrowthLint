"""Sitemap scanner for crawling entire sites."""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse

import defusedxml.ElementTree as SafeET
import requests
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

from growthlint.models import PageData
from growthlint.scanners.dom_parser import parse_html
from growthlint.utils.http import SSRFError, create_session, fetch_url, validate_url

# XML namespace for sitemaps
SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def crawl_site(
    url: str,
    max_pages: int = 50,
    workers: int = 5,
    show_progress: bool = True,
) -> list[PageData]:
    """Crawl a site via its sitemap and return page data for each page.

    Falls back to homepage-only scan if no sitemap is found.
    """
    base_url = _normalize_base(url)
    session = create_session()

    # Try to find and parse sitemap
    urls = _discover_urls(base_url, session)
    if not urls:
        urls = [base_url]

    urls = urls[:max_pages]

    if show_progress:
        return _crawl_with_progress(urls, session, workers)
    else:
        return _crawl_urls(urls, session, workers)


def _normalize_base(url: str) -> str:
    """Normalize URL to base form."""
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def _discover_urls(base_url: str, session: requests.Session) -> list[str]:
    """Discover URLs from sitemap.xml, robots.txt, or fallback to internal links."""
    urls: list[str] = []

    # Try sitemap.xml directly
    sitemap_url = f"{base_url}/sitemap.xml"
    sitemap_urls = _fetch_sitemap(sitemap_url, session)
    if sitemap_urls:
        return sitemap_urls

    # Try robots.txt for sitemap references
    robots_url = f"{base_url}/robots.txt"
    try:
        resp = session.get(robots_url, timeout=10)
        if resp.status_code == 200:
            for line in resp.text.splitlines():
                if line.lower().startswith("sitemap:"):
                    sm_url = line.split(":", 1)[1].strip()
                    try:
                        validate_url(sm_url)
                    except SSRFError:
                        continue
                    found = _fetch_sitemap(sm_url, session)
                    urls.extend(found)
    except Exception:
        pass

    if urls:
        return list(dict.fromkeys(urls))  # dedupe preserving order

    # Fallback: crawl homepage for internal links
    try:
        resp = fetch_url(base_url, session)
        page = parse_html(resp.text, url=base_url)
        urls = [base_url] + page.internal_links[:49]
    except Exception:
        urls = [base_url]

    return list(dict.fromkeys(urls))


def _fetch_sitemap(url: str, session: requests.Session) -> list[str]:
    """Fetch and parse a sitemap XML, handling nested sitemaps.

    Uses defusedxml to prevent XXE and entity expansion attacks.
    Validates nested URLs against SSRF before following them.
    """
    try:
        validate_url(url)
    except SSRFError:
        return []

    try:
        resp = session.get(url, timeout=10)
        if resp.status_code != 200:
            return []
    except Exception:
        return []

    try:
        root = SafeET.fromstring(resp.content)
    except Exception:
        return []

    urls: list[str] = []

    # Check for sitemap index (nested sitemaps)
    for sitemap in root.findall("sm:sitemap", SITEMAP_NS):
        loc = sitemap.find("sm:loc", SITEMAP_NS)
        if loc is not None and loc.text:
            nested_url = loc.text.strip()
            try:
                validate_url(nested_url)
            except SSRFError:
                continue
            nested = _fetch_sitemap(nested_url, session)
            urls.extend(nested)

    # Regular URL entries
    for url_elem in root.findall("sm:url", SITEMAP_NS):
        loc = url_elem.find("sm:loc", SITEMAP_NS)
        if loc is not None and loc.text:
            urls.append(loc.text.strip())

    return urls


def _crawl_with_progress(
    urls: list[str],
    session: requests.Session,
    workers: int,
) -> list[PageData]:
    """Crawl URLs with a Rich progress bar."""
    pages: list[PageData] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]Crawling...[/bold cyan]"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total} pages"),
    ) as progress:
        task = progress.add_task("Crawling", total=len(urls))

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(_fetch_and_parse, url, session): url
                for url in urls
            }
            for future in as_completed(futures):
                page = future.result()
                if page:
                    pages.append(page)
                progress.advance(task)

    return pages


def _crawl_urls(
    urls: list[str],
    session: requests.Session,
    workers: int,
) -> list[PageData]:
    """Crawl URLs without progress display."""
    pages: list[PageData] = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(_fetch_and_parse, url, session): url
            for url in urls
        }
        for future in as_completed(futures):
            page = future.result()
            if page:
                pages.append(page)

    return pages


def _fetch_and_parse(url: str, session: requests.Session) -> PageData | None:
    """Fetch a single URL and parse it."""
    try:
        validate_url(url)
        resp = session.get(url, timeout=15, allow_redirects=True)
        resp.raise_for_status()

        content_type = resp.headers.get("content-type", "")
        if "text/html" not in content_type:
            return None

        return parse_html(resp.text, url=str(resp.url))
    except Exception:
        return None
