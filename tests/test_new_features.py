"""Tests for harvest, consent-audit, and badge features."""

from __future__ import annotations

import pytest

from growthlint.analyzers.playbook_harvester import (
    GrowthPlaybook,
    harvest_playbook,
    format_playbook,
)
from growthlint.analyzers.consent_audit import (
    audit_consent,
    format_consent_report,
)
from growthlint.generators.badge_generator import (
    generate_badge,
    generate_badge_markdown,
    save_badge,
)
from growthlint.models import GrowthScore
from growthlint.scanners.dom_parser import parse_html


# ---- Fixtures ---- #

@pytest.fixture
def competitor_page():
    """A competitor page with a rich growth stack."""
    html = """<!DOCTYPE html>
    <html><head>
        <title>CompetitorApp - Project Management for Teams</title>
        <meta name="description" content="The best project management tool.">
        <meta property="og:title" content="CompetitorApp">
        <meta property="og:image" content="https://competitor.com/og.png">
        <link rel="canonical" href="https://competitor.com/">
        <link rel="icon" href="/favicon.ico">
    </head><body>
        <h1>Ship 2x faster with CompetitorApp</h1>
        <h2>Trusted by 10,000+ companies</h2>
        <p>4.9 out of 5 on G2. 2,000+ reviews.</p>
        <p>SOC 2 certified. GDPR compliant.</p>
        <p>Free trial for 14 days. Cancel anytime.</p>
        <p>Save 20% with annual billing. Most popular: Pro plan.</p>
        <p>Enterprise custom pricing available. Contact sales.</p>
        <a href="/signup" class="cta">Start Free Trial</a>
        <a href="/demo" class="cta">Book a Demo</a>
        <a href="/pricing">Pricing</a>
        <a href="/blog">Blog</a>
        <a href="/docs">Documentation</a>
        <a href="/about">About Us</a>
        <a href="/careers">Careers</a>
        <a href="/contact">Contact</a>
        <a href="/privacy">Privacy Policy</a>
        <a href="/terms">Terms of Service</a>
        <a href="/changelog">Changelog</a>
        <a href="/customers">Customer Stories</a>
        <form action="/newsletter"><input name="email" type="email"><button>Subscribe</button></form>
        <script src="https://www.googletagmanager.com/gtm.js?id=GTM-XXXX"></script>
        <script src="https://www.googletagmanager.com/gtag/js?id=G-XXXX"></script>
        <script>
            gtag('config', 'G-XXXX');
        </script>
        <script src="https://connect.facebook.net/en_US/fbevents.js"></script>
        <script>fbq('init', '12345'); fbq('track', 'PageView');</script>
        <script src="https://snap.licdn.com/li.lms-analytics/insight.min.js"></script>
        <script src="https://widget.intercom.io/widget/abc123"></script>
        <script src="https://static.klaviyo.com/onsite/js/klaviyo.js"></script>
        <script src="https://cdn.shopify.com/s/files/shop.js"></script>
        <script type="application/ld+json">
        {"@context": "https://schema.org", "@type": "Organization", "name": "CompetitorApp"}
        </script>
    </body></html>"""
    return parse_html(html, url="https://competitor.com/")


@pytest.fixture
def compliant_page():
    """A page with proper consent setup."""
    html = """<!DOCTYPE html>
    <html><head>
        <title>Compliant Site</title>
    </head><body>
        <h1>Welcome</h1>
        <a href="/privacy">Privacy Policy</a>
        <a href="/cookie-policy">Cookie Policy</a>
        <a href="/terms">Terms of Service</a>
        <a href="/do-not-sell">Do Not Sell My Data</a>
        <script src="https://cdn.cookielaw.org/scripttemplates/otSDKStub.js"></script>
        <script>
            gtag('consent', 'default', {
                ad_storage: 'denied',
                ad_user_data: 'denied',
                ad_personalization: 'denied',
                analytics_storage: 'denied'
            });
        </script>
        <p>Reject all cookies or manage your preferences.</p>
        <p>Analytics cookies, marketing cookies, functional cookies.</p>
        <script src="https://www.googletagmanager.com/gtag/js?id=G-XXXX"></script>
    </body></html>"""
    return parse_html(html, url="https://compliant.com/")


@pytest.fixture
def noncompliant_page():
    """A page with tracking but no consent."""
    html = """<!DOCTYPE html>
    <html><head>
        <title>No Consent Site</title>
    </head><body>
        <h1>Welcome</h1>
        <script src="https://www.googletagmanager.com/gtag/js?id=G-XXXX"></script>
        <script>gtag('config', 'G-XXXX');</script>
        <script src="https://connect.facebook.net/en_US/fbevents.js"></script>
        <script>fbq('init', '12345'); fbq('track', 'PageView');</script>
    </body></html>"""
    return parse_html(html, url="https://noncompliant.com/")


# ---- Playbook Harvester Tests ---- #

class TestPlaybookHarvester:

    def test_detects_analytics_tools(self, competitor_page):
        playbook = harvest_playbook(competitor_page)
        tool_names = [t.name.lower() for t in playbook.tools]
        analytics_found = any("ga4" in n or "gtm" in n or "analytics" in n or "tag manager" in n
                              for n in tool_names)
        assert analytics_found

    def test_detects_retargeting(self, competitor_page):
        playbook = harvest_playbook(competitor_page)
        assert len(playbook.retargeting) >= 2  # FB Pixel + LinkedIn

    def test_detects_support_tools(self, competitor_page):
        playbook = harvest_playbook(competitor_page)
        categories = [t.category for t in playbook.tools]
        assert "support & chat" in categories

    def test_detects_email_tools(self, competitor_page):
        playbook = harvest_playbook(competitor_page)
        categories = [t.category for t in playbook.tools]
        assert "email & marketing" in categories

    def test_extracts_ctas(self, competitor_page):
        playbook = harvest_playbook(competitor_page)
        assert len(playbook.cta_strategy) >= 2

    def test_detects_social_proof(self, competitor_page):
        playbook = harvest_playbook(competitor_page)
        assert len(playbook.social_proof) >= 1

    def test_detects_pricing_psychology(self, competitor_page):
        playbook = harvest_playbook(competitor_page)
        assert len(playbook.pricing_psychology) >= 3

    def test_maps_funnel_pages(self, competitor_page):
        playbook = harvest_playbook(competitor_page)
        page_types = {p.page_type for p in playbook.funnel_pages}
        assert "pricing" in page_types
        assert "blog" in page_types

    def test_detects_lead_capture(self, competitor_page):
        playbook = harvest_playbook(competitor_page)
        assert len(playbook.lead_capture) >= 1

    def test_detects_tech_stack(self, competitor_page):
        playbook = harvest_playbook(competitor_page)
        assert len(playbook.tech_stack) >= 1  # Shopify at least

    def test_generates_steal_this(self, competitor_page):
        playbook = harvest_playbook(competitor_page)
        assert len(playbook.steal_this) >= 3

    def test_seo_strategy(self, competitor_page):
        playbook = harvest_playbook(competitor_page)
        assert playbook.seo_strategy["has_title"] is True
        assert playbook.seo_strategy["has_canonical"] is True
        assert "Organization" in playbook.seo_strategy["schema_types"]

    def test_format_playbook(self, competitor_page):
        playbook = harvest_playbook(competitor_page)
        md = format_playbook(playbook)
        assert "Growth Playbook" in md
        assert "Steal This" in md
        assert "CTA Strategy" in md


# ---- Consent Audit Tests ---- #

class TestConsentAudit:

    def test_detects_consent_banner(self, compliant_page):
        report = audit_consent(compliant_page)
        assert report.consent_banner.detected is True
        assert report.consent_banner.provider == "OneTrust"

    def test_no_banner_on_noncompliant(self, noncompliant_page):
        report = audit_consent(noncompliant_page)
        assert report.consent_banner.detected is False

    def test_noncompliant_has_critical_issues(self, noncompliant_page):
        report = audit_consent(noncompliant_page)
        critical = [i for i in report.issues if i.severity == "critical"]
        assert len(critical) >= 2  # No banner + no privacy policy at minimum

    def test_noncompliant_is_not_compliant(self, noncompliant_page):
        report = audit_consent(noncompliant_page)
        assert report.compliant is False

    def test_noncompliant_low_score(self, noncompliant_page):
        report = audit_consent(noncompliant_page)
        assert report.compliance_score < 50

    def test_detects_consent_mode_v2(self, compliant_page):
        report = audit_consent(compliant_page)
        assert report.consent_mode.v2_detected is True
        assert "ad_storage" in report.consent_mode.storage_settings

    def test_detects_privacy_links(self, compliant_page):
        report = audit_consent(compliant_page)
        link_types = {l.link_type for l in report.privacy_links}
        assert "privacy_policy" in link_types
        assert "terms" in link_types
        assert "do_not_sell" in link_types

    def test_detects_reject_option(self, compliant_page):
        report = audit_consent(compliant_page)
        assert report.consent_banner.has_reject_option is True

    def test_detects_granular_choices(self, compliant_page):
        report = audit_consent(compliant_page)
        assert report.consent_banner.has_granular_choices is True

    def test_categorizes_tracking_scripts(self, noncompliant_page):
        report = audit_consent(noncompliant_page)
        categories = {s.category for s in report.tracking_scripts}
        assert "analytics" in categories or "marketing" in categories

    def test_detects_pre_consent_firing(self, noncompliant_page):
        report = audit_consent(noncompliant_page)
        pre_consent = [s for s in report.tracking_scripts if s.fires_before_consent]
        assert len(pre_consent) >= 1

    def test_format_consent_report(self, noncompliant_page):
        report = audit_consent(noncompliant_page)
        md = format_consent_report(report)
        assert "Compliance Score" in md
        assert "NON-COMPLIANT" in md
        assert "Quick Fix Checklist" in md

    def test_compliant_page_higher_score(self, compliant_page):
        report = audit_consent(compliant_page)
        assert report.compliance_score > 50


# ---- Badge Generator Tests ---- #

class TestBadgeGenerator:

    def test_generate_badge_svg(self):
        score = GrowthScore(score=85, grade="B+")
        svg = generate_badge(score)
        assert svg.startswith("<svg")
        assert "GrowthLint" in svg
        assert "85/100" in svg

    def test_badge_color_green_for_a(self):
        score = GrowthScore(score=95, grade="A")
        svg = generate_badge(score)
        assert "#4c1" in svg

    def test_badge_color_red_for_f(self):
        score = GrowthScore(score=20, grade="F")
        svg = generate_badge(score)
        assert "#cb2431" in svg

    def test_badge_flat_style(self):
        score = GrowthScore(score=70, grade="B")
        svg = generate_badge(score, style="flat")
        assert "linearGradient" in svg

    def test_badge_flat_square_style(self):
        score = GrowthScore(score=70, grade="B")
        svg = generate_badge(score, style="flat-square")
        assert "linearGradient" not in svg

    def test_badge_for_the_badge_style(self):
        score = GrowthScore(score=70, grade="B")
        svg = generate_badge(score, style="for-the-badge")
        assert "GROWTHLINT" in svg  # Uppercase

    def test_generate_badge_markdown(self):
        score = GrowthScore(score=80, grade="B+")
        md = generate_badge_markdown(score)
        assert "GrowthLint Score" in md
        assert ".svg" in md

    def test_save_badge(self, tmp_path):
        score = GrowthScore(score=90, grade="A")
        filepath = str(tmp_path / "test-badge.svg")
        result = save_badge(score, filepath)
        assert result == filepath
        with open(filepath) as f:
            content = f.read()
        assert "<svg" in content
        assert "90/100" in content
