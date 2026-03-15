"""Rule evaluation engine for GrowthLint."""

from __future__ import annotations

import re
import signal
from contextlib import contextmanager

from growthlint.models import PageData, RuleDefinition, RuleViolation
from growthlint.scanners.dom_parser import detect_analytics_tools, has_event_tracking

# Maximum time (seconds) for a single regex match against page content.
_REGEX_TIMEOUT = 2


class RegexTimeoutError(Exception):
    """Raised when a regex match exceeds the time limit."""


@contextmanager
def _regex_timeout(seconds: int):
    """Context manager that raises RegexTimeoutError after *seconds*."""
    def _handler(signum, frame):
        raise RegexTimeoutError("Regex match timed out")

    old = signal.signal(signal.SIGALRM, _handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


def _safe_regex_search(pattern_str: str, text: str, flags: int = 0) -> re.Match | None:
    """Compile and search with a timeout to guard against catastrophic backtracking."""
    compiled = re.compile(pattern_str, flags)
    try:
        with _regex_timeout(_REGEX_TIMEOUT):
            return compiled.search(text)
    except RegexTimeoutError:
        return None


def _safe_regex_filter(pattern_str: str, elements: list[str], flags: int = 0) -> list[str]:
    """Filter elements matching *pattern_str* with a per-element timeout."""
    compiled = re.compile(pattern_str, flags)
    matches: list[str] = []
    for elem in elements:
        try:
            with _regex_timeout(_REGEX_TIMEOUT):
                if compiled.search(elem):
                    matches.append(elem)
        except RegexTimeoutError:
            continue
    return matches


def evaluate_rules(page_data: PageData, rules: list[RuleDefinition]) -> list[RuleViolation]:
    """Evaluate all rules against page data and return violations."""
    violations = []
    for rule in rules:
        violation = _evaluate_rule(page_data, rule)
        if violation:
            violations.append(violation)
    return violations


def _evaluate_rule(page_data: PageData, rule: RuleDefinition) -> RuleViolation | None:
    """Evaluate a single rule. Returns a violation if the rule is triggered."""
    check = rule.check
    triggered = False
    details = ""

    if check.type == "presence":
        triggered, details = _check_presence(page_data, rule)
    elif check.type == "absence":
        triggered, details = _check_absence(page_data, rule)
    elif check.type == "count":
        triggered, details = _check_count(page_data, rule)
    elif check.type == "pattern":
        triggered, details = _check_pattern(page_data, rule)
    elif check.type == "attribute":
        triggered, details = _check_attribute(page_data, rule)
    elif check.type == "analytics":
        triggered, details = _check_analytics(page_data, rule)
    elif check.type == "meta_quality":
        triggered, details = _check_meta_quality(page_data, rule)

    if triggered:
        return RuleViolation(
            rule_id=rule.id,
            rule_name=rule.name,
            category=rule.category,
            severity=rule.severity,
            description=rule.description or rule.impact,
            impact=rule.impact,
            fix=rule.fix,
            revenue_weight=rule.revenue_weight,
            page_url=page_data.url,
            details=details,
        )
    return None


def _check_presence(page_data: PageData, rule: RuleDefinition) -> tuple[bool, str]:
    """Check that required elements are present. Violation = missing."""
    check = rule.check
    elements = _get_elements(page_data, check.field or check.selector)

    if check.text_pattern:
        matching = _safe_regex_filter(check.text_pattern, elements, re.IGNORECASE)
        if not matching:
            return True, f"No elements matching pattern '{check.text_pattern}' found"
        return False, ""

    if not elements:
        return True, f"No '{check.field or check.selector}' elements found"
    return False, ""


def _check_absence(page_data: PageData, rule: RuleDefinition) -> tuple[bool, str]:
    """Check that unwanted elements are absent. Violation = found."""
    check = rule.check
    elements = _get_elements(page_data, check.field or check.selector)

    if check.text_pattern:
        matching = _safe_regex_filter(check.text_pattern, elements, re.IGNORECASE)
        if matching:
            return True, f"Found {len(matching)} unwanted elements"
        return False, ""

    if elements:
        return True, f"Found {len(elements)} unwanted elements"
    return False, ""


def _check_count(page_data: PageData, rule: RuleDefinition) -> tuple[bool, str]:
    """Check element count is within range."""
    check = rule.check
    elements = _get_elements(page_data, check.field or check.selector)
    count = len(elements)

    if check.min_count is not None and count < check.min_count:
        return True, f"Found {count}, expected at least {check.min_count}"
    if check.max_count is not None and count > check.max_count:
        return True, f"Found {count}, expected at most {check.max_count}"
    return False, ""


def _check_pattern(page_data: PageData, rule: RuleDefinition) -> tuple[bool, str]:
    """Check for pattern in page content. Violation = pattern not found (or found for negative)."""
    check = rule.check
    target = _get_field_value(page_data, check.field)

    if not check.text_pattern:
        return False, ""

    found = bool(_safe_regex_search(check.text_pattern, target, re.IGNORECASE))

    # For pattern checks, violation means the pattern was NOT found
    if not found:
        return True, f"Pattern '{check.text_pattern}' not found in {check.field}"
    return False, ""


def _check_attribute(page_data: PageData, rule: RuleDefinition) -> tuple[bool, str]:
    """Check attributes on elements. Common: images without alt text."""
    check = rule.check

    if check.field == "images":
        missing_alt = [img for img in page_data.images if not img.text.strip()]
        if missing_alt:
            return True, f"{len(missing_alt)} images missing alt text"
        return False, ""

    if check.field == "links":
        empty_links = [l for l in page_data.links if not l.text.strip() and not l.attributes.get("aria-label")]
        if empty_links:
            return True, f"{len(empty_links)} links missing accessible text"
        return False, ""

    return False, ""


def _check_analytics(page_data: PageData, rule: RuleDefinition) -> tuple[bool, str]:
    """Check analytics-related conditions."""
    check = rule.check

    if check.field == "analytics_tools":
        tools = detect_analytics_tools(page_data)
        if not tools:
            return True, "No analytics tools detected"
        return False, ""

    if check.field == "event_tracking":
        if not has_event_tracking(page_data):
            return True, "No event tracking detected"
        return False, ""

    if check.field == "conversion_tracking":
        tools = detect_analytics_tools(page_data)
        has_events = has_event_tracking(page_data)
        if tools and not has_events:
            return True, f"Analytics detected ({', '.join(tools)}) but no event tracking found"
        return False, ""

    return False, ""


def _check_meta_quality(page_data: PageData, rule: RuleDefinition) -> tuple[bool, str]:
    """Check meta tag quality (length, content)."""
    check = rule.check
    meta = page_data.meta

    if check.field == "title_length":
        title_len = len(meta.title)
        if check.min_count and title_len < check.min_count:
            return True, f"Title too short ({title_len} chars, min {check.min_count})"
        if check.max_count and title_len > check.max_count:
            return True, f"Title too long ({title_len} chars, max {check.max_count})"
        return False, ""

    if check.field == "description_length":
        desc_len = len(meta.description)
        if check.min_count and desc_len < check.min_count:
            return True, f"Meta description too short ({desc_len} chars, min {check.min_count})"
        if check.max_count and desc_len > check.max_count:
            return True, f"Meta description too long ({desc_len} chars, max {check.max_count})"
        return False, ""

    return False, ""


def _get_elements(page_data: PageData, field: str) -> list[str]:
    """Get a list of string values from page data for a given field."""
    if field == "ctas":
        return [cta.text for cta in page_data.ctas]
    if field == "h1":
        return page_data.headings.get("h1", [])
    if field == "h2":
        return page_data.headings.get("h2", [])
    if field in ("h1", "h2", "h3", "h4", "h5", "h6"):
        return page_data.headings.get(field, [])
    if field == "images":
        return [img.href for img in page_data.images]
    if field == "links":
        return [l.href for l in page_data.links]
    if field == "forms":
        return [f.action for f in page_data.forms]
    if field == "scripts":
        return page_data.scripts
    if field == "script_sources":
        return page_data.script_sources
    if field == "schema_markup":
        return [str(s) for s in page_data.schema_markup]
    if field == "title":
        return [page_data.meta.title] if page_data.meta.title else []
    if field == "description":
        return [page_data.meta.description] if page_data.meta.description else []
    if field == "canonical":
        return [page_data.meta.canonical] if page_data.meta.canonical else []
    if field == "viewport":
        return [page_data.meta.viewport] if page_data.meta.viewport else []
    if field == "og_tags":
        tags = []
        if page_data.meta.og_title:
            tags.append(page_data.meta.og_title)
        if page_data.meta.og_description:
            tags.append(page_data.meta.og_description)
        return tags
    if field == "favicon":
        return [page_data.meta.favicon] if page_data.meta.favicon else []
    if field == "social_proof":
        return _find_social_proof(page_data)
    if field == "trust_signals":
        return _find_trust_signals(page_data)
    return []


def _get_field_value(page_data: PageData, field: str) -> str:
    """Get a single string value for pattern matching."""
    if field == "text_content":
        return page_data.text_content
    if field == "inline_scripts":
        return " ".join(page_data.inline_scripts)
    if field == "all_scripts":
        return " ".join(page_data.scripts)
    elements = _get_elements(page_data, field)
    return " ".join(elements)


def _find_social_proof(page_data: PageData) -> list[str]:
    """Find social proof indicators in page text."""
    patterns = [
        r"\d[\d,]*\+?\s*(customers?|users?|companies|businesses|teams?|people)",
        r"trusted\s+by",
        r"as\s+seen\s+(in|on)",
        r"testimonial",
        r"customer\s+stor(y|ies)",
        r"case\s+stud(y|ies)",
        r"reviews?\s*\(",
        r"\d+(\.\d+)?\s*\/\s*5\s*(stars?)?",
        r"rated\s+\d",
    ]
    found = []
    for pattern in patterns:
        if re.search(pattern, page_data.text_content, re.IGNORECASE):
            found.append(pattern)
    return found


def _find_trust_signals(page_data: PageData) -> list[str]:
    """Find trust signal indicators."""
    patterns = [
        r"money[- ]back\s+guarantee",
        r"free\s+(trial|cancell?ation)",
        r"no\s+credit\s+card",
        r"ssl|secure|encrypted",
        r"gdpr|privacy",
        r"soc\s*2|iso\s*27001|hipaa",
        r"100%\s+satisfaction",
        r"cancel\s+any\s*time",
    ]
    found = []
    for pattern in patterns:
        if re.search(pattern, page_data.text_content, re.IGNORECASE):
            found.append(pattern)
    return found
