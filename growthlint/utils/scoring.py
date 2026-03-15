"""Scoring system for GrowthLint."""

from __future__ import annotations

from growthlint.config import SEVERITY_WEIGHTS
from growthlint.models import GrowthScore, RuleViolation


def calculate_score(violations: list[RuleViolation]) -> GrowthScore:
    """Calculate the growth health score from violations."""
    critical_count = sum(1 for v in violations if v.severity == "critical")
    warning_count = sum(1 for v in violations if v.severity == "warning")
    info_count = sum(1 for v in violations if v.severity == "info")

    raw_deduction = sum(
        SEVERITY_WEIGHTS.get(v.severity, 1) * v.revenue_weight for v in violations
    )
    score = max(0, int(100 - raw_deduction))

    grade = _score_to_grade(score)
    revenue_estimate = _estimate_revenue_leak(violations)
    category_scores = _category_scores(violations)

    return GrowthScore(
        score=score,
        grade=grade,
        total_violations=len(violations),
        critical_count=critical_count,
        warning_count=warning_count,
        info_count=info_count,
        revenue_leak_estimate=revenue_estimate,
        category_scores=category_scores,
    )


def _score_to_grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B+"
    if score >= 70:
        return "B"
    if score >= 60:
        return "C+"
    if score >= 50:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def _estimate_revenue_leak(violations: list[RuleViolation]) -> str:
    """Estimate potential conversion improvement range."""
    total_weight = sum(v.revenue_weight for v in violations if v.severity in ("critical", "warning"))
    if total_weight == 0:
        return "Minimal"

    low = int(total_weight * 3)
    high = int(total_weight * 7)
    low = min(low, 45)
    high = min(high, 60)

    if low == high:
        return f"~{low}% potential conversion improvement"
    return f"{low}-{high}% potential conversion improvement"


def _category_scores(violations: list[RuleViolation]) -> dict[str, int]:
    """Calculate per-category scores (each starts at 100)."""
    categories: dict[str, float] = {}
    for v in violations:
        cat = v.category
        if cat not in categories:
            categories[cat] = 0.0
        categories[cat] += SEVERITY_WEIGHTS.get(v.severity, 1) * v.revenue_weight

    return {cat: max(0, int(100 - deduction)) for cat, deduction in categories.items()}
