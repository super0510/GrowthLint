"""DOM parser for extracting structured page data from HTML."""

from __future__ import annotations

import json
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Comment

from growthlint.config import ANALYTICS_PATTERNS, CTA_PATTERNS, EVENT_TRACKING_PATTERNS
from growthlint.models import FormData, MetaData, PageData, PageElement


def parse_html(html: str, url: str = "") -> PageData:
    """Parse HTML string into structured PageData."""
    soup = BeautifulSoup(html, "lxml")

    return PageData(
        url=url,
        html_length=len(html),
        meta=_extract_meta(soup),
        headings=_extract_headings(soup),
        links=_extract_links(soup),
        internal_links=_extract_internal_links(soup, url),
        external_links=_extract_external_links(soup, url),
        images=_extract_images(soup),
        forms=_extract_forms(soup),
        ctas=_extract_ctas(soup),
        scripts=_extract_all_scripts(soup),
        script_sources=_extract_script_sources(soup),
        inline_scripts=_extract_inline_scripts(soup),
        schema_markup=_extract_schema(soup),
        text_content=_extract_text(soup),
    )


def _extract_meta(soup: BeautifulSoup) -> MetaData:
    """Extract page metadata."""
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    def meta_content(name: str = "", property: str = "") -> str:
        tag = None
        if name:
            tag = soup.find("meta", attrs={"name": name})
        if not tag and property:
            tag = soup.find("meta", attrs={"property": property})
        return tag.get("content", "").strip() if tag else ""

    canonical_tag = soup.find("link", attrs={"rel": "canonical"})
    canonical = canonical_tag.get("href", "").strip() if canonical_tag else ""

    favicon_tag = soup.find("link", attrs={"rel": re.compile(r"icon", re.I)})
    favicon = favicon_tag.get("href", "").strip() if favicon_tag else ""

    return MetaData(
        title=title,
        description=meta_content(name="description"),
        canonical=canonical,
        viewport=meta_content(name="viewport"),
        robots=meta_content(name="robots"),
        og_title=meta_content(property="og:title"),
        og_description=meta_content(property="og:description"),
        og_image=meta_content(property="og:image"),
        og_type=meta_content(property="og:type"),
        favicon=favicon,
    )


def _extract_headings(soup: BeautifulSoup) -> dict[str, list[str]]:
    """Extract all headings by level."""
    headings: dict[str, list[str]] = {}
    for level in range(1, 7):
        tag = f"h{level}"
        found = soup.find_all(tag)
        if found:
            headings[tag] = [h.get_text(strip=True) for h in found]
    return headings


def _extract_links(soup: BeautifulSoup) -> list[PageElement]:
    """Extract all links."""
    links = []
    for a in soup.find_all("a", href=True):
        links.append(PageElement(
            tag="a",
            text=a.get_text(strip=True)[:200],
            href=a["href"],
            attributes={k: str(v) for k, v in a.attrs.items() if k != "href"},
        ))
    return links


def _classify_link(href: str, base_url: str) -> str | None:
    """Return 'internal' or 'external' for a link."""
    if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
        return None
    try:
        full = urljoin(base_url, href) if base_url else href
        if not base_url:
            return None
        base_domain = urlparse(base_url).netloc
        link_domain = urlparse(full).netloc
        if not link_domain:
            return "internal"
        return "internal" if link_domain == base_domain else "external"
    except Exception:
        return None


def _extract_internal_links(soup: BeautifulSoup, base_url: str) -> list[str]:
    """Extract internal links."""
    result = []
    for a in soup.find_all("a", href=True):
        if _classify_link(a["href"], base_url) == "internal":
            full = urljoin(base_url, a["href"]) if base_url else a["href"]
            result.append(full)
    return list(set(result))


def _extract_external_links(soup: BeautifulSoup, base_url: str) -> list[str]:
    """Extract external links."""
    result = []
    for a in soup.find_all("a", href=True):
        if _classify_link(a["href"], base_url) == "external":
            full = urljoin(base_url, a["href"]) if base_url else a["href"]
            result.append(full)
    return list(set(result))


def _extract_images(soup: BeautifulSoup) -> list[PageElement]:
    """Extract all images."""
    images = []
    for img in soup.find_all("img"):
        images.append(PageElement(
            tag="img",
            text=img.get("alt", ""),
            href=img.get("src", ""),
            attributes={
                k: str(v) for k, v in img.attrs.items()
                if k not in ("src", "alt")
            },
        ))
    return images


def _extract_forms(soup: BeautifulSoup) -> list[FormData]:
    """Extract form data."""
    forms = []
    for form in soup.find_all("form"):
        inputs = form.find_all(["input", "select", "textarea"])
        field_names = []
        field_types = []
        has_hidden = False

        for inp in inputs:
            inp_type = inp.get("type", "text").lower()
            name = inp.get("name", "") or inp.get("id", "") or inp_type
            if inp_type == "hidden":
                has_hidden = True
            elif inp_type not in ("submit", "button"):
                field_names.append(name)
                field_types.append(inp_type)

        forms.append(FormData(
            action=form.get("action", ""),
            method=form.get("method", "get").upper(),
            fields=field_names,
            field_count=len(field_names),
            has_hidden_fields=has_hidden,
            field_types=field_types,
        ))
    return forms


def _extract_ctas(soup: BeautifulSoup) -> list[PageElement]:
    """Extract call-to-action elements."""
    ctas = []
    combined_pattern = re.compile("|".join(CTA_PATTERNS), re.IGNORECASE)

    for el in soup.find_all(["a", "button"]):
        text = el.get_text(strip=True)
        if combined_pattern.search(text):
            ctas.append(PageElement(
                tag=el.name,
                text=text[:200],
                href=el.get("href", ""),
                attributes={k: str(v) for k, v in el.attrs.items() if k != "href"},
            ))

    return ctas


def _extract_all_scripts(soup: BeautifulSoup) -> list[str]:
    """Extract all script content (src + inline)."""
    scripts = []
    for s in soup.find_all("script"):
        src = s.get("src", "")
        if src:
            scripts.append(src)
        elif s.string:
            scripts.append(s.string[:500])
    return scripts


def _extract_script_sources(soup: BeautifulSoup) -> list[str]:
    """Extract external script source URLs."""
    return [s["src"] for s in soup.find_all("script", src=True)]


def _extract_inline_scripts(soup: BeautifulSoup) -> list[str]:
    """Extract inline script content."""
    return [
        s.string[:1000]
        for s in soup.find_all("script")
        if not s.get("src") and s.string
    ]


def _extract_schema(soup: BeautifulSoup) -> list[dict]:
    """Extract JSON-LD structured data."""
    schemas = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        if script.string:
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    schemas.extend(data)
                else:
                    schemas.append(data)
            except (json.JSONDecodeError, ValueError):
                pass
    return schemas


def _extract_text(soup: BeautifulSoup) -> str:
    """Extract visible text content."""
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
        comment.extract()
    text = soup.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text)
    return text[:5000]


def detect_analytics_tools(page_data: PageData) -> list[str]:
    """Detect which analytics tools are present on the page."""
    all_scripts = " ".join(page_data.scripts + page_data.inline_scripts)
    detected = []
    for tool, patterns in ANALYTICS_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, all_scripts, re.IGNORECASE):
                detected.append(tool)
                break
    return detected


def has_event_tracking(page_data: PageData) -> bool:
    """Check if the page has any event tracking."""
    all_scripts = " ".join(page_data.inline_scripts)
    for pattern in EVENT_TRACKING_PATTERNS:
        if re.search(pattern, all_scripts, re.IGNORECASE):
            return True
    return False
