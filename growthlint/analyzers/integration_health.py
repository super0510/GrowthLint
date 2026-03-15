"""Analytics integration health checker."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from growthlint.config import ANALYTICS_PATTERNS, EVENT_TRACKING_PATTERNS
from growthlint.models import PageData


TOOL_DISPLAY_NAMES = {
    "ga4": "Google Analytics 4",
    "gtm": "Google Tag Manager",
    "segment": "Segment",
    "posthog": "PostHog",
    "mixpanel": "Mixpanel",
    "hotjar": "Hotjar",
    "fb_pixel": "Meta Pixel (Facebook)",
    "clarity": "Microsoft Clarity",
    "amplitude": "Amplitude",
    "plausible": "Plausible Analytics",
    "fathom": "Fathom Analytics",
}


@dataclass
class IntegrationStatus:
    """Status of a single analytics integration."""

    tool_id: str
    tool_name: str
    detected: bool = False
    has_events: bool = False
    config_issues: list[str] = field(default_factory=list)

    @property
    def health(self) -> str:
        if not self.detected:
            return "not_found"
        if self.config_issues:
            return "warning"
        if not self.has_events:
            return "partial"
        return "healthy"


@dataclass
class IntegrationReport:
    """Full integration health report."""

    integrations: list[IntegrationStatus] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    @property
    def detected_tools(self) -> list[IntegrationStatus]:
        return [i for i in self.integrations if i.detected]


def check_integrations(page_data: PageData) -> IntegrationReport:
    """Check analytics integration health on a page."""
    all_scripts = " ".join(page_data.scripts + page_data.inline_scripts)
    report = IntegrationReport()

    # Check each known analytics tool
    for tool_id, patterns in ANALYTICS_PATTERNS.items():
        status = IntegrationStatus(
            tool_id=tool_id,
            tool_name=TOOL_DISPLAY_NAMES.get(tool_id, tool_id),
        )

        for pattern in patterns:
            if re.search(pattern, all_scripts, re.IGNORECASE):
                status.detected = True
                break

        if status.detected:
            status.has_events = _check_tool_events(tool_id, all_scripts)
            status.config_issues = _check_tool_config(tool_id, all_scripts, page_data)

        report.integrations.append(status)

    # Check for conflicts
    report.conflicts = _detect_conflicts(report.detected_tools, all_scripts)

    # Generate recommendations
    report.recommendations = _generate_recommendations(report)

    return report


def _check_tool_events(tool_id: str, scripts: str) -> bool:
    """Check if a specific tool has event tracking configured."""
    tool_event_patterns = {
        "ga4": [r"gtag\(['\"]event['\"]", r"dataLayer\.push"],
        "gtm": [r"dataLayer\.push"],
        "segment": [r"analytics\.track\(", r"analytics\.identify\("],
        "posthog": [r"posthog\.capture\(", r"posthog\.identify\("],
        "mixpanel": [r"mixpanel\.track\(", r"mixpanel\.identify\("],
        "fb_pixel": [r"fbq\(['\"]track"],
        "amplitude": [r"amplitude\.track\(", r"amplitude\.logEvent\("],
    }

    patterns = tool_event_patterns.get(tool_id, [])
    for pattern in patterns:
        if re.search(pattern, scripts, re.IGNORECASE):
            return True
    return False


def _check_tool_config(tool_id: str, scripts: str, page_data: PageData) -> list[str]:
    """Check for common configuration issues."""
    issues = []

    if tool_id == "ga4":
        # Check for debug mode in production
        if re.search(r"debug_mode.*true", scripts, re.IGNORECASE):
            issues.append("GA4 debug mode is enabled (should be disabled in production)")
        # Check for measurement ID
        if not re.search(r"G-[A-Z0-9]+", scripts):
            issues.append("GA4 measurement ID not found in config")

    if tool_id == "gtm":
        # Check for noscript fallback
        all_html = " ".join(page_data.scripts + [page_data.text_content])
        if not re.search(r"noscript.*googletagmanager", all_html, re.IGNORECASE):
            issues.append("GTM noscript fallback not detected")

    if tool_id == "fb_pixel":
        # Check for PageView event
        if not re.search(r"fbq\(['\"]track['\"],\s*['\"]PageView", scripts):
            issues.append("Meta Pixel PageView event not detected")

    return issues


def _detect_conflicts(detected: list[IntegrationStatus], scripts: str) -> list[str]:
    """Detect potential conflicts between analytics tools."""
    conflicts = []
    tool_ids = {t.tool_id for t in detected}

    # Multiple analytics tools sending pageviews = double counting
    pageview_tools = {"ga4", "plausible", "fathom"}
    active_pv = tool_ids & pageview_tools
    if len(active_pv) > 1:
        names = [TOOL_DISPLAY_NAMES[t] for t in active_pv]
        conflicts.append(
            f"Multiple pageview trackers detected ({', '.join(names)}). "
            "This may cause double-counted sessions."
        )

    # GTM + direct GA4 = potential double tracking
    if "gtm" in tool_ids and "ga4" in tool_ids:
        if re.search(r"gtag\(['\"]config['\"]", scripts):
            conflicts.append(
                "Both GTM and direct GA4 gtag.js detected. "
                "If GA4 is also configured inside GTM, pageviews may be double-counted."
            )

    return conflicts


def _generate_recommendations(report: IntegrationReport) -> list[str]:
    """Generate recommendations based on integration health."""
    recs = []
    detected_ids = {t.tool_id for t in report.detected_tools}

    if not detected_ids:
        recs.append("Install an analytics tool. GA4 (free) or PostHog (open-source) are great starting points.")
        return recs

    if "gtm" not in detected_ids:
        recs.append("Consider installing Google Tag Manager for centralized tag management without code deploys.")

    if not detected_ids & {"hotjar", "clarity"}:
        recs.append("Consider adding a session recording tool (Clarity is free, Hotjar has a free tier) to see actual user behavior.")

    for tool in report.detected_tools:
        if tool.health == "partial":
            recs.append(f"{tool.tool_name}: Detected but no custom events found. Add event tracking for key user actions.")

    return recs


def format_integration_report(report: IntegrationReport) -> str:
    """Format integration health report as markdown."""
    lines: list[str] = []
    lines.append("# Integration Health Report")
    lines.append("")

    detected = report.detected_tools
    lines.append(f"**Detected tools:** {len(detected)}")
    lines.append("")

    if detected:
        lines.append("## Detected Integrations")
        lines.append("")
        lines.append("| Tool | Events | Health | Issues |")
        lines.append("|------|--------|--------|--------|")
        for t in detected:
            health_icon = {"healthy": "🟢", "partial": "🟡", "warning": "🟠"}.get(t.health, "🔴")
            events = "Yes" if t.has_events else "No"
            issues = "; ".join(t.config_issues) if t.config_issues else "-"
            lines.append(f"| {t.tool_name} | {events} | {health_icon} {t.health} | {issues} |")
        lines.append("")

    not_found = [i for i in report.integrations if not i.detected]
    if not_found:
        lines.append("## Not Detected")
        lines.append("")
        for t in not_found:
            lines.append(f"- {t.tool_name}")
        lines.append("")

    if report.conflicts:
        lines.append("## Conflicts")
        lines.append("")
        for c in report.conflicts:
            lines.append(f"- {c}")
        lines.append("")

    if report.recommendations:
        lines.append("## Recommendations")
        lines.append("")
        for r in report.recommendations:
            lines.append(f"- {r}")
        lines.append("")

    return "\n".join(lines)
