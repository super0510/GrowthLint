"""Core data models for GrowthLint."""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class SeverityLevel(str, Enum):
    critical = "critical"
    warning = "warning"
    info = "info"


class Platform(str, Enum):
    nextjs = "nextjs"
    react = "react"
    astro = "astro"
    wordpress = "wordpress"
    shopify = "shopify"
    webflow = "webflow"
    static = "static"
    unknown = "unknown"


class PageElement(BaseModel):
    """A detected element on a page (CTA, form, image, etc.)."""

    tag: str = ""
    text: str = ""
    href: str = ""
    attributes: dict[str, str] = Field(default_factory=dict)


class FormData(BaseModel):
    """Extracted form information."""

    action: str = ""
    method: str = ""
    fields: list[str] = Field(default_factory=list)
    field_count: int = 0
    has_hidden_fields: bool = False
    field_types: list[str] = Field(default_factory=list)


class MetaData(BaseModel):
    """Page metadata."""

    title: str = ""
    description: str = ""
    canonical: str = ""
    viewport: str = ""
    robots: str = ""
    og_title: str = ""
    og_description: str = ""
    og_image: str = ""
    og_type: str = ""
    favicon: str = ""


class PageData(BaseModel):
    """Structured data extracted from a single page."""

    url: str = ""
    file_path: str = ""
    html_length: int = 0
    meta: MetaData = Field(default_factory=MetaData)
    headings: dict[str, list[str]] = Field(default_factory=dict)  # h1: [...], h2: [...]
    links: list[PageElement] = Field(default_factory=list)
    internal_links: list[str] = Field(default_factory=list)
    external_links: list[str] = Field(default_factory=list)
    images: list[PageElement] = Field(default_factory=list)
    forms: list[FormData] = Field(default_factory=list)
    ctas: list[PageElement] = Field(default_factory=list)
    scripts: list[str] = Field(default_factory=list)
    script_sources: list[str] = Field(default_factory=list)
    inline_scripts: list[str] = Field(default_factory=list)
    schema_markup: list[dict] = Field(default_factory=list)
    text_content: str = ""


class RuleCheck(BaseModel):
    """Definition of what a rule checks."""

    type: str  # presence, absence, pattern, count, attribute
    selector: str = ""
    text_pattern: str = ""
    field: str = ""
    min_count: int | None = None
    max_count: int | None = None
    attribute: str = ""
    attribute_pattern: str = ""


class RuleDefinition(BaseModel):
    """A single lint rule loaded from YAML."""

    id: str
    name: str
    category: str
    severity: SeverityLevel
    description: str = ""
    check: RuleCheck
    impact: str = ""
    fix: str = ""
    revenue_weight: float = 0.5
    platforms: list[str] = Field(default_factory=list)  # empty = all platforms


class RuleViolation(BaseModel):
    """A rule violation found during scanning."""

    rule_id: str
    rule_name: str
    category: str
    severity: SeverityLevel
    description: str = ""
    impact: str = ""
    fix: str = ""
    revenue_weight: float = 0.5
    page_url: str = ""
    details: str = ""


class GrowthScore(BaseModel):
    """Overall growth health score."""

    score: int = 100  # 0-100
    grade: str = "A"
    total_violations: int = 0
    critical_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    revenue_leak_estimate: str = ""
    category_scores: dict[str, int] = Field(default_factory=dict)


class AuditReport(BaseModel):
    """Complete audit report."""

    target: str
    scan_date: str = ""
    platform: str = "unknown"
    pages_scanned: int = 1
    score: GrowthScore = Field(default_factory=GrowthScore)
    violations: list[RuleViolation] = Field(default_factory=list)
    page_data: list[PageData] = Field(default_factory=list)
