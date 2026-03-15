"""Analytics tracking plan generator."""

from __future__ import annotations

from dataclasses import dataclass, field

from growthlint.models import PageData
from growthlint.scanners.dom_parser import detect_analytics_tools


@dataclass
class TrackingEvent:
    """A single event in the tracking plan."""

    event_name: str
    category: str  # pageview, engagement, conversion, system
    description: str
    trigger: str
    properties: dict[str, str] = field(default_factory=dict)
    priority: str = "required"  # required, recommended, optional


@dataclass
class AnalyticsSpec:
    """Complete analytics tracking plan."""

    detected_tools: list[str] = field(default_factory=list)
    events: list[TrackingEvent] = field(default_factory=list)
    implementation_notes: list[str] = field(default_factory=list)


def generate_analytics_spec(pages: list[PageData]) -> AnalyticsSpec:
    """Generate a tracking plan from page analysis."""
    spec = AnalyticsSpec()

    # Detect existing tools
    for page in pages:
        tools = detect_analytics_tools(page)
        for tool in tools:
            if tool not in spec.detected_tools:
                spec.detected_tools.append(tool)

    # Generate events based on detected page elements
    events = []

    # Always needed: page views
    events.append(TrackingEvent(
        event_name="page_view",
        category="pageview",
        description="Track every page load with URL and title",
        trigger="Page load",
        properties={
            "page_url": "Current page URL",
            "page_title": "Document title",
            "referrer": "document.referrer",
            "utm_source": "UTM source parameter",
            "utm_medium": "UTM medium parameter",
            "utm_campaign": "UTM campaign parameter",
        },
        priority="required",
    ))

    # Check for forms
    has_forms = any(page.forms for page in pages)
    if has_forms:
        events.append(TrackingEvent(
            event_name="form_start",
            category="engagement",
            description="Track when a user begins filling out a form",
            trigger="First interaction with any form field",
            properties={
                "form_id": "Form identifier or action URL",
                "form_type": "signup, contact, checkout, etc.",
            },
            priority="recommended",
        ))
        events.append(TrackingEvent(
            event_name="form_submit",
            category="conversion",
            description="Track successful form submissions",
            trigger="Form submission event",
            properties={
                "form_id": "Form identifier",
                "form_type": "signup, contact, checkout, etc.",
                "field_count": "Number of fields submitted",
            },
            priority="required",
        ))

    # Check for CTAs
    has_ctas = any(page.ctas for page in pages)
    if has_ctas:
        events.append(TrackingEvent(
            event_name="cta_click",
            category="engagement",
            description="Track clicks on call-to-action buttons and links",
            trigger="Click on CTA element",
            properties={
                "cta_text": "Button/link text content",
                "cta_url": "Destination URL",
                "cta_location": "Header, hero, sidebar, footer, etc.",
                "page_url": "Page where click occurred",
            },
            priority="required",
        ))

    # Check for external links
    has_external = any(page.external_links for page in pages)
    if has_external:
        events.append(TrackingEvent(
            event_name="outbound_click",
            category="engagement",
            description="Track clicks on external links",
            trigger="Click on link to external domain",
            properties={
                "link_url": "Destination URL",
                "link_text": "Link text",
                "page_url": "Page where click occurred",
            },
            priority="recommended",
        ))

    # Check for images (scroll engagement)
    events.append(TrackingEvent(
        event_name="scroll_depth",
        category="engagement",
        description="Track how far users scroll on each page",
        trigger="Scroll milestones (25%, 50%, 75%, 100%)",
        properties={
            "percent": "Scroll depth percentage",
            "page_url": "Current page URL",
        },
        priority="recommended",
    ))

    # Session-level events
    events.append(TrackingEvent(
        event_name="session_start",
        category="system",
        description="Track new session starts with attribution data",
        trigger="New session detected",
        properties={
            "referrer": "Traffic source",
            "utm_source": "Campaign source",
            "utm_medium": "Campaign medium",
            "utm_campaign": "Campaign name",
            "device_type": "mobile, tablet, desktop",
            "landing_page": "First page URL",
        },
        priority="required",
    ))

    events.append(TrackingEvent(
        event_name="user_identify",
        category="system",
        description="Identify the user after signup/login",
        trigger="Successful authentication or form submit with email",
        properties={
            "user_id": "Unique user identifier",
            "email": "User email (hashed if needed for privacy)",
            "signup_date": "Account creation date",
            "plan": "Current plan/tier",
        },
        priority="required",
    ))

    spec.events = events

    # Implementation notes
    if not spec.detected_tools:
        spec.implementation_notes.append(
            "No analytics tool detected. Install GA4 (free) or PostHog (open-source) first."
        )
    if "gtm" not in spec.detected_tools:
        spec.implementation_notes.append(
            "Consider using Google Tag Manager for centralized event management without code deploys."
        )
    spec.implementation_notes.append(
        "Persist UTM parameters in localStorage on first page load. Attach them to all events."
    )
    spec.implementation_notes.append(
        "Use a naming convention for events: noun_verb (e.g., form_submit, cta_click, page_view)."
    )

    return spec


def format_analytics_spec(spec: AnalyticsSpec) -> str:
    """Format the analytics spec as markdown."""
    lines: list[str] = []
    lines.append("# Analytics Tracking Plan")
    lines.append("")

    if spec.detected_tools:
        lines.append(f"**Detected tools:** {', '.join(spec.detected_tools)}")
    else:
        lines.append("**Detected tools:** None")
    lines.append("")

    # Event taxonomy table
    lines.append("## Event Taxonomy")
    lines.append("")
    lines.append("| Event | Category | Priority | Trigger |")
    lines.append("|-------|----------|----------|---------|")
    for event in spec.events:
        icon = {"required": "🔴", "recommended": "🟡", "optional": "🔵"}.get(event.priority, "")
        lines.append(f"| `{event.event_name}` | {event.category} | {icon} {event.priority} | {event.trigger} |")
    lines.append("")

    # Detailed event specs
    lines.append("## Event Details")
    lines.append("")
    for event in spec.events:
        lines.append(f"### `{event.event_name}`")
        lines.append("")
        lines.append(f"**{event.description}**")
        lines.append("")
        lines.append(f"**Trigger:** {event.trigger}")
        lines.append("")
        if event.properties:
            lines.append("| Property | Description |")
            lines.append("|----------|-------------|")
            for prop, desc in event.properties.items():
                lines.append(f"| `{prop}` | {desc} |")
            lines.append("")

    # Implementation notes
    if spec.implementation_notes:
        lines.append("## Implementation Notes")
        lines.append("")
        for note in spec.implementation_notes:
            lines.append(f"- {note}")
        lines.append("")

    # QA checklist
    lines.append("## QA Checklist")
    lines.append("")
    lines.append("- [ ] All required events firing on page load")
    lines.append("- [ ] CTA clicks tracked with correct properties")
    lines.append("- [ ] Form submissions tracked with form_id")
    lines.append("- [ ] UTM parameters persisted across pages")
    lines.append("- [ ] Events appear in analytics dashboard")
    lines.append("- [ ] No duplicate events on page refresh")
    lines.append("- [ ] Events fire on mobile and desktop")
    lines.append("- [ ] User identification working after signup/login")
    lines.append("")

    return "\n".join(lines)
