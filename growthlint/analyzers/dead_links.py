"""Dead link and redirect chain detection."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

import requests
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

from growthlint.models import PageData
from growthlint.utils.http import SSRFError, create_session, validate_url


@dataclass
class LinkCheckResult:
    """Result of checking a single link."""

    url: str
    source_page: str = ""
    status_code: int = 0
    final_url: str = ""
    redirect_chain: list[str] = field(default_factory=list)
    error: str = ""

    @property
    def is_broken(self) -> bool:
        return self.status_code >= 400 or bool(self.error)

    @property
    def is_redirect(self) -> bool:
        return 300 <= self.status_code < 400 or len(self.redirect_chain) > 1

    @property
    def has_long_chain(self) -> bool:
        return len(self.redirect_chain) >= 3

    @property
    def status_label(self) -> str:
        if self.error:
            return f"Error: {self.error}"
        if self.status_code == 0:
            return "Timeout"
        return str(self.status_code)


def check_links(
    pages: list[PageData],
    workers: int = 10,
    show_progress: bool = True,
) -> list[LinkCheckResult]:
    """Check all links across multiple pages for broken links and redirect chains."""
    # Collect unique URLs to check
    url_sources: dict[str, str] = {}  # url -> source page
    for page in pages:
        for link in page.links:
            href = link.href
            if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
                continue
            if href not in url_sources:
                url_sources[href] = page.url or page.file_path

    if not url_sources:
        return []

    session = create_session()
    urls_to_check = list(url_sources.items())

    if show_progress:
        return _check_with_progress(urls_to_check, session, workers)
    else:
        return _check_urls(urls_to_check, session, workers)


def check_page_links(
    page_data: PageData,
    workers: int = 10,
    show_progress: bool = True,
) -> list[LinkCheckResult]:
    """Check all links on a single page."""
    return check_links([page_data], workers=workers, show_progress=show_progress)


def _check_with_progress(
    urls: list[tuple[str, str]],
    session: requests.Session,
    workers: int,
) -> list[LinkCheckResult]:
    """Check URLs with progress bar."""
    results: list[LinkCheckResult] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]Checking links...[/bold cyan]"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total} links"),
    ) as progress:
        task = progress.add_task("Checking", total=len(urls))

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(_check_single, url, source, session): url
                for url, source in urls
            }
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                progress.advance(task)

    return sorted(results, key=lambda r: (not r.is_broken, r.status_code))


def _check_urls(
    urls: list[tuple[str, str]],
    session: requests.Session,
    workers: int,
) -> list[LinkCheckResult]:
    """Check URLs without progress display."""
    results: list[LinkCheckResult] = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(_check_single, url, source, session): url
            for url, source in urls
        }
        for future in as_completed(futures):
            results.append(future.result())

    return sorted(results, key=lambda r: (not r.is_broken, r.status_code))


def _check_single(url: str, source_page: str, session: requests.Session) -> LinkCheckResult:
    """Check a single URL, following redirects and recording the chain."""
    result = LinkCheckResult(url=url, source_page=source_page)

    try:
        validate_url(url)
        resp = session.head(url, timeout=10, allow_redirects=True)

        # If HEAD fails, try GET (some servers don't support HEAD)
        if resp.status_code >= 400:
            resp = session.get(url, timeout=10, allow_redirects=True, stream=True)

        result.status_code = resp.status_code
        result.final_url = str(resp.url)

        # Record redirect chain
        if resp.history:
            result.redirect_chain = [str(r.url) for r in resp.history] + [str(resp.url)]

    except requests.exceptions.Timeout:
        result.error = "Timeout"
    except requests.exceptions.ConnectionError:
        result.error = "Connection failed"
    except requests.exceptions.TooManyRedirects:
        result.error = "Too many redirects"
    except SSRFError:
        result.error = "Blocked: internal/private IP"
    except Exception as e:
        result.error = type(e).__name__

    return result


def format_link_report(results: list[LinkCheckResult]) -> str:
    """Format link check results as markdown."""
    lines: list[str] = []
    lines.append("# Dead Link Report")
    lines.append("")

    broken = [r for r in results if r.is_broken]
    redirects = [r for r in results if r.has_long_chain and not r.is_broken]
    ok = [r for r in results if not r.is_broken and not r.has_long_chain]

    lines.append(f"**Total links checked:** {len(results)}")
    lines.append(f"**Broken:** {len(broken)}")
    lines.append(f"**Long redirect chains (3+):** {len(redirects)}")
    lines.append(f"**OK:** {len(ok)}")
    lines.append("")

    if broken:
        lines.append("## Broken Links")
        lines.append("")
        lines.append("| URL | Status | Source Page |")
        lines.append("|-----|--------|------------|")
        for r in broken:
            lines.append(f"| {r.url} | {r.status_label} | {r.source_page} |")
        lines.append("")

    if redirects:
        lines.append("## Long Redirect Chains (3+ hops)")
        lines.append("")
        for r in redirects:
            lines.append(f"**{r.url}** ({len(r.redirect_chain)} hops)")
            for i, hop in enumerate(r.redirect_chain):
                arrow = "  -> " if i > 0 else "  "
                lines.append(f"{arrow}{hop}")
            lines.append("")

    return "\n".join(lines)
