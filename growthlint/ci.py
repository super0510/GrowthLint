"""CI/CD integration for GrowthLint."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from growthlint.models import AuditReport, RuleViolation
from growthlint.rules.engine import evaluate_rules
from growthlint.rules.loader import load_rules
from growthlint.scanners.repo_scanner import scan_repo
from growthlint.utils.scoring import calculate_score


@dataclass
class CICheckResult:
    """Result of a CI check."""

    passed: bool = True
    score: int = 100
    grade: str = "A"
    critical_count: int = 0
    total_violations: int = 0
    failures: list[str] = field(default_factory=list)


def check_pr(
    repo_path: str | Path,
    min_score: int = 0,
    max_critical: int = -1,
    fail_on_new_critical: bool = True,
) -> CICheckResult:
    """Run a CI check on a repo directory.

    Args:
        repo_path: Path to the repository.
        min_score: Minimum acceptable score (0 = no minimum).
        max_critical: Maximum critical violations allowed (-1 = unlimited).
        fail_on_new_critical: Fail if any critical violations are found.
    """
    result = CICheckResult()

    pages, platform = scan_repo(repo_path)
    rules = load_rules(platform=platform.value)

    all_violations: list[RuleViolation] = []
    for page in pages:
        violations = evaluate_rules(page, rules)
        for v in violations:
            v.page_url = page.file_path
        all_violations.extend(violations)

    score = calculate_score(all_violations)
    result.score = score.score
    result.grade = score.grade
    result.critical_count = score.critical_count
    result.total_violations = score.total_violations

    # Check thresholds
    if min_score > 0 and score.score < min_score:
        result.passed = False
        result.failures.append(f"Score {score.score} is below minimum {min_score}")

    if max_critical >= 0 and score.critical_count > max_critical:
        result.passed = False
        result.failures.append(f"Found {score.critical_count} critical issues (max allowed: {max_critical})")

    if fail_on_new_critical and score.critical_count > 0:
        critical_names = [v.rule_name for v in all_violations if v.severity == "critical"]
        unique_names = list(dict.fromkeys(critical_names))
        result.passed = False
        result.failures.append(f"Critical issues found: {', '.join(unique_names[:5])}")

    return result
