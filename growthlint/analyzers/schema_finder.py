"""Schema/rich result opportunity finder."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from growthlint.models import PageData


@dataclass
class SchemaSuggestion:
    """A suggested schema markup for the page."""

    schema_type: str
    confidence: str  # high, medium, low
    reason: str
    json_ld: dict = field(default_factory=dict)


def find_schema_opportunities(page_data: PageData) -> list[SchemaSuggestion]:
    """Detect content types and suggest appropriate schema markup."""
    suggestions = []
    text = page_data.text_content.lower()

    # Check what schemas already exist
    existing_types = set()
    for schema in page_data.schema_markup:
        if "@type" in schema:
            existing_types.add(schema["@type"])

    # Organization / WebSite (always applicable for homepage-like pages)
    if "Organization" not in existing_types:
        suggestions.append(_suggest_organization(page_data))

    # FAQ detection
    if "FAQ" not in existing_types and "FAQPage" not in existing_types:
        faq = _detect_faq(page_data, text)
        if faq:
            suggestions.append(faq)

    # Product detection
    if "Product" not in existing_types:
        product = _detect_product(page_data, text)
        if product:
            suggestions.append(product)

    # Article / Blog Post detection
    if "Article" not in existing_types:
        article = _detect_article(page_data, text)
        if article:
            suggestions.append(article)

    # LocalBusiness detection
    if "LocalBusiness" not in existing_types:
        local = _detect_local_business(page_data, text)
        if local:
            suggestions.append(local)

    # HowTo detection
    if "HowTo" not in existing_types:
        howto = _detect_howto(page_data, text)
        if howto:
            suggestions.append(howto)

    # Review / AggregateRating detection
    if "Review" not in existing_types:
        review = _detect_reviews(page_data, text)
        if review:
            suggestions.append(review)

    # Event detection
    if "Event" not in existing_types:
        event = _detect_event(page_data, text)
        if event:
            suggestions.append(event)

    return suggestions


def _suggest_organization(page_data: PageData) -> SchemaSuggestion:
    name = page_data.meta.title.split(" - ")[0].split(" | ")[0] if page_data.meta.title else "Your Organization"
    url = page_data.url or "https://yoursite.com"
    return SchemaSuggestion(
        schema_type="Organization",
        confidence="high",
        reason="Every site should have Organization schema for branded search results.",
        json_ld={
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": name,
            "url": url,
            "logo": f"{url}/logo.png",
        },
    )


def _detect_faq(page_data: PageData, text: str) -> SchemaSuggestion | None:
    faq_signals = [
        r"frequently\s+asked",
        r"\bfaq\b",
        r"questions?\s+and\s+answers?",
    ]
    if not any(re.search(p, text) for p in faq_signals):
        return None

    # Try to extract Q&A pairs from headings
    questions = []
    h2s = page_data.headings.get("h2", []) + page_data.headings.get("h3", [])
    for h in h2s:
        if "?" in h:
            questions.append({"@type": "Question", "name": h, "acceptedAnswer": {"@type": "Answer", "text": "Your answer here"}})

    if not questions:
        return None

    return SchemaSuggestion(
        schema_type="FAQPage",
        confidence="high",
        reason=f"Detected {len(questions)} FAQ-style questions. FAQ schema enables rich FAQ snippets in Google.",
        json_ld={
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": questions[:10],
        },
    )


def _detect_product(page_data: PageData, text: str) -> SchemaSuggestion | None:
    product_signals = [
        r"\$\d+(\.\d{2})?",
        r"add\s+to\s+cart",
        r"buy\s+now",
        r"price|pricing",
        r"in\s+stock|out\s+of\s+stock",
    ]
    matches = sum(1 for p in product_signals if re.search(p, text))
    if matches < 2:
        return None

    name = page_data.headings.get("h1", ["Product"])[0] if page_data.headings.get("h1") else "Product"
    desc = page_data.meta.description or "Product description"

    return SchemaSuggestion(
        schema_type="Product",
        confidence="medium",
        reason="Price and purchase signals detected. Product schema enables rich results with price and availability.",
        json_ld={
            "@context": "https://schema.org",
            "@type": "Product",
            "name": name,
            "description": desc,
            "offers": {
                "@type": "Offer",
                "price": "0.00",
                "priceCurrency": "USD",
                "availability": "https://schema.org/InStock",
            },
        },
    )


def _detect_article(page_data: PageData, text: str) -> SchemaSuggestion | None:
    article_signals = [
        r"published|posted\s+on|date",
        r"author|by\s+\w+",
        r"read\s+time|min\s+read",
        r"blog|article|post",
    ]
    matches = sum(1 for p in article_signals if re.search(p, text))
    if matches < 2:
        return None

    title = page_data.meta.title or "Article Title"
    desc = page_data.meta.description or ""

    return SchemaSuggestion(
        schema_type="Article",
        confidence="medium",
        reason="Blog/article signals detected. Article schema enables rich results with date and author.",
        json_ld={
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "description": desc,
            "author": {"@type": "Person", "name": "Author Name"},
            "datePublished": "2024-01-01",
        },
    )


def _detect_local_business(page_data: PageData, text: str) -> SchemaSuggestion | None:
    local_signals = [
        r"address|location",
        r"phone|call\s+us|tel:",
        r"hours|open\s+(mon|tue|wed|thu|fri|sat|sun)",
        r"directions|map",
    ]
    matches = sum(1 for p in local_signals if re.search(p, text))
    if matches < 2:
        return None

    return SchemaSuggestion(
        schema_type="LocalBusiness",
        confidence="medium",
        reason="Local business signals detected (address, phone, hours). LocalBusiness schema enables the Knowledge Panel.",
        json_ld={
            "@context": "https://schema.org",
            "@type": "LocalBusiness",
            "name": page_data.meta.title or "Business Name",
            "address": {"@type": "PostalAddress", "streetAddress": "", "addressLocality": "", "addressRegion": "", "postalCode": ""},
            "telephone": "",
        },
    )


def _detect_howto(page_data: PageData, text: str) -> SchemaSuggestion | None:
    howto_signals = [
        r"how\s+to",
        r"step\s+\d|step\s+one|step\s+1",
        r"guide|tutorial|instructions",
    ]
    matches = sum(1 for p in howto_signals if re.search(p, text))
    if matches < 2:
        return None

    return SchemaSuggestion(
        schema_type="HowTo",
        confidence="medium",
        reason="Step-by-step content detected. HowTo schema enables rich step-by-step results in Google.",
        json_ld={
            "@context": "https://schema.org",
            "@type": "HowTo",
            "name": page_data.meta.title or "How To Guide",
            "step": [
                {"@type": "HowToStep", "name": "Step 1", "text": "Description"},
            ],
        },
    )


def _detect_reviews(page_data: PageData, text: str) -> SchemaSuggestion | None:
    review_signals = [
        r"review|testimonial",
        r"\d(\.\d)?\s*\/\s*5|★|star",
        r"rated|rating",
    ]
    matches = sum(1 for p in review_signals if re.search(p, text))
    if matches < 2:
        return None

    return SchemaSuggestion(
        schema_type="AggregateRating",
        confidence="medium",
        reason="Review/rating content detected. Review schema enables star ratings in search results.",
        json_ld={
            "@context": "https://schema.org",
            "@type": "Product",
            "name": page_data.meta.title or "Product",
            "aggregateRating": {
                "@type": "AggregateRating",
                "ratingValue": "4.5",
                "reviewCount": "100",
            },
        },
    )


def _detect_event(page_data: PageData, text: str) -> SchemaSuggestion | None:
    event_signals = [
        r"event|webinar|conference|workshop|meetup",
        r"register|rsvp|tickets?",
        r"date.*time|when.*where",
    ]
    matches = sum(1 for p in event_signals if re.search(p, text))
    if matches < 2:
        return None

    return SchemaSuggestion(
        schema_type="Event",
        confidence="low",
        reason="Event-related content detected. Event schema enables event rich results with date and registration.",
        json_ld={
            "@context": "https://schema.org",
            "@type": "Event",
            "name": page_data.meta.title or "Event",
            "startDate": "2024-01-01T09:00",
            "location": {"@type": "Place", "name": "Venue"},
        },
    )


def format_schema_suggestions(suggestions: list[SchemaSuggestion]) -> str:
    """Format schema suggestions as markdown with JSON-LD code blocks."""
    lines: list[str] = []
    lines.append("# Schema Markup Opportunities")
    lines.append("")
    lines.append(f"**{len(suggestions)} schema opportunities found**")
    lines.append("")

    for s in suggestions:
        icon = {"high": "🟢", "medium": "🟡", "low": "🔵"}.get(s.confidence, "")
        lines.append(f"## {icon} {s.schema_type}")
        lines.append("")
        lines.append(f"**Confidence:** {s.confidence} | **Why:** {s.reason}")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(s.json_ld, indent=2))
        lines.append("```")
        lines.append("")

    return "\n".join(lines)
