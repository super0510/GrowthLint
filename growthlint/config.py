"""Configuration for GrowthLint."""

from __future__ import annotations

from pathlib import Path

# Package paths
PACKAGE_DIR = Path(__file__).parent
DATA_DIR = PACKAGE_DIR / "data"

# Severity weights for scoring
SEVERITY_WEIGHTS = {
    "critical": 10,
    "warning": 5,
    "info": 1,
}

# HTTP defaults
DEFAULT_USER_AGENT = "GrowthLint/0.1 (+https://github.com/super0510/GrowthLint)"
DEFAULT_TIMEOUT = 15
MAX_RETRIES = 2

# CTA text patterns (regex, case-insensitive)
CTA_PATTERNS = [
    r"sign\s*up",
    r"get\s*started",
    r"start\s*free",
    r"try\s*(it\s*)?free",
    r"try\s*now",
    r"buy\s*now",
    r"add\s*to\s*cart",
    r"subscribe",
    r"join\s*(now|free|us)?",
    r"download",
    r"book\s*(a\s*)?(demo|call|meeting)",
    r"schedule",
    r"request\s*(a\s*)?(demo|quote|trial)",
    r"claim",
    r"start\s*(your\s*)?(trial|journey)",
    r"create\s*(an?\s*)?account",
    r"register",
    r"contact\s*(us|sales)",
    r"learn\s*more",
    r"shop\s*now",
    r"order\s*now",
    r"enroll",
]

# Analytics tool detection patterns
ANALYTICS_PATTERNS = {
    "ga4": [
        r"gtag\(['\"]config['\"],\s*['\"]G-",
        r"googletagmanager\.com/gtag",
        r"google-analytics\.com/g/collect",
    ],
    "gtm": [
        r"googletagmanager\.com/gtm\.js",
        r"GTM-[A-Z0-9]+",
    ],
    "segment": [
        r"cdn\.segment\.com",
        r"analytics\.load\(",
        r"analytics\.identify\(",
    ],
    "posthog": [
        r"posthog",
        r"app\.posthog\.com",
        r"us\.posthog\.com",
    ],
    "mixpanel": [
        r"cdn\.mxpnl\.com",
        r"mixpanel\.init\(",
        r"mixpanel\.track\(",
    ],
    "hotjar": [
        r"static\.hotjar\.com",
        r"hj\(['\"]identify",
    ],
    "fb_pixel": [
        r"connect\.facebook\.net.*fbevents\.js",
        r"fbq\(['\"]init",
    ],
    "clarity": [
        r"clarity\.ms/tag/",
    ],
    "amplitude": [
        r"cdn\.amplitude\.com",
        r"amplitude\.getInstance\(",
    ],
    "plausible": [
        r"plausible\.io",
    ],
    "fathom": [
        r"cdn\.usefathom\.com",
    ],
}

# Event tracking patterns
EVENT_TRACKING_PATTERNS = [
    r"analytics\.track\(",
    r"gtag\(['\"]event['\"]",
    r"dataLayer\.push\(",
    r"posthog\.capture\(",
    r"mixpanel\.track\(",
    r"fbq\(['\"]track",
    r"plausible\(",
    r"umami\.track\(",
    r"\.track\(['\"]",
]
