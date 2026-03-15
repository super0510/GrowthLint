"""Funnel reconstruction from page structure and internal links."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

from growthlint.models import PageData


@dataclass
class FunnelStage:
    """A single stage in the detected funnel."""

    name: str
    page_type: str  # landing, product, pricing, signup, checkout, thank_you, blog, other
    url: str = ""
    file_path: str = ""
    has_cta: bool = False
    cta_targets: list[str] = field(default_factory=list)
    links_to: list[str] = field(default_factory=list)
    is_dead_end: bool = False


@dataclass
class FunnelMap:
    """Complete funnel map for a site."""

    stages: list[FunnelStage] = field(default_factory=list)
    dead_ends: list[FunnelStage] = field(default_factory=list)
    missing_stages: list[str] = field(default_factory=list)

    @property
    def stage_count(self) -> int:
        return len(self.stages)


# Page type detection patterns
PAGE_TYPE_PATTERNS = {
    "landing": [r"^/$", r"/home", r"/landing", r"index\.(html|php)$"],
    "product": [r"/product", r"/item", r"/shop/", r"/store/"],
    "pricing": [r"/pricing", r"/plans", r"/packages"],
    "signup": [r"/sign-?up", r"/register", r"/create-account", r"/onboard"],
    "login": [r"/log-?in", r"/sign-?in", r"/auth"],
    "checkout": [r"/checkout", r"/cart", r"/order", r"/payment"],
    "thank_you": [r"/thank", r"/success", r"/confirm", r"/welcome"],
    "blog": [r"/blog", r"/articles?", r"/posts?", r"/news"],
    "about": [r"/about", r"/team", r"/story"],
    "contact": [r"/contact", r"/support", r"/help"],
    "demo": [r"/demo", r"/book", r"/schedule", r"/calendar"],
}


def map_funnel(pages: list[PageData]) -> FunnelMap:
    """Reconstruct the conversion funnel from page data."""
    stages: list[FunnelStage] = []

    for page in pages:
        identifier = page.url or page.file_path
        page_type = _classify_page(identifier, page)

        cta_targets = []
        for cta in page.ctas:
            if cta.href:
                cta_targets.append(cta.href)

        links_to = page.internal_links[:20]

        stage = FunnelStage(
            name=_stage_name(page_type, page),
            page_type=page_type,
            url=page.url,
            file_path=page.file_path,
            has_cta=len(page.ctas) > 0,
            cta_targets=cta_targets,
            links_to=links_to,
            is_dead_end=len(page.ctas) == 0 and len(page.internal_links) <= 2,
        )
        stages.append(stage)

    # Identify dead ends (pages with no CTAs and few internal links)
    dead_ends = [s for s in stages if s.is_dead_end and s.page_type != "thank_you"]

    # Identify missing stages
    found_types = {s.page_type for s in stages}
    ideal_funnel = ["landing", "product", "pricing", "signup", "thank_you"]
    missing = [stage for stage in ideal_funnel if stage not in found_types]

    return FunnelMap(
        stages=stages,
        dead_ends=dead_ends,
        missing_stages=missing,
    )


def _classify_page(identifier: str, page: PageData) -> str:
    """Classify a page into a funnel stage type."""
    path = urlparse(identifier).path if identifier.startswith("http") else identifier

    for page_type, patterns in PAGE_TYPE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, path, re.IGNORECASE):
                return page_type

    # Heuristic classification from content
    text = page.text_content.lower()
    if page.forms and any("email" in f for form in page.forms for f in form.fields):
        return "signup"
    if "pricing" in text[:500] or "per month" in text[:500]:
        return "pricing"

    return "other"


def _stage_name(page_type: str, page: PageData) -> str:
    """Generate a human-readable name for a funnel stage."""
    h1 = page.headings.get("h1", [""])[0] if page.headings.get("h1") else ""
    if h1:
        return h1[:60]
    if page.meta.title:
        return page.meta.title[:60]
    return page_type.replace("_", " ").title()


def format_funnel_map(funnel: FunnelMap) -> str:
    """Format the funnel map as markdown with a Mermaid diagram."""
    lines: list[str] = []
    lines.append("# Funnel Map")
    lines.append("")

    # Mermaid diagram
    lines.append("```mermaid")
    lines.append("graph TD")

    for i, stage in enumerate(funnel.stages):
        node_id = f"S{i}"
        label = stage.name.replace('"', "'")
        style = ":::dead" if stage.is_dead_end else ""
        lines.append(f'    {node_id}["{label}<br/><small>{stage.page_type}</small>"]{style}')

    # Add edges based on CTA targets and internal links
    stage_urls = {s.url or s.file_path: f"S{i}" for i, s in enumerate(funnel.stages)}
    for i, stage in enumerate(funnel.stages):
        for target in stage.cta_targets[:3]:
            if target in stage_urls:
                lines.append(f"    S{i} -->|CTA| {stage_urls[target]}")

    lines.append("")
    lines.append("    classDef dead fill:#ff6b6b,stroke:#c92a2a,color:white")
    lines.append("```")
    lines.append("")

    # Summary
    lines.append(f"**Total pages:** {funnel.stage_count}")
    lines.append("")

    if funnel.dead_ends:
        lines.append("## Dead-End Pages")
        lines.append("")
        lines.append("These pages have no clear next step for the visitor:")
        lines.append("")
        for de in funnel.dead_ends:
            loc = de.url or de.file_path
            lines.append(f"- **{de.name}** ({loc}) - No CTA, limited navigation")
        lines.append("")

    if funnel.missing_stages:
        lines.append("## Missing Funnel Stages")
        lines.append("")
        lines.append("Your funnel appears to be missing these critical stages:")
        lines.append("")
        for stage in funnel.missing_stages:
            lines.append(f"- **{stage.replace('_', ' ').title()}** page")
        lines.append("")

    return "\n".join(lines)
