"""YAML rule loader for GrowthLint."""

from __future__ import annotations

from pathlib import Path

import yaml

from growthlint.config import DATA_DIR
from growthlint.models import RuleCheck, RuleDefinition, SeverityLevel


def load_rules(categories: list[str] | None = None, platform: str = "") -> list[RuleDefinition]:
    """Load rules from YAML files in the data directory.

    Args:
        categories: Optional list of categories to load (e.g., ["conversion", "seo"]).
                    If None, loads all categories.
        platform: Optional platform filter. Rules with a non-empty platforms list
                  will only be included if platform matches.
    """
    rules: list[RuleDefinition] = []
    yaml_files = sorted(DATA_DIR.glob("*_rules.yaml"))

    for path in yaml_files:
        category_name = path.stem.replace("_rules", "")
        if categories and category_name not in categories:
            continue
        rules.extend(_load_file(path, platform))

    return rules


def _load_file(path: Path, platform: str = "") -> list[RuleDefinition]:
    """Load rules from a single YAML file."""
    with open(path) as f:
        data = yaml.safe_load(f)

    if not data or "rules" not in data:
        return []

    rules = []
    for raw in data["rules"]:
        rule = RuleDefinition(
            id=raw["id"],
            name=raw["name"],
            category=raw["category"],
            severity=SeverityLevel(raw["severity"]),
            description=raw.get("description", ""),
            check=RuleCheck(**raw["check"]),
            impact=raw.get("impact", ""),
            fix=raw.get("fix", ""),
            revenue_weight=raw.get("revenue_weight", 0.5),
            platforms=raw.get("platforms", []),
        )

        if rule.platforms and platform and platform not in rule.platforms:
            continue

        rules.append(rule)

    return rules
