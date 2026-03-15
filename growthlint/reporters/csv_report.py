"""CSV report generator for GrowthLint."""

from __future__ import annotations

import csv
import io

from growthlint.models import AuditReport


def generate_csv(report: AuditReport) -> str:
    """Generate a CSV report with one row per violation."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Rule ID",
        "Rule Name",
        "Category",
        "Severity",
        "Page",
        "Impact",
        "Fix",
        "Revenue Weight",
        "Details",
    ])

    # Rows
    for v in report.violations:
        writer.writerow([
            v.rule_id,
            v.rule_name,
            v.category,
            v.severity.value if hasattr(v.severity, "value") else str(v.severity),
            v.page_url,
            v.impact,
            v.fix,
            v.revenue_weight,
            v.details,
        ])

    return output.getvalue()
