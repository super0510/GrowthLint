"""Message consistency and alignment checker."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from growthlint.models import PageData


@dataclass
class MessageIssue:
    """A detected message consistency issue."""

    issue_type: str  # mismatch, weak, missing, inconsistent
    location: str
    description: str
    suggestion: str


@dataclass
class MessageMatchReport:
    """Complete message consistency report."""

    issues: list[MessageIssue] = field(default_factory=list)
    consistency_score: int = 100  # starts at 100, deducted for issues

    @property
    def has_issues(self) -> bool:
        return len(self.issues) > 0


def check_messages(page_data: PageData) -> MessageMatchReport:
    """Check message consistency across page elements."""
    report = MessageMatchReport()

    _check_h1_vs_title(page_data, report)
    _check_cta_vs_value_prop(page_data, report)
    _check_meta_alignment(page_data, report)
    _check_heading_flow(page_data, report)

    # Calculate consistency score
    deduction = len(report.issues) * 15
    report.consistency_score = max(0, 100 - deduction)

    return report


def _check_h1_vs_title(page_data: PageData, report: MessageMatchReport) -> None:
    """Check H1 and title tag alignment."""
    title = page_data.meta.title
    h1_list = page_data.headings.get("h1", [])

    if not title or not h1_list:
        return

    h1 = h1_list[0]

    # Check if title and H1 share meaningful words
    title_words = set(_meaningful_words(title))
    h1_words = set(_meaningful_words(h1))

    if not title_words or not h1_words:
        return

    overlap = title_words & h1_words
    overlap_ratio = len(overlap) / max(len(title_words), len(h1_words))

    if overlap_ratio < 0.2:
        report.issues.append(MessageIssue(
            issue_type="mismatch",
            location="H1 vs Title",
            description=f"H1 ('{h1[:50]}') and title ('{title[:50]}') share very few words. Users who clicked the search result may feel confused.",
            suggestion="Align your H1 and title tag. The H1 can expand on the title but should reinforce the same core message.",
        ))


def _check_cta_vs_value_prop(page_data: PageData, report: MessageMatchReport) -> None:
    """Check CTA text aligns with the page's value proposition."""
    h1_list = page_data.headings.get("h1", [])
    if not h1_list or not page_data.ctas:
        return

    h1 = h1_list[0].lower()

    # Check for generic CTAs that don't relate to the value prop
    generic_ctas = ["learn more", "click here", "submit", "read more", "continue"]
    for cta in page_data.ctas:
        cta_text = cta.text.lower().strip()
        if cta_text in generic_ctas:
            report.issues.append(MessageIssue(
                issue_type="weak",
                location=f"CTA: '{cta.text}'",
                description=f"Generic CTA '{cta.text}' doesn't reinforce the page's value proposition.",
                suggestion=f"Replace with action-specific text that echoes the value prop. Instead of 'Learn More', try something that relates to '{h1[:40]}'.",
            ))


def _check_meta_alignment(page_data: PageData, report: MessageMatchReport) -> None:
    """Check meta description aligns with page content."""
    desc = page_data.meta.description
    h1_list = page_data.headings.get("h1", [])

    if not desc:
        report.issues.append(MessageIssue(
            issue_type="missing",
            location="Meta Description",
            description="No meta description found. Google will auto-generate one from page content.",
            suggestion="Write a compelling meta description (120-160 chars) that reinforces your H1's promise and includes a call to action.",
        ))
        return

    if h1_list:
        h1 = h1_list[0]
        h1_words = set(_meaningful_words(h1))
        desc_words = set(_meaningful_words(desc))

        if h1_words and desc_words:
            overlap = h1_words & desc_words
            if len(overlap) == 0:
                report.issues.append(MessageIssue(
                    issue_type="mismatch",
                    location="Meta Description vs H1",
                    description="Meta description doesn't share any key terms with H1. The search snippet may not match what visitors find on the page.",
                    suggestion="Include key terms from your H1 in the meta description to maintain message consistency from search to landing.",
                ))


def _check_heading_flow(page_data: PageData, report: MessageMatchReport) -> None:
    """Check that heading hierarchy tells a coherent story."""
    h1_list = page_data.headings.get("h1", [])
    h2_list = page_data.headings.get("h2", [])

    if not h1_list or not h2_list:
        return

    # Check for all-caps headings (reads as shouting)
    for h in h2_list:
        if h == h.upper() and len(h) > 5:
            report.issues.append(MessageIssue(
                issue_type="inconsistent",
                location=f"H2: '{h[:50]}'",
                description="All-caps heading reads as aggressive/shouting. May reduce trust.",
                suggestion="Use title case or sentence case for headings.",
            ))
            break  # Only report once


def _meaningful_words(text: str) -> list[str]:
    """Extract meaningful words (skip stop words and short words)."""
    stop_words = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
        "it", "its", "this", "that", "your", "our", "we", "you", "they",
        "how", "what", "why", "when", "where", "which", "who",
    }
    words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
    return [w for w in words if w not in stop_words and len(w) > 2]


def format_message_report(report: MessageMatchReport) -> str:
    """Format message consistency report as markdown."""
    lines: list[str] = []
    lines.append("# Message Consistency Report")
    lines.append("")
    lines.append(f"### Consistency Score: {report.consistency_score}/100")
    lines.append("")

    if not report.issues:
        lines.append("No message consistency issues found. Your page messaging is well-aligned.")
        return "\n".join(lines)

    for issue in report.issues:
        icon = {"mismatch": "🔴", "weak": "🟡", "missing": "🟠", "inconsistent": "🔵"}.get(issue.issue_type, "")
        lines.append(f"### {icon} {issue.location}")
        lines.append("")
        lines.append(f"**Issue:** {issue.description}")
        lines.append("")
        lines.append(f"**Suggestion:** {issue.suggestion}")
        lines.append("")

    return "\n".join(lines)
