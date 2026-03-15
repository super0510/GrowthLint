"""Platform detection for repos and URLs."""

from __future__ import annotations

import json
import re
from pathlib import Path

from growthlint.models import PageData, Platform


def detect_platform_from_repo(path: Path) -> Platform:
    """Detect the platform/framework from a local repository."""
    # Check package.json for JS frameworks
    pkg_json = path / "package.json"
    if pkg_json.exists():
        try:
            pkg = json.loads(pkg_json.read_text())
            deps = {
                **pkg.get("dependencies", {}),
                **pkg.get("devDependencies", {}),
            }

            if "next" in deps:
                return Platform.nextjs
            if "astro" in deps:
                return Platform.astro
            if "react" in deps or "react-dom" in deps:
                return Platform.react
        except (json.JSONDecodeError, KeyError):
            pass

    # WordPress signals
    if (path / "wp-content").is_dir() or (path / "wp-config.php").exists():
        return Platform.wordpress
    if (path / "style.css").exists():
        style = (path / "style.css").read_text(errors="ignore")[:500]
        if "Theme Name:" in style:
            return Platform.wordpress

    # Shopify signals
    if (path / "templates").is_dir() and any(
        (path / "templates").glob("*.liquid")
    ):
        return Platform.shopify
    if (path / "layout" / "theme.liquid").exists():
        return Platform.shopify

    # Webflow export signals
    has_webflow_css = any(path.glob("css/webflow*.css"))
    has_webflow_js = any(path.glob("js/webflow*.js"))
    if has_webflow_css or has_webflow_js:
        return Platform.webflow

    # Static site (has HTML files but no framework)
    html_files = list(path.glob("*.html")) + list(path.glob("**/*.html"))
    if html_files:
        return Platform.static

    return Platform.unknown


def detect_platform_from_url(page_data: PageData) -> Platform:
    """Detect the platform from a live URL's page data."""
    all_scripts = " ".join(page_data.scripts + page_data.inline_scripts)
    text = page_data.text_content

    # Next.js signals
    if any(s for s in page_data.script_sources if "/_next/" in s):
        return Platform.nextjs
    if re.search(r"__NEXT_DATA__", all_scripts):
        return Platform.nextjs

    # React signals (check after Next.js since Next uses React)
    if re.search(r"__REACT_DEVTOOLS|react-root|reactroot|_reactRootContainer", all_scripts):
        return Platform.react
    if any(s for s in page_data.script_sources if "react" in s.lower()):
        return Platform.react

    # Astro signals
    if any(s for s in page_data.script_sources if "astro" in s.lower()):
        return Platform.astro

    # WordPress signals
    if any(s for s in page_data.script_sources if "/wp-content/" in s or "/wp-includes/" in s):
        return Platform.wordpress

    # Shopify signals
    if any(s for s in page_data.script_sources if "cdn.shopify.com" in s):
        return Platform.shopify
    if re.search(r"Shopify\.theme", all_scripts):
        return Platform.shopify

    # Webflow signals
    if any(s for s in page_data.script_sources if "webflow" in s.lower()):
        return Platform.webflow
    if re.search(r"class=\"w-", page_data.text_content[:2000]):
        return Platform.webflow

    return Platform.unknown


def get_scannable_extensions(platform: Platform) -> list[str]:
    """Get file extensions to scan for a given platform."""
    base = [".html", ".htm"]

    platform_extensions = {
        Platform.nextjs: [".jsx", ".tsx", ".js", ".ts"],
        Platform.react: [".jsx", ".tsx", ".js", ".ts"],
        Platform.astro: [".astro", ".jsx", ".tsx"],
        Platform.wordpress: [".php"],
        Platform.shopify: [".liquid"],
        Platform.webflow: [],
        Platform.static: [],
    }

    return base + platform_extensions.get(platform, [])
