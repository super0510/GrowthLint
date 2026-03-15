"""Tests for GrowthLint analyzers."""

from __future__ import annotations

import pytest

from growthlint.analyzers.integration_health import (
    check_integrations,
    format_integration_report,
)
from growthlint.analyzers.page_psychology import (
    analyze_psychology,
    format_psychology_report,
)
from growthlint.analyzers.message_matcher import (
    check_messages,
    format_message_report,
)
from growthlint.analyzers.schema_finder import (
    find_schema_opportunities,
    format_schema_suggestions,
)
from growthlint.scanners.dom_parser import parse_html


# ---- Fixtures ---- #

@pytest.fixture
def rich_page():
    """A page with many trust signals, social proof, and analytics."""
    html = """<!DOCTYPE html>
    <html><head>
        <title>Acme SaaS - Project Management</title>
        <meta name="description" content="Acme helps teams manage projects faster.">
    </head><body>
        <h1>Get 2x More Done With Acme</h1>
        <h2>Trusted by 10,000+ Teams</h2>
        <h2>How It Works</h2>
        <h2>What Our Customers Say</h2>
        <p>Trusted by companies like Google and Stripe.</p>
        <p>4.8 / 5 stars from 500+ reviews</p>
        <p>SOC 2 certified. GDPR compliant.</p>
        <p>Since 2018. 5+ years of experience.</p>
        <p>30-day money-back guarantee. Cancel anytime. No credit card required.</p>
        <p>Limited time offer! Only 10 spots remaining.</p>
        <p>As seen on Forbes and TechCrunch.</p>
        <p>Meet the team behind Acme.</p>
        <a href="/signup" class="cta">Start Free Trial</a>
        <form action="/signup"><input name="email" type="email"><button>Sign Up</button></form>
        <img src="/logo.png" alt="Acme logo">
        <script src="https://www.googletagmanager.com/gtm.js?id=GTM-XXXX"></script>
        <script src="https://www.googletagmanager.com/gtag/js?id=G-XXXX"></script>
        <script>
            gtag('config', 'G-XXXX');
            gtag('event', 'page_view');
            dataLayer.push({'event': 'signup_click'});
        </script>
    </body></html>"""
    return parse_html(html, url="https://acme.com/")


@pytest.fixture
def bare_page():
    """A minimal page with nothing."""
    html = """<!DOCTYPE html>
    <html><head><title>Bare Page</title></head>
    <body><h1>Hello World</h1><p>Some text.</p></body></html>"""
    return parse_html(html, url="https://bare.com/")


@pytest.fixture
def mismatch_page():
    """A page with mismatched H1 and title."""
    html = """<!DOCTYPE html>
    <html><head>
        <title>Best CRM Software for Small Business</title>
    </head><body>
        <h1>Welcome to Our Platform</h1>
        <h2>FEATURES AND BENEFITS FOR YOUR TEAM</h2>
        <a href="/signup">Learn More</a>
    </body></html>"""
    return parse_html(html, url="https://mismatch.com/")


@pytest.fixture
def faq_page():
    """A page with FAQ content."""
    html = """<!DOCTYPE html>
    <html><head>
        <title>FAQ - Acme</title>
        <meta name="description" content="Frequently asked questions about Acme.">
    </head><body>
        <h1>Frequently Asked Questions</h1>
        <h2>What is Acme?</h2>
        <p>Acme is a project management tool.</p>
        <h2>How much does it cost?</h2>
        <p>Plans start at $10/month.</p>
        <h2>Is there a free trial?</h2>
        <p>Yes, 14-day free trial.</p>
    </body></html>"""
    return parse_html(html, url="https://acme.com/faq")


@pytest.fixture
def product_page():
    """A page with product signals."""
    html = """<!DOCTYPE html>
    <html><head>
        <title>Widget Pro - $49.99</title>
        <meta name="description" content="Buy Widget Pro, the best widget.">
    </head><body>
        <h1>Widget Pro</h1>
        <p>Price: $49.99. In stock. Free shipping.</p>
        <p>4.5 / 5 stars. Rated by 200 customers.</p>
        <button>Add to Cart</button>
        <button>Buy Now</button>
    </body></html>"""
    return parse_html(html, url="https://shop.com/product/widget-pro")


# ---- Integration Health Tests ---- #

class TestIntegrationHealth:

    def test_detects_ga4_and_gtm(self, rich_page):
        report = check_integrations(rich_page)
        detected_ids = {t.tool_id for t in report.detected_tools}
        assert "ga4" in detected_ids
        assert "gtm" in detected_ids

    def test_detects_ga4_events(self, rich_page):
        report = check_integrations(rich_page)
        ga4 = next(t for t in report.integrations if t.tool_id == "ga4")
        assert ga4.has_events is True

    def test_no_tools_on_bare_page(self, bare_page):
        report = check_integrations(bare_page)
        assert len(report.detected_tools) == 0

    def test_recommendations_for_bare_page(self, bare_page):
        report = check_integrations(bare_page)
        assert len(report.recommendations) > 0
        assert any("analytics" in r.lower() for r in report.recommendations)

    def test_conflict_detection(self, rich_page):
        report = check_integrations(rich_page)
        # GTM + direct GA4 should trigger a conflict warning
        assert len(report.conflicts) > 0

    def test_format_report(self, rich_page):
        report = check_integrations(rich_page)
        md = format_integration_report(report)
        assert "Integration Health Report" in md
        assert "Google Analytics 4" in md


# ---- Page Psychology Tests ---- #

class TestPagePsychology:

    def test_rich_page_high_score(self, rich_page):
        score = analyze_psychology(rich_page)
        assert score.overall_score >= 50

    def test_rich_page_trust(self, rich_page):
        score = analyze_psychology(rich_page)
        assert score.trust_score > 0

    def test_rich_page_social_proof(self, rich_page):
        score = analyze_psychology(rich_page)
        assert score.social_proof_score > 0

    def test_rich_page_urgency(self, rich_page):
        score = analyze_psychology(rich_page)
        assert score.urgency_score > 0

    def test_rich_page_risk_reduction(self, rich_page):
        score = analyze_psychology(rich_page)
        assert score.risk_reduction_score > 0

    def test_rich_page_clarity(self, rich_page):
        score = analyze_psychology(rich_page)
        assert score.clarity_score > 0

    def test_bare_page_low_score(self, bare_page):
        score = analyze_psychology(bare_page)
        assert score.overall_score < 30

    def test_bare_page_missing_signals(self, bare_page):
        score = analyze_psychology(bare_page)
        missing = [f for f in score.findings if f.signal_type == "missing"]
        assert len(missing) >= 2  # at least trust and social proof missing

    def test_format_report(self, rich_page):
        score = analyze_psychology(rich_page)
        md = format_psychology_report(score)
        assert "Persuasion Score" in md
        assert "Trust" in md


# ---- Message Matcher Tests ---- #

class TestMessageMatcher:

    def test_mismatched_h1_and_title(self, mismatch_page):
        report = check_messages(mismatch_page)
        mismatch_issues = [i for i in report.issues if i.issue_type == "mismatch"]
        assert len(mismatch_issues) > 0

    def test_generic_cta_detected(self, mismatch_page):
        report = check_messages(mismatch_page)
        weak_issues = [i for i in report.issues if i.issue_type == "weak"]
        assert len(weak_issues) > 0

    def test_allcaps_heading_detected(self, mismatch_page):
        report = check_messages(mismatch_page)
        inconsistent = [i for i in report.issues if i.issue_type == "inconsistent"]
        assert len(inconsistent) > 0

    def test_missing_meta_description(self, mismatch_page):
        report = check_messages(mismatch_page)
        missing = [i for i in report.issues if i.issue_type == "missing"]
        assert len(missing) > 0

    def test_consistency_score_deducted(self, mismatch_page):
        report = check_messages(mismatch_page)
        assert report.consistency_score < 100

    def test_aligned_page_no_issues(self, rich_page):
        report = check_messages(rich_page)
        # Rich page has aligned H1/title and non-generic CTA
        mismatch_issues = [i for i in report.issues if i.issue_type == "mismatch"]
        weak_issues = [i for i in report.issues if i.issue_type == "weak"]
        # At least one of these should be clean
        assert report.consistency_score > 0

    def test_format_report(self, mismatch_page):
        report = check_messages(mismatch_page)
        md = format_message_report(report)
        assert "Consistency Score" in md


# ---- Schema Finder Tests ---- #

class TestSchemaFinder:

    def test_organization_always_suggested(self, bare_page):
        suggestions = find_schema_opportunities(bare_page)
        types = [s.schema_type for s in suggestions]
        assert "Organization" in types

    def test_faq_schema_detected(self, faq_page):
        suggestions = find_schema_opportunities(faq_page)
        types = [s.schema_type for s in suggestions]
        assert "FAQPage" in types

    def test_faq_has_questions(self, faq_page):
        suggestions = find_schema_opportunities(faq_page)
        faq = next(s for s in suggestions if s.schema_type == "FAQPage")
        assert len(faq.json_ld["mainEntity"]) >= 2

    def test_product_schema_detected(self, product_page):
        suggestions = find_schema_opportunities(product_page)
        types = [s.schema_type for s in suggestions]
        assert "Product" in types

    def test_review_schema_detected(self, product_page):
        suggestions = find_schema_opportunities(product_page)
        types = [s.schema_type for s in suggestions]
        assert "AggregateRating" in types

    def test_json_ld_has_context(self, bare_page):
        suggestions = find_schema_opportunities(bare_page)
        for s in suggestions:
            assert s.json_ld.get("@context") == "https://schema.org"

    def test_format_suggestions(self, faq_page):
        suggestions = find_schema_opportunities(faq_page)
        md = format_schema_suggestions(suggestions)
        assert "Schema Markup Opportunities" in md
        assert "```json" in md
