"""Tests for platform detection and repo scanning."""

from __future__ import annotations

from pathlib import Path

from growthlint.models import Platform
from growthlint.rules.loader import load_rules
from growthlint.scanners.platform_detector import (
    detect_platform_from_repo,
    detect_platform_from_url,
    get_scannable_extensions,
)
from growthlint.scanners.repo_scanner import scan_repo

FIXTURES = Path(__file__).parent / "fixtures"


class TestPlatformDetectionRepo:
    def test_detects_nextjs(self) -> None:
        platform = detect_platform_from_repo(FIXTURES / "nextjs_project")
        assert platform == Platform.nextjs

    def test_detects_wordpress(self) -> None:
        platform = detect_platform_from_repo(FIXTURES / "wordpress_project")
        assert platform == Platform.wordpress

    def test_detects_shopify(self) -> None:
        platform = detect_platform_from_repo(FIXTURES / "shopify_project")
        assert platform == Platform.shopify

    def test_static_fallback(self) -> None:
        platform = detect_platform_from_repo(FIXTURES / "sample_react_site")
        assert platform == Platform.static


class TestPlatformDetectionURL:
    def test_detects_nextjs_from_scripts(self) -> None:
        from growthlint.models import PageData
        page = PageData(
            script_sources=["/_next/static/chunks/main.js"],
            scripts=["/_next/static/chunks/main.js"],
        )
        assert detect_platform_from_url(page) == Platform.nextjs

    def test_detects_shopify_from_cdn(self) -> None:
        from growthlint.models import PageData
        page = PageData(
            script_sources=["https://cdn.shopify.com/s/files/1/shop.js"],
            scripts=["https://cdn.shopify.com/s/files/1/shop.js"],
        )
        assert detect_platform_from_url(page) == Platform.shopify

    def test_detects_wordpress_from_paths(self) -> None:
        from growthlint.models import PageData
        page = PageData(
            script_sources=["/wp-content/plugins/jetpack/js/main.js", "/wp-includes/js/jquery.js"],
            scripts=["/wp-content/plugins/jetpack/js/main.js"],
        )
        assert detect_platform_from_url(page) == Platform.wordpress

    def test_unknown_for_empty_page(self) -> None:
        from growthlint.models import PageData
        page = PageData()
        assert detect_platform_from_url(page) == Platform.unknown


class TestScannableExtensions:
    def test_nextjs_extensions(self) -> None:
        exts = get_scannable_extensions(Platform.nextjs)
        assert ".tsx" in exts
        assert ".jsx" in exts
        assert ".html" in exts

    def test_wordpress_extensions(self) -> None:
        exts = get_scannable_extensions(Platform.wordpress)
        assert ".php" in exts
        assert ".html" in exts

    def test_shopify_extensions(self) -> None:
        exts = get_scannable_extensions(Platform.shopify)
        assert ".liquid" in exts


class TestRepoScanner:
    def test_scans_nextjs_project(self) -> None:
        pages, platform = scan_repo(FIXTURES / "nextjs_project")
        assert platform == Platform.nextjs
        assert len(pages) >= 1
        # Should find the page.tsx file
        file_paths = [p.file_path for p in pages]
        assert any("page.tsx" in fp for fp in file_paths)

    def test_scans_wordpress_project(self) -> None:
        pages, platform = scan_repo(FIXTURES / "wordpress_project")
        assert platform == Platform.wordpress
        assert len(pages) >= 1

    def test_scans_shopify_project(self) -> None:
        pages, platform = scan_repo(FIXTURES / "shopify_project")
        assert platform == Platform.shopify
        assert len(pages) >= 1

    def test_scans_static_site(self) -> None:
        pages, platform = scan_repo(FIXTURES / "sample_react_site")
        assert platform == Platform.static
        assert len(pages) >= 1

    def test_platform_override(self) -> None:
        pages, platform = scan_repo(FIXTURES / "sample_react_site", platform=Platform.react)
        assert platform == Platform.react

    def test_nonexistent_dir_raises(self) -> None:
        import pytest
        with pytest.raises(FileNotFoundError):
            scan_repo("/nonexistent/path")


class TestPlatformSpecificRules:
    def test_shopify_rules_load(self) -> None:
        rules = load_rules(platform="shopify")
        shopify_ids = [r.id for r in rules if r.platforms and "shopify" in r.platforms]
        assert len(shopify_ids) >= 3
        assert "shopify-no-cart-tracking" in shopify_ids

    def test_wordpress_rules_load(self) -> None:
        rules = load_rules(platform="wordpress")
        wp_ids = [r.id for r in rules if r.platforms and "wordpress" in r.platforms]
        assert len(wp_ids) >= 3
        assert "wp-excessive-scripts" in wp_ids

    def test_webflow_rules_load(self) -> None:
        rules = load_rules(platform="webflow")
        wf_ids = [r.id for r in rules if r.platforms and "webflow" in r.platforms]
        assert len(wf_ids) >= 2

    def test_platform_rules_not_in_generic(self) -> None:
        """Platform-specific rules should not fire for unknown platform."""
        rules = load_rules(platform="unknown")
        platform_rules = [r for r in rules if r.platforms]
        assert len(platform_rules) == 0

    def test_base_rules_always_included(self) -> None:
        """Base rules (no platform restriction) should always load."""
        rules = load_rules(platform="shopify")
        base_rules = [r for r in rules if not r.platforms]
        assert len(base_rules) >= 15  # Our original 23+ base rules
