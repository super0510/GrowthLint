"""Competitor comparison analyzer."""

from __future__ import annotations

from dataclasses import dataclass, field

from growthlint.models import PageData, RuleViolation
from growthlint.rules.engine import evaluate_rules
from growthlint.rules.loader import load_rules
from growthlint.scanners.dom_parser import detect_analytics_tools
from growthlint.scanners.url_scanner import scan_url
from growthlint.utils.scoring import calculate_score


@dataclass
class SiteProfile:
    """Profile of a single site for comparison."""

    url: str
    score: int = 0
    grade: str = ""
    violations: list[RuleViolation] = field(default_factory=list)
    analytics_tools: list[str] = field(default_factory=list)
    has_schema: bool = False
    has_ctas: bool = False
    has_social_proof: bool = False
    has_trust_signals: bool = False
    cta_count: int = 0
    form_count: int = 0
    h1_text: str = ""
    meta_title: str = ""
    meta_description: str = ""


@dataclass
class ComparisonResult:
    """Side-by-side comparison of two sites."""

    site_a: SiteProfile
    site_b: SiteProfile
    your_advantages: list[str] = field(default_factory=list)
    your_gaps: list[str] = field(default_factory=list)
    shared_issues: list[str] = field(default_factory=list)


def compare_sites(url_a: str, url_b: str) -> ComparisonResult:
    """Compare two sites side by side."""
    profile_a = _build_profile(url_a)
    profile_b = _build_profile(url_b)

    advantages = []
    gaps = []
    shared = []

    # Score comparison
    if profile_a.score > profile_b.score:
        advantages.append(f"Higher overall score ({profile_a.score} vs {profile_b.score})")
    elif profile_b.score > profile_a.score:
        gaps.append(f"Lower overall score ({profile_a.score} vs {profile_b.score})")

    # Analytics comparison
    a_tools = set(profile_a.analytics_tools)
    b_tools = set(profile_b.analytics_tools)
    if a_tools - b_tools:
        advantages.append(f"Analytics tools they don't have: {', '.join(a_tools - b_tools)}")
    if b_tools - a_tools:
        gaps.append(f"Analytics tools you're missing: {', '.join(b_tools - a_tools)}")

    # Feature comparisons
    if profile_a.has_schema and not profile_b.has_schema:
        advantages.append("You have structured data (JSON-LD), they don't")
    elif profile_b.has_schema and not profile_a.has_schema:
        gaps.append("They have structured data (JSON-LD), you don't")

    if profile_a.has_social_proof and not profile_b.has_social_proof:
        advantages.append("You have social proof, they don't")
    elif profile_b.has_social_proof and not profile_a.has_social_proof:
        gaps.append("They have social proof, you don't")

    if profile_a.has_trust_signals and not profile_b.has_trust_signals:
        advantages.append("You have trust signals, they don't")
    elif profile_b.has_trust_signals and not profile_a.has_trust_signals:
        gaps.append("They have trust signals, you don't")

    if profile_a.cta_count > profile_b.cta_count:
        advantages.append(f"More CTAs ({profile_a.cta_count} vs {profile_b.cta_count})")
    elif profile_b.cta_count > profile_a.cta_count:
        gaps.append(f"Fewer CTAs ({profile_a.cta_count} vs {profile_b.cta_count})")

    # Shared issues
    a_ids = {v.rule_id for v in profile_a.violations}
    b_ids = {v.rule_id for v in profile_b.violations}
    common = a_ids & b_ids
    if common:
        shared = [f"Both sites have: {rid}" for rid in sorted(common)[:5]]

    return ComparisonResult(
        site_a=profile_a,
        site_b=profile_b,
        your_advantages=advantages,
        your_gaps=gaps,
        shared_issues=shared,
    )


def _build_profile(url: str) -> SiteProfile:
    """Build a site profile from a URL scan."""
    page = scan_url(url)
    rules = load_rules()
    violations = evaluate_rules(page, rules)
    score_data = calculate_score(violations)
    analytics = detect_analytics_tools(page)

    from growthlint.rules.engine import _find_social_proof, _find_trust_signals
    social = _find_social_proof(page)
    trust = _find_trust_signals(page)

    return SiteProfile(
        url=url,
        score=score_data.score,
        grade=score_data.grade,
        violations=violations,
        analytics_tools=analytics,
        has_schema=len(page.schema_markup) > 0,
        has_ctas=len(page.ctas) > 0,
        has_social_proof=len(social) > 0,
        has_trust_signals=len(trust) > 0,
        cta_count=len(page.ctas),
        form_count=len(page.forms),
        h1_text=page.headings.get("h1", [""])[0] if page.headings.get("h1") else "",
        meta_title=page.meta.title,
        meta_description=page.meta.description,
    )


def format_comparison(result: ComparisonResult) -> str:
    """Format comparison as markdown."""
    lines: list[str] = []
    a = result.site_a
    b = result.site_b

    lines.append("# Competitor Comparison")
    lines.append("")
    lines.append(f"**Your site:** {a.url}")
    lines.append(f"**Competitor:** {b.url}")
    lines.append("")

    # Score comparison
    lines.append("## Score Comparison")
    lines.append("")
    lines.append("| Metric | Your Site | Competitor |")
    lines.append("|--------|-----------|------------|")
    lines.append(f"| Score | {a.score}/100 ({a.grade}) | {b.score}/100 ({b.grade}) |")
    lines.append(f"| Total Issues | {len(a.violations)} | {len(b.violations)} |")
    lines.append(f"| CTAs | {a.cta_count} | {b.cta_count} |")
    lines.append(f"| Forms | {a.form_count} | {b.form_count} |")
    lines.append(f"| Schema | {'Yes' if a.has_schema else 'No'} | {'Yes' if b.has_schema else 'No'} |")
    lines.append(f"| Social Proof | {'Yes' if a.has_social_proof else 'No'} | {'Yes' if b.has_social_proof else 'No'} |")
    lines.append(f"| Trust Signals | {'Yes' if a.has_trust_signals else 'No'} | {'Yes' if b.has_trust_signals else 'No'} |")
    lines.append(f"| Analytics Tools | {len(a.analytics_tools)} | {len(b.analytics_tools)} |")
    lines.append("")

    if result.your_advantages:
        lines.append("## Where You're Ahead")
        lines.append("")
        for adv in result.your_advantages:
            lines.append(f"- {adv}")
        lines.append("")

    if result.your_gaps:
        lines.append("## Where You're Behind")
        lines.append("")
        for gap in result.your_gaps:
            lines.append(f"- {gap}")
        lines.append("")

    if result.shared_issues:
        lines.append("## Shared Issues")
        lines.append("")
        for issue in result.shared_issues:
            lines.append(f"- {issue}")
        lines.append("")

    return "\n".join(lines)
