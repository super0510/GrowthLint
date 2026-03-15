"""Tests for DOM parser and scanners."""

from __future__ import annotations

from growthlint.scanners.dom_parser import (
    detect_analytics_tools,
    has_event_tracking,
    parse_html,
)


class TestParseHTML:
    def test_extracts_title(self, sample_html: str) -> None:
        page = parse_html(sample_html, url="https://example.com")
        assert page.meta.title == "Acme SaaS - Project Management"

    def test_extracts_description(self, sample_html: str) -> None:
        page = parse_html(sample_html, url="https://example.com")
        assert page.meta.description == "Acme helps teams ship faster."

    def test_extracts_h1(self, sample_html: str) -> None:
        page = parse_html(sample_html, url="https://example.com")
        assert "h1" in page.headings
        assert "Ship Projects 2x Faster" in page.headings["h1"]

    def test_extracts_h2(self, sample_html: str) -> None:
        page = parse_html(sample_html, url="https://example.com")
        assert "h2" in page.headings
        assert len(page.headings["h2"]) == 2

    def test_extracts_images(self, sample_html: str) -> None:
        page = parse_html(sample_html, url="https://example.com")
        assert len(page.images) == 2
        # One image has alt, one doesn't
        alt_texts = [img.text for img in page.images]
        assert "" in alt_texts  # missing alt
        assert "Sprint board view" in alt_texts

    def test_extracts_forms(self, sample_html: str) -> None:
        page = parse_html(sample_html, url="https://example.com")
        assert len(page.forms) == 1
        form = page.forms[0]
        assert form.field_count == 7  # 7 visible fields (not hidden, not submit)
        assert form.has_hidden_fields is True

    def test_extracts_ctas(self, sample_html: str) -> None:
        page = parse_html(sample_html, url="https://example.com")
        cta_texts = [cta.text for cta in page.ctas]
        assert "Get Started Free" in cta_texts

    def test_extracts_internal_links(self, sample_html: str) -> None:
        page = parse_html(sample_html, url="https://example.com")
        assert any("/features" in link for link in page.internal_links)
        assert any("/pricing" in link for link in page.internal_links)

    def test_extracts_external_links(self, sample_html: str) -> None:
        page = parse_html(sample_html, url="https://example.com")
        assert any("blog.external.com" in link for link in page.external_links)

    def test_missing_viewport(self, sample_html: str) -> None:
        page = parse_html(sample_html, url="https://example.com")
        assert page.meta.viewport == ""

    def test_missing_canonical(self, sample_html: str) -> None:
        page = parse_html(sample_html, url="https://example.com")
        assert page.meta.canonical == ""

    def test_missing_og_tags(self, sample_html: str) -> None:
        page = parse_html(sample_html, url="https://example.com")
        assert page.meta.og_title == ""

    def test_text_content_extracted(self, sample_html: str) -> None:
        page = parse_html(sample_html, url="https://example.com")
        assert "Ship Projects 2x Faster" in page.text_content

    def test_html_length(self, sample_html: str) -> None:
        page = parse_html(sample_html, url="https://example.com")
        assert page.html_length > 0


class TestMinimalPage:
    def test_all_meta_present(self, minimal_html: str) -> None:
        page = parse_html(minimal_html, url="https://example.com")
        assert page.meta.title == "Minimal Page"
        assert page.meta.viewport != ""
        assert page.meta.canonical != ""
        assert page.meta.og_title != ""
        assert page.meta.favicon != ""

    def test_schema_markup_extracted(self, minimal_html: str) -> None:
        page = parse_html(minimal_html, url="https://example.com")
        assert len(page.schema_markup) == 1
        assert page.schema_markup[0]["@type"] == "Organization"

    def test_detects_analytics(self, minimal_html: str) -> None:
        page = parse_html(minimal_html, url="https://example.com")
        tools = detect_analytics_tools(page)
        assert "ga4" in tools

    def test_detects_event_tracking(self, minimal_html: str) -> None:
        page = parse_html(minimal_html, url="https://example.com")
        assert has_event_tracking(page) is True


class TestNoAnalytics:
    def test_no_analytics_detected(self, sample_html: str) -> None:
        page = parse_html(sample_html, url="https://example.com")
        tools = detect_analytics_tools(page)
        assert tools == []

    def test_no_event_tracking(self, sample_html: str) -> None:
        page = parse_html(sample_html, url="https://example.com")
        assert has_event_tracking(page) is False
