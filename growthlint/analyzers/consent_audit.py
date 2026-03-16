"""Tracking Compliance Scanner — GDPR/CCPA consent audit."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from growthlint.config import ANALYTICS_PATTERNS
from growthlint.models import PageData


# ---------------------------------------------------------------------------
# CMP (Consent Management Platform) detection patterns
# ---------------------------------------------------------------------------

CMP_PATTERNS: dict[str, list[str]] = {
    "OneTrust": [r"onetrust", r"optanon", r"cdn\.cookielaw\.org"],
    "CookieBot": [r"cookiebot", r"consent\.cookiebot\.com"],
    "TrustArc": [r"trustarc", r"consent\.trustarc\.com", r"truste"],
    "Osano": [r"osano", r"cmp\.osano\.com"],
    "Termly": [r"termly", r"app\.termly\.io"],
    "Iubenda": [r"iubenda", r"cdn\.iubenda\.com"],
    "CookieYes": [r"cookieyes", r"cdn-cookieyes\.com"],
    "Complianz": [r"complianz", r"cmplz"],
    "Cookie Notice": [r"cookie-notice", r"cookie-law-info"],
    "Quantcast": [r"quantcast", r"cmp\.quantcast\.com"],
    "Usercentrics": [r"usercentrics"],
    "Didomi": [r"didomi", r"sdk\.privacy-center"],
}

# Patterns for categorizing third-party scripts
SCRIPT_CATEGORIES: dict[str, list[str]] = {
    "essential": [
        r"cdn\.jsdelivr\.net", r"cdnjs\.cloudflare\.com", r"unpkg\.com",
        r"ajax\.googleapis\.com", r"stackpath\.bootstrapcdn",
        r"fonts\.googleapis\.com", r"fonts\.gstatic\.com",
        r"code\.jquery\.com",
    ],
    "analytics": [
        r"google-analytics\.com", r"googletagmanager\.com",
        r"cdn\.segment\.com", r"posthog", r"cdn\.mxpnl\.com",
        r"mixpanel", r"plausible\.io", r"cdn\.usefathom\.com",
        r"static\.hotjar\.com", r"clarity\.ms", r"cdn\.amplitude\.com",
    ],
    "marketing": [
        r"connect\.facebook\.net", r"fbevents\.js",
        r"googleads", r"doubleclick\.net",
        r"snap\.licdn\.com", r"ads-twitter\.com",
        r"analytics\.tiktok\.com", r"ct\.pinterest\.com",
        r"alb\.reddit\.com",
    ],
    "functional": [
        r"widget\.intercom\.io", r"js\.driftt\.com",
        r"zdassets\.com", r"crisp\.chat",
        r"livechatinc\.com", r"hubspot\.com",
    ],
}

# Consent gating patterns in inline scripts
CONSENT_GATE_PATTERNS = [
    r"if\s*\(.*consent",
    r"addEventListener.*consent",
    r"cookieconsent.*callback",
    r"onAccept",
    r"onConsentChange",
    r"consent.*granted",
    r"hasConsent",
]


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class ConsentBannerStatus:
    detected: bool = False
    provider: str = ""
    has_reject_option: bool = False
    has_granular_choices: bool = False
    detected_via: str = ""


@dataclass
class TrackingScript:
    name: str
    category: str  # essential, analytics, marketing, functional, unknown
    src: str
    fires_before_consent: bool = False
    has_consent_gate: bool = False


@dataclass
class PrivacyLink:
    link_type: str  # privacy_policy, cookie_policy, terms, do_not_sell
    url: str
    in_footer: bool = False


@dataclass
class ConsentModeStatus:
    v2_detected: bool = False
    has_default_config: bool = False
    storage_settings: dict[str, str] = field(default_factory=dict)


@dataclass
class ComplianceIssue:
    severity: str  # critical, warning, info
    category: str  # consent, privacy, tracking, rights
    title: str
    description: str
    regulation: str  # GDPR, CCPA, ePrivacy, all
    fix: str


@dataclass
class ConsentAuditReport:
    url: str
    consent_banner: ConsentBannerStatus = field(default_factory=ConsentBannerStatus)
    consent_mode: ConsentModeStatus = field(default_factory=ConsentModeStatus)
    tracking_scripts: list[TrackingScript] = field(default_factory=list)
    privacy_links: list[PrivacyLink] = field(default_factory=list)
    issues: list[ComplianceIssue] = field(default_factory=list)

    @property
    def compliant(self) -> bool:
        return not any(i.severity == "critical" for i in self.issues)

    @property
    def compliance_score(self) -> int:
        deductions = sum(
            {"critical": 25, "warning": 10, "info": 3}.get(i.severity, 0)
            for i in self.issues
        )
        return max(0, 100 - deductions)


# ---------------------------------------------------------------------------
# Core audit logic
# ---------------------------------------------------------------------------

def audit_consent(page_data: PageData) -> ConsentAuditReport:
    """Run a full consent and tracking compliance audit."""
    report = ConsentAuditReport(url=page_data.url)

    all_scripts_text = " ".join(page_data.scripts + page_data.inline_scripts)
    all_sources = " ".join(page_data.script_sources)
    search_text = all_scripts_text + " " + all_sources
    text_content = page_data.text_content.lower()

    # 1. Detect consent banner / CMP
    report.consent_banner = _detect_consent_banner(search_text, text_content)

    # 2. Detect Google Consent Mode v2
    report.consent_mode = _detect_consent_mode(all_scripts_text)

    # 3. Categorize tracking scripts
    report.tracking_scripts = _categorize_scripts(page_data, report.consent_banner)

    # 4. Find privacy/legal links
    report.privacy_links = _find_privacy_links(page_data)

    # 5. Generate compliance issues
    report.issues = _generate_issues(report, page_data)

    return report


def _detect_consent_banner(scripts: str, text: str) -> ConsentBannerStatus:
    """Detect if a consent management platform is present."""
    status = ConsentBannerStatus()

    for provider, patterns in CMP_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, scripts, re.IGNORECASE):
                status.detected = True
                status.provider = provider
                status.detected_via = pattern
                break
        if status.detected:
            break

    # Also check for generic cookie consent patterns in text/scripts
    if not status.detected:
        generic = [r"cookie.?consent", r"cookie.?banner", r"cookie.?notice", r"gdpr.?banner"]
        for pattern in generic:
            if re.search(pattern, scripts + " " + text, re.IGNORECASE):
                status.detected = True
                status.provider = "Custom"
                status.detected_via = pattern
                break

    # Check for reject option
    reject_patterns = [r"reject\s*all", r"decline\s*all", r"deny\s*all", r"refuse"]
    for pattern in reject_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            status.has_reject_option = True
            break

    # Check for granular choices
    granular_patterns = [
        r"(analytics|functional|marketing|advertising)\s*cookies?",
        r"cookie\s*(categories|preferences|settings)",
        r"manage\s*(cookie|consent)\s*(preferences|settings)",
    ]
    for pattern in granular_patterns:
        if re.search(pattern, text + " " + scripts, re.IGNORECASE):
            status.has_granular_choices = True
            break

    return status


def _detect_consent_mode(scripts: str) -> ConsentModeStatus:
    """Detect Google Consent Mode v2 implementation."""
    status = ConsentModeStatus()

    # Check for consent mode default configuration
    if re.search(r"gtag\s*\(\s*['\"]consent['\"],\s*['\"]default['\"]", scripts, re.IGNORECASE):
        status.v2_detected = True
        status.has_default_config = True

    # Check for storage settings
    storage_keys = ["ad_storage", "ad_user_data", "ad_personalization", "analytics_storage"]
    for key in storage_keys:
        match = re.search(rf"{key}\s*:\s*['\"](\w+)['\"]", scripts)
        if match:
            status.v2_detected = True
            status.storage_settings[key] = match.group(1)

    # Also detect consent mode update calls
    if re.search(r"gtag\s*\(\s*['\"]consent['\"],\s*['\"]update['\"]", scripts, re.IGNORECASE):
        status.v2_detected = True

    return status


def _categorize_scripts(page_data: PageData, banner: ConsentBannerStatus) -> list[TrackingScript]:
    """Categorize all external scripts and check consent ordering."""
    scripts: list[TrackingScript] = []
    inline_text = " ".join(page_data.inline_scripts)

    # Find CMP script position in the ordered script list
    cmp_position = -1
    if banner.detected and banner.detected_via:
        for i, src in enumerate(page_data.scripts):
            if re.search(banner.detected_via, src, re.IGNORECASE):
                cmp_position = i
                break

    for i, src in enumerate(page_data.script_sources):
        name = _identify_script(src)
        category = _classify_script(src)

        fires_before = False
        if cmp_position >= 0 and category in ("analytics", "marketing") and i < cmp_position:
            fires_before = True
        elif cmp_position < 0 and category in ("analytics", "marketing"):
            fires_before = True  # No CMP at all = fires without consent

        has_gate = any(
            re.search(p, inline_text, re.IGNORECASE) for p in CONSENT_GATE_PATTERNS
        ) if category in ("analytics", "marketing") else False

        scripts.append(TrackingScript(
            name=name,
            category=category,
            src=src,
            fires_before_consent=fires_before,
            has_consent_gate=has_gate,
        ))

    return scripts


def _identify_script(src: str) -> str:
    """Return a human-readable name for a script source."""
    identifiers = {
        "google-analytics": "Google Analytics",
        "googletagmanager": "Google Tag Manager",
        "gtag": "Google gtag.js",
        "segment.com": "Segment",
        "posthog": "PostHog",
        "mixpanel": "Mixpanel",
        "hotjar": "Hotjar",
        "clarity.ms": "Microsoft Clarity",
        "amplitude": "Amplitude",
        "plausible": "Plausible",
        "usefathom": "Fathom",
        "facebook.net": "Meta Pixel",
        "fbevents": "Meta Pixel",
        "doubleclick": "Google Ads",
        "googleads": "Google Ads",
        "licdn.com": "LinkedIn Insight",
        "ads-twitter": "Twitter/X Pixel",
        "tiktok.com": "TikTok Pixel",
        "pinterest.com": "Pinterest Tag",
        "intercom": "Intercom",
        "drift": "Drift",
        "zendesk": "Zendesk",
        "crisp.chat": "Crisp",
        "hubspot": "HubSpot",
        "onetrust": "OneTrust",
        "cookiebot": "CookieBot",
        "cookielaw": "OneTrust",
    }
    src_lower = src.lower()
    for key, name in identifiers.items():
        if key in src_lower:
            return name
    # Return domain as fallback
    parts = src.split("/")
    for part in parts:
        if "." in part and not part.startswith("."):
            return part
    return src[:60]


def _classify_script(src: str) -> str:
    """Classify a script source into a category."""
    for category, patterns in SCRIPT_CATEGORIES.items():
        for pattern in patterns:
            if re.search(pattern, src, re.IGNORECASE):
                return category
    return "unknown"


def _find_privacy_links(page_data: PageData) -> list[PrivacyLink]:
    """Find privacy-related links on the page."""
    links: list[PrivacyLink] = []
    link_checks = [
        ("privacy_policy", [r"privacy\s*policy", r"privacy\s*notice"], [r"/privacy"]),
        ("cookie_policy", [r"cookie\s*policy", r"cookie\s*notice"], [r"/cookie"]),
        ("terms", [r"terms\s*(of\s*service|of\s*use|&\s*conditions)", r"terms\s*and"], [r"/terms", r"/tos"]),
        ("do_not_sell", [r"do\s*not\s*sell", r"opt.?out", r"ccpa"], [r"/do-not-sell", r"/opt-out", r"/ccpa"]),
    ]

    for link_type, text_patterns, href_patterns in link_checks:
        for link in page_data.links:
            text = link.text.lower()
            href = link.href.lower()
            matched = False
            for pattern in text_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    matched = True
                    break
            if not matched:
                for pattern in href_patterns:
                    if re.search(pattern, href):
                        matched = True
                        break
            if matched:
                # Heuristic: if link is in last 20% of all links, likely in footer
                link_idx = next((i for i, l in enumerate(page_data.links) if l.href == link.href), 0)
                in_footer = link_idx > len(page_data.links) * 0.8
                links.append(PrivacyLink(
                    link_type=link_type, url=link.href, in_footer=in_footer,
                ))
                break  # One per type

    return links


def _generate_issues(report: ConsentAuditReport, page_data: PageData) -> list[ComplianceIssue]:
    """Generate compliance issues based on audit findings."""
    issues: list[ComplianceIssue] = []
    has_tracking = any(s.category in ("analytics", "marketing") for s in report.tracking_scripts)

    # CRITICAL: No consent banner but tracking present
    if not report.consent_banner.detected and has_tracking:
        issues.append(ComplianceIssue(
            severity="critical",
            category="consent",
            title="No consent banner detected",
            description="Tracking scripts are present but no cookie consent mechanism was found. "
                        "This violates GDPR and ePrivacy Directive requirements.",
            regulation="GDPR",
            fix="Install a Consent Management Platform (CMP) such as CookieBot, OneTrust, or Osano. "
                "Ensure it loads before any tracking scripts.",
        ))

    # CRITICAL: Scripts fire before consent
    pre_consent = [s for s in report.tracking_scripts if s.fires_before_consent]
    for script in pre_consent:
        issues.append(ComplianceIssue(
            severity="critical",
            category="tracking",
            title=f"{script.name} fires before consent",
            description=f"{script.name} ({script.category}) loads before the consent banner. "
                        "This means user data is collected without consent.",
            regulation="GDPR",
            fix=f"Move {script.name} below the CMP script, or use Google Tag Manager with "
                "consent mode to gate this script behind user consent.",
        ))

    # CRITICAL: No privacy policy
    has_privacy = any(l.link_type == "privacy_policy" for l in report.privacy_links)
    if not has_privacy and has_tracking:
        issues.append(ComplianceIssue(
            severity="critical",
            category="privacy",
            title="No privacy policy link found",
            description="No privacy policy link was detected. Both GDPR and CCPA require "
                        "a clear, accessible privacy policy.",
            regulation="all",
            fix="Add a privacy policy link to your footer. The policy should describe "
                "what data you collect, how you use it, and how users can exercise their rights.",
        ))

    # CRITICAL: No Consent Mode v2 (required for Google tools since March 2024)
    has_google = any(s.name in ("Google Analytics", "Google Tag Manager", "Google gtag.js", "Google Ads")
                     for s in report.tracking_scripts)
    if has_google and not report.consent_mode.v2_detected:
        issues.append(ComplianceIssue(
            severity="critical",
            category="consent",
            title="Google Consent Mode v2 not detected",
            description="Google tools are present but Consent Mode v2 is not configured. "
                        "Since March 2024, Google requires Consent Mode v2 for all advertising features in the EEA.",
            regulation="GDPR",
            fix="Add gtag('consent', 'default', { ad_storage: 'denied', "
                "ad_user_data: 'denied', ad_personalization: 'denied', "
                "analytics_storage: 'denied' }) before your GTM/GA4 script. "
                "Then update consent state when user accepts.",
        ))

    # WARNING: No reject-all option
    if report.consent_banner.detected and not report.consent_banner.has_reject_option:
        issues.append(ComplianceIssue(
            severity="warning",
            category="consent",
            title="No 'Reject All' option on consent banner",
            description="GDPR requires that rejecting cookies must be as easy as accepting them. "
                        "No 'Reject All' button was detected.",
            regulation="GDPR",
            fix=f"Configure {report.consent_banner.provider} to show a 'Reject All' button "
                "with equal prominence to 'Accept All'.",
        ))

    # WARNING: No granular cookie choices
    if report.consent_banner.detected and not report.consent_banner.has_granular_choices:
        issues.append(ComplianceIssue(
            severity="warning",
            category="consent",
            title="No granular cookie categories",
            description="The consent banner does not appear to offer per-category cookie choices "
                        "(analytics, marketing, functional).",
            regulation="GDPR",
            fix="Configure your CMP to let users choose which cookie categories to accept.",
        ))

    # WARNING: No "Do Not Sell" link (CCPA)
    has_dns = any(l.link_type == "do_not_sell" for l in report.privacy_links)
    if not has_dns and has_tracking:
        issues.append(ComplianceIssue(
            severity="warning",
            category="rights",
            title="No 'Do Not Sell My Data' link",
            description="CCPA requires a 'Do Not Sell My Personal Information' link for California users.",
            regulation="CCPA",
            fix="Add a 'Do Not Sell My Personal Information' link to your footer "
                "that allows users to opt out of data sales.",
        ))

    # WARNING: Marketing scripts without consent gate
    ungated_marketing = [s for s in report.tracking_scripts
                         if s.category == "marketing" and not s.has_consent_gate and not s.fires_before_consent]
    for script in ungated_marketing:
        issues.append(ComplianceIssue(
            severity="warning",
            category="tracking",
            title=f"{script.name} may not be consent-gated",
            description=f"{script.name} is a marketing script but no consent gating pattern was detected.",
            regulation="GDPR",
            fix=f"Ensure {script.name} only fires after the user grants marketing consent.",
        ))

    # INFO: No cookie policy
    has_cookie_policy = any(l.link_type == "cookie_policy" for l in report.privacy_links)
    if not has_cookie_policy and has_tracking:
        issues.append(ComplianceIssue(
            severity="info",
            category="privacy",
            title="No separate cookie policy",
            description="No dedicated cookie policy was found. While often included in the privacy policy, "
                        "a separate cookie policy improves transparency.",
            regulation="ePrivacy",
            fix="Consider adding a dedicated cookie policy page that lists all cookies, "
                "their purposes, and expiration periods.",
        ))

    # INFO: No terms of service
    has_terms = any(l.link_type == "terms" for l in report.privacy_links)
    if not has_terms:
        issues.append(ComplianceIssue(
            severity="info",
            category="privacy",
            title="No terms of service link",
            description="No terms of service link was found on the page.",
            regulation="all",
            fix="Add a terms of service link to your footer.",
        ))

    # INFO: Unclassified scripts
    unknown = [s for s in report.tracking_scripts if s.category == "unknown"]
    if unknown:
        issues.append(ComplianceIssue(
            severity="info",
            category="tracking",
            title=f"{len(unknown)} unclassified third-party scripts",
            description="Some external scripts could not be categorized. Review them to ensure "
                        "they are properly classified in your consent configuration.",
            regulation="GDPR",
            fix="Audit unclassified scripts and add them to the appropriate consent category "
                "in your CMP configuration.",
        ))

    return issues


# ---------------------------------------------------------------------------
# Markdown formatter
# ---------------------------------------------------------------------------

def format_consent_report(report: ConsentAuditReport) -> str:
    """Format the consent audit as markdown."""
    lines: list[str] = []
    status = "COMPLIANT" if report.compliant else "NON-COMPLIANT"
    status_icon = "✓" if report.compliant else "✗"

    lines.append(f"# Consent & Compliance Audit: {report.url}")
    lines.append("")
    lines.append(f"## Compliance Score: {report.compliance_score}/100 — {status} {status_icon}")
    lines.append("")

    # Consent banner
    lines.append("## Consent Banner")
    lines.append("")
    if report.consent_banner.detected:
        lines.append(f"- **Status:** Detected ({report.consent_banner.provider})")
        lines.append(f"- **Reject Option:** {'Yes' if report.consent_banner.has_reject_option else 'Not found'} "
                     f"{'✓' if report.consent_banner.has_reject_option else '⚠️'}")
        lines.append(f"- **Granular Choices:** {'Yes' if report.consent_banner.has_granular_choices else 'Not found'} "
                     f"{'✓' if report.consent_banner.has_granular_choices else '⚠️'}")
    else:
        lines.append("- **Status:** Not detected ✗")
    lines.append("")

    # Google Consent Mode
    lines.append("## Google Consent Mode v2")
    lines.append("")
    if report.consent_mode.v2_detected:
        lines.append("- **Status:** Detected ✓")
        if report.consent_mode.has_default_config:
            lines.append("- **Default Config:** Set ✓")
        if report.consent_mode.storage_settings:
            for key, val in report.consent_mode.storage_settings.items():
                lines.append(f"- **{key}:** {val}")
    else:
        lines.append("- **Status:** Not detected ✗")
        lines.append("- **Required since:** March 2024 for all Google advertising tools in EEA")
    lines.append("")

    # Tracking scripts
    tracking = [s for s in report.tracking_scripts if s.category != "essential"]
    if tracking:
        lines.append(f"## Tracking Scripts ({len(tracking)} non-essential)")
        lines.append("")
        lines.append("| Script | Category | Fires Before Consent | Consent Gated |")
        lines.append("|--------|----------|---------------------|---------------|")
        for s in tracking:
            before = "Yes ✗" if s.fires_before_consent else "No ✓"
            gated = "Yes ✓" if s.has_consent_gate else "No ✗"
            lines.append(f"| {s.name} | {s.category} | {before} | {gated} |")
        lines.append("")

    # Privacy links
    lines.append("## Privacy & Legal Links")
    lines.append("")
    link_types = {
        "privacy_policy": "Privacy Policy",
        "cookie_policy": "Cookie Policy",
        "terms": "Terms of Service",
        "do_not_sell": "Do Not Sell (CCPA)",
    }
    found_types = {l.link_type for l in report.privacy_links}
    for lt, label in link_types.items():
        if lt in found_types:
            link = next(l for l in report.privacy_links if l.link_type == lt)
            lines.append(f"- {label}: {link.url} ✓")
        else:
            lines.append(f"- {label}: Not found ✗")
    lines.append("")

    # Issues
    if report.issues:
        lines.append(f"## Issues Found ({len(report.issues)})")
        lines.append("")

        for severity in ["critical", "warning", "info"]:
            severity_issues = [i for i in report.issues if i.severity == severity]
            if severity_issues:
                icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}[severity]
                lines.append(f"### {icon} {severity.title()}")
                lines.append("")
                for issue in severity_issues:
                    lines.append(f"**{issue.title}** ({issue.regulation})")
                    lines.append(f"  {issue.description}")
                    lines.append(f"  **Fix:** {issue.fix}")
                    lines.append("")

    # Recommendations summary
    lines.append("## Quick Fix Checklist")
    lines.append("")
    critical = [i for i in report.issues if i.severity == "critical"]
    warnings = [i for i in report.issues if i.severity == "warning"]
    for i, issue in enumerate(critical + warnings, 1):
        lines.append(f"{i}. [ ] {issue.title} — {issue.fix}")
    lines.append("")

    return "\n".join(lines)
