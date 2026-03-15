"""JSON report generator for GrowthLint."""

from __future__ import annotations

import json

from growthlint.models import AuditReport


def generate_json(report: AuditReport, indent: int = 2) -> str:
    """Generate a JSON audit report."""
    return report.model_dump_json(indent=indent)
