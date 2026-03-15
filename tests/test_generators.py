"""Tests for GrowthLint generators."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from growthlint.generators.funnel_mapper import (
    map_funnel,
    format_funnel_map,
    FunnelStage,
)
from growthlint.generators.analytics_spec import (
    generate_analytics_spec,
    format_analytics_spec,
)
from growthlint.generators.patch_generator import generate_patches
from growthlint.generators.growth_diff import (
    save_snapshot,
    load_snapshots,
    diff_snapshots,
    format_diff,
)
from growthlint.models import (
    AuditReport,
    GrowthScore,
    RuleViolation,
    PageData,
    MetaData,
    PageElement,
    FormData,
)
from growthlint.scanners.dom_parser import parse_html


# ---- Fixtures ---- #

@pytest.fixture
def multi_page_site():
    """Multiple pages simulating a real funnel."""
    pages = []

    # Landing page
    landing = parse_html("""
    <html><head><title>Acme - Landing</title></head><body>
        <h1>Welcome to Acme</h1>
        <a href="/pricing">See Pricing</a>
        <a href="/signup">Get Started</a>
    </body></html>""", url="https://acme.com/")
    pages.append(landing)

    # Pricing page
    pricing = parse_html("""
    <html><head><title>Pricing</title></head><body>
        <h1>Simple Pricing</h1>
        <p>$29/month. Per month pricing.</p>
        <a href="/signup">Start Free Trial</a>
    </body></html>""", url="https://acme.com/pricing")
    pages.append(pricing)

    # Signup page
    signup = parse_html("""
    <html><head><title>Sign Up</title></head><body>
        <h1>Create Account</h1>
        <form action="/api/signup"><input name="email" type="email"><button>Sign Up</button></form>
    </body></html>""", url="https://acme.com/signup")
    pages.append(signup)

    # Blog (dead end - no CTA)
    blog = parse_html("""
    <html><head><title>Blog</title></head><body>
        <h1>Our Blog</h1>
        <p>Some blog content.</p>
    </body></html>""", url="https://acme.com/blog/post-1")
    pages.append(blog)

    return pages


@pytest.fixture
def sample_report():
    """A sample AuditReport for snapshot testing."""
    return AuditReport(
        target="https://example.com",
        scan_date="2026-01-01 10:00",
        pages_scanned=1,
        score=GrowthScore(
            score=65,
            grade="C+",
            total_violations=5,
            critical_count=1,
            warning_count=3,
            info_count=1,
            revenue_leak_estimate="10-25%",
            category_scores={"conversion": 70, "seo": 80, "analytics": 50},
        ),
        violations=[
            RuleViolation(
                rule_id="no-analytics",
                rule_name="No Analytics",
                category="analytics",
                severity="critical",
                description="No analytics detected",
                impact="Flying blind",
                fix="Install GA4",
                revenue_weight=1.0,
                page_url="https://example.com",
            ),
            RuleViolation(
                rule_id="missing-meta-description",
                rule_name="Missing Meta Description",
                category="seo",
                severity="warning",
                description="No meta description",
                impact="Google generates one",
                fix="Add meta description",
                revenue_weight=0.4,
                page_url="https://example.com",
            ),
        ],
    )


@pytest.fixture
def improved_report():
    """An improved report for diff testing."""
    return AuditReport(
        target="https://example.com",
        scan_date="2026-02-01 10:00",
        pages_scanned=1,
        score=GrowthScore(
            score=80,
            grade="B+",
            total_violations=2,
            critical_count=0,
            warning_count=1,
            info_count=1,
            revenue_leak_estimate="5-10%",
            category_scores={"conversion": 85, "seo": 90, "analytics": 70},
        ),
        violations=[
            RuleViolation(
                rule_id="weak-cta-text",
                rule_name="Weak CTA Text",
                category="conversion",
                severity="info",
                description="Generic CTA",
                impact="Lower clicks",
                fix="Use specific text",
                revenue_weight=0.35,
                page_url="https://example.com",
            ),
            RuleViolation(
                rule_id="missing-meta-description",
                rule_name="Missing Meta Description",
                category="seo",
                severity="warning",
                description="No meta description",
                impact="Google generates one",
                fix="Add meta description",
                revenue_weight=0.4,
                page_url="https://example.com",
            ),
        ],
    )


# ---- Funnel Mapper Tests ---- #

class TestFunnelMapper:

    def test_classifies_landing_page(self, multi_page_site):
        funnel = map_funnel(multi_page_site)
        types = {s.page_type for s in funnel.stages}
        assert "landing" in types

    def test_classifies_pricing_page(self, multi_page_site):
        funnel = map_funnel(multi_page_site)
        types = {s.page_type for s in funnel.stages}
        assert "pricing" in types

    def test_classifies_signup_page(self, multi_page_site):
        funnel = map_funnel(multi_page_site)
        types = {s.page_type for s in funnel.stages}
        assert "signup" in types

    def test_detects_dead_ends(self, multi_page_site):
        funnel = map_funnel(multi_page_site)
        assert len(funnel.dead_ends) > 0

    def test_detects_missing_stages(self, multi_page_site):
        funnel = map_funnel(multi_page_site)
        # Missing thank_you and product pages
        assert "thank_you" in funnel.missing_stages

    def test_stage_count(self, multi_page_site):
        funnel = map_funnel(multi_page_site)
        assert funnel.stage_count == 4

    def test_format_has_mermaid(self, multi_page_site):
        funnel = map_funnel(multi_page_site)
        md = format_funnel_map(funnel)
        assert "```mermaid" in md
        assert "graph TD" in md

    def test_format_shows_dead_ends(self, multi_page_site):
        funnel = map_funnel(multi_page_site)
        md = format_funnel_map(funnel)
        assert "Dead-End" in md

    def test_format_shows_missing(self, multi_page_site):
        funnel = map_funnel(multi_page_site)
        md = format_funnel_map(funnel)
        assert "Missing Funnel Stages" in md


# ---- Analytics Spec Tests ---- #

class TestAnalyticsSpec:

    def test_generates_events(self, multi_page_site):
        spec = generate_analytics_spec(multi_page_site)
        assert len(spec.events) > 0

    def test_has_page_view_event(self, multi_page_site):
        spec = generate_analytics_spec(multi_page_site)
        names = [e.event_name for e in spec.events]
        assert "page_view" in names

    def test_has_cta_click_event(self, multi_page_site):
        spec = generate_analytics_spec(multi_page_site)
        names = [e.event_name for e in spec.events]
        assert "cta_click" in names

    def test_has_form_submit_event(self, multi_page_site):
        spec = generate_analytics_spec(multi_page_site)
        names = [e.event_name for e in spec.events]
        assert "form_submit" in names

    def test_events_have_properties(self, multi_page_site):
        spec = generate_analytics_spec(multi_page_site)
        for event in spec.events:
            assert isinstance(event.properties, dict)

    def test_format_spec(self, multi_page_site):
        spec = generate_analytics_spec(multi_page_site)
        md = format_analytics_spec(spec)
        assert "Tracking Plan" in md
        assert "page_view" in md


# ---- Patch Generator Tests ---- #

class TestPatchGenerator:

    def test_generates_patches_for_missing_meta(self):
        violation = RuleViolation(
            rule_id="missing-meta-description",
            rule_name="Missing Meta Description",
            category="seo",
            severity="warning",
            description="No meta desc",
            impact="Bad",
            fix="Add one",
            revenue_weight=0.4,
            page_url="https://example.com",
        )
        page = parse_html(
            "<html><head><title>Test</title></head><body><h1>Hi</h1></body></html>",
            url="https://example.com",
        )
        patches = generate_patches([violation], page)
        assert len(patches) > 0
        assert any("meta" in p.code.lower() for p in patches)

    def test_generates_patches_for_missing_viewport(self):
        violation = RuleViolation(
            rule_id="missing-viewport",
            rule_name="Missing Viewport",
            category="seo",
            severity="critical",
            description="No viewport",
            impact="Bad mobile",
            fix="Add viewport",
            revenue_weight=0.8,
            page_url="https://example.com",
        )
        page = parse_html(
            "<html><head><title>Test</title></head><body><h1>Hi</h1></body></html>",
            url="https://example.com",
        )
        patches = generate_patches([violation], page)
        assert len(patches) > 0
        assert any("viewport" in p.code.lower() for p in patches)

    def test_no_patches_for_unknown_rule(self):
        violation = RuleViolation(
            rule_id="unknown-rule",
            rule_name="Unknown",
            category="other",
            severity="info",
            description="Something",
            impact="Low",
            fix="N/A",
            revenue_weight=0.1,
            page_url="https://example.com",
        )
        page = parse_html(
            "<html><head><title>Test</title></head><body><h1>Hi</h1></body></html>",
            url="https://example.com",
        )
        patches = generate_patches([violation], page)
        assert len(patches) == 0


# ---- Growth Diff Tests ---- #

class TestGrowthDiff:

    def test_save_and_load_snapshot(self, sample_report):
        with TemporaryDirectory() as tmpdir:
            path = save_snapshot(sample_report, directory=Path(tmpdir))
            assert path.exists()
            assert path.suffix == ".json"

            snapshots = load_snapshots(directory=Path(tmpdir))
            assert len(snapshots) == 1
            assert snapshots[0][1].score.score == 65

    def test_diff_shows_improvement(self, sample_report, improved_report):
        diff = diff_snapshots(sample_report, improved_report)
        assert diff.score_delta > 0
        assert diff.old_score == 65
        assert diff.new_score == 80

    def test_diff_shows_fixed_violations(self, sample_report, improved_report):
        diff = diff_snapshots(sample_report, improved_report)
        assert len(diff.fixed_violations) > 0
        assert any("No Analytics" in v for v in diff.fixed_violations)

    def test_diff_shows_new_violations(self, sample_report, improved_report):
        diff = diff_snapshots(sample_report, improved_report)
        assert len(diff.new_violations) > 0
        assert any("Weak CTA" in v for v in diff.new_violations)

    def test_diff_category_deltas(self, sample_report, improved_report):
        diff = diff_snapshots(sample_report, improved_report)
        assert len(diff.category_deltas) > 0
        assert diff.category_deltas.get("analytics", 0) > 0

    def test_format_diff(self, sample_report, improved_report):
        diff = diff_snapshots(sample_report, improved_report)
        md = format_diff(diff)
        assert "Growth Diff Report" in md
        assert "65" in md
        assert "80" in md

    def test_empty_snapshot_dir(self):
        with TemporaryDirectory() as tmpdir:
            snapshots = load_snapshots(directory=Path(tmpdir))
            assert len(snapshots) == 0

    def test_nonexistent_snapshot_dir(self):
        snapshots = load_snapshots(directory=Path("/nonexistent/path"))
        assert len(snapshots) == 0
