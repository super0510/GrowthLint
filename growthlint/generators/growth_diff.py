"""Growth diff - snapshot and temporal tracking."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from growthlint.models import AuditReport, RuleViolation


SNAPSHOT_DIR = Path(".growthlint/snapshots")
MAX_SNAPSHOT_SIZE = 10 * 1024 * 1024  # 10 MB


@dataclass
class DiffResult:
    """Result of comparing two snapshots."""

    old_date: str
    new_date: str
    score_delta: int = 0
    old_score: int = 0
    new_score: int = 0
    new_violations: list[str] = field(default_factory=list)
    fixed_violations: list[str] = field(default_factory=list)
    category_deltas: dict[str, int] = field(default_factory=dict)


def save_snapshot(report: AuditReport, directory: Path | None = None) -> Path:
    """Save a timestamped snapshot of the audit report."""
    snap_dir = directory or SNAPSHOT_DIR
    snap_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"snapshot_{timestamp}.json"
    filepath = snap_dir / filename

    filepath.write_text(report.model_dump_json(indent=2))
    return filepath


def load_snapshots(directory: Path | None = None) -> list[tuple[str, AuditReport]]:
    """Load all snapshots, sorted by date (oldest first)."""
    snap_dir = directory or SNAPSHOT_DIR
    if not snap_dir.exists():
        return []

    snapshots = []
    for path in sorted(snap_dir.glob("snapshot_*.json")):
        try:
            if path.stat().st_size > MAX_SNAPSHOT_SIZE:
                continue
            data = json.loads(path.read_text())
            report = AuditReport(**data)
            snapshots.append((path.stem, report))
        except Exception:
            continue

    return snapshots


def diff_snapshots(old: AuditReport, new: AuditReport) -> DiffResult:
    """Compare two audit snapshots."""
    old_ids = {v.rule_id for v in old.violations}
    new_ids = {v.rule_id for v in new.violations}

    new_violations = []
    for v in new.violations:
        if v.rule_id not in old_ids:
            new_violations.append(f"{v.rule_name} ({v.severity})")

    fixed_violations = []
    for v in old.violations:
        if v.rule_id not in new_ids:
            fixed_violations.append(f"{v.rule_name} ({v.severity})")

    # Category deltas
    old_cats = old.score.category_scores
    new_cats = new.score.category_scores
    all_cats = set(old_cats.keys()) | set(new_cats.keys())
    category_deltas = {}
    for cat in all_cats:
        old_val = old_cats.get(cat, 100)
        new_val = new_cats.get(cat, 100)
        if old_val != new_val:
            category_deltas[cat] = new_val - old_val

    return DiffResult(
        old_date=old.scan_date,
        new_date=new.scan_date,
        score_delta=new.score.score - old.score.score,
        old_score=old.score.score,
        new_score=new.score.score,
        new_violations=new_violations,
        fixed_violations=fixed_violations,
        category_deltas=category_deltas,
    )


def format_diff(diff: DiffResult) -> str:
    """Format diff as markdown."""
    lines: list[str] = []
    lines.append("# Growth Diff Report")
    lines.append("")
    lines.append(f"**Period:** {diff.old_date} → {diff.new_date}")
    lines.append("")

    # Score delta
    arrow = "↑" if diff.score_delta > 0 else "↓" if diff.score_delta < 0 else "→"
    color_word = "improved" if diff.score_delta > 0 else "declined" if diff.score_delta < 0 else "unchanged"
    lines.append(f"## Score: {diff.old_score} → {diff.new_score} ({arrow} {abs(diff.score_delta)} points, {color_word})")
    lines.append("")

    if diff.fixed_violations:
        lines.append("## Fixed Issues")
        lines.append("")
        for v in diff.fixed_violations:
            lines.append(f"- {v}")
        lines.append("")

    if diff.new_violations:
        lines.append("## New Issues")
        lines.append("")
        for v in diff.new_violations:
            lines.append(f"- {v}")
        lines.append("")

    if diff.category_deltas:
        lines.append("## Category Changes")
        lines.append("")
        lines.append("| Category | Change |")
        lines.append("|----------|--------|")
        for cat, delta in sorted(diff.category_deltas.items()):
            arrow = "↑" if delta > 0 else "↓"
            lines.append(f"| {cat.title()} | {arrow} {abs(delta)} |")
        lines.append("")

    return "\n".join(lines)
