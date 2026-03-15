"""Tests for rule loading and evaluation."""

from __future__ import annotations

from growthlint.rules.engine import evaluate_rules
from growthlint.rules.loader import load_rules
from growthlint.scanners.dom_parser import parse_html
from growthlint.utils.scoring import calculate_score


class TestRuleLoader:
    def test_loads_all_rules(self) -> None:
        rules = load_rules()
        assert len(rules) >= 15  # We created 23 rules across 4 files

    def test_loads_by_category(self) -> None:
        seo_rules = load_rules(categories=["seo"])
        assert all(r.category == "seo" for r in seo_rules)
        assert len(seo_rules) >= 5

    def test_all_rules_have_required_fields(self) -> None:
        rules = load_rules()
        for rule in rules:
            assert rule.id, f"Rule missing id"
            assert rule.name, f"Rule {rule.id} missing name"
            assert rule.category, f"Rule {rule.id} missing category"
            assert rule.severity, f"Rule {rule.id} missing severity"
            assert rule.check, f"Rule {rule.id} missing check"
            assert rule.impact, f"Rule {rule.id} missing impact"
            assert rule.fix, f"Rule {rule.id} missing fix"
            assert rule.revenue_weight > 0, f"Rule {rule.id} has zero revenue_weight"


class TestRuleEvaluation:
    def test_sample_site_has_violations(self, sample_html: str) -> None:
        page = parse_html(sample_html, url="https://example.com")
        rules = load_rules()
        violations = evaluate_rules(page, rules)
        assert len(violations) > 0

    def test_sample_site_missing_analytics(self, sample_html: str) -> None:
        page = parse_html(sample_html, url="https://example.com")
        rules = load_rules(categories=["analytics"])
        violations = evaluate_rules(page, rules)
        violation_ids = [v.rule_id for v in violations]
        assert "no-analytics" in violation_ids

    def test_sample_site_missing_viewport(self, sample_html: str) -> None:
        page = parse_html(sample_html, url="https://example.com")
        rules = load_rules(categories=["seo"])
        violations = evaluate_rules(page, rules)
        violation_ids = [v.rule_id for v in violations]
        assert "missing-viewport" in violation_ids

    def test_sample_site_images_missing_alt(self, sample_html: str) -> None:
        page = parse_html(sample_html, url="https://example.com")
        rules = load_rules(categories=["seo"])
        violations = evaluate_rules(page, rules)
        violation_ids = [v.rule_id for v in violations]
        assert "images-missing-alt" in violation_ids

    def test_sample_site_missing_og_tags(self, sample_html: str) -> None:
        page = parse_html(sample_html, url="https://example.com")
        rules = load_rules(categories=["seo"])
        violations = evaluate_rules(page, rules)
        violation_ids = [v.rule_id for v in violations]
        assert "missing-og-tags" in violation_ids

    def test_minimal_page_fewer_violations(self, minimal_html: str) -> None:
        page = parse_html(minimal_html, url="https://example.com")
        rules = load_rules()
        violations = evaluate_rules(page, rules)
        # Minimal page should have significantly fewer issues
        sample_violations = evaluate_rules(
            parse_html((open("tests/fixtures/sample_react_site/index.html").read()), url="https://example.com"),
            rules,
        )
        assert len(violations) < len(sample_violations)

    def test_violations_have_details(self, sample_html: str) -> None:
        page = parse_html(sample_html, url="https://example.com")
        rules = load_rules()
        violations = evaluate_rules(page, rules)
        for v in violations:
            assert v.rule_id
            assert v.rule_name
            assert v.category
            assert v.severity


class TestScoring:
    def test_sample_site_low_score(self, sample_html: str) -> None:
        page = parse_html(sample_html, url="https://example.com")
        rules = load_rules()
        violations = evaluate_rules(page, rules)
        score = calculate_score(violations)
        # Sample site has many issues, should score low
        assert score.score < 70
        assert score.grade in ("C+", "C", "D", "F")

    def test_no_violations_perfect_score(self) -> None:
        score = calculate_score([])
        assert score.score == 100
        assert score.grade == "A"

    def test_score_has_category_breakdown(self, sample_html: str) -> None:
        page = parse_html(sample_html, url="https://example.com")
        rules = load_rules()
        violations = evaluate_rules(page, rules)
        score = calculate_score(violations)
        assert len(score.category_scores) > 0

    def test_revenue_estimate(self, sample_html: str) -> None:
        page = parse_html(sample_html, url="https://example.com")
        rules = load_rules()
        violations = evaluate_rules(page, rules)
        score = calculate_score(violations)
        assert score.revenue_leak_estimate != ""
        assert "conversion improvement" in score.revenue_leak_estimate.lower() or "minimal" in score.revenue_leak_estimate.lower()
