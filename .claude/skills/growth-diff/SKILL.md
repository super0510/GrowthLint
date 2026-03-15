---
description: "Track growth health over time with snapshots and velocity analysis."
user-invocable: true
---

# /growth-diff

Track your growth health score over time and analyze improvement velocity.

## Usage
```
/growth-diff <url>
```

## Instructions

1. Take a new snapshot:
```bash
cd /Users/sdm/Desktop/GrowthLint && python3 -c "import growthlint.cli; growthlint.cli.app()" -- snapshot "$URL"
```

2. Check if previous snapshots exist and show the diff:
```bash
cd /Users/sdm/Desktop/GrowthLint && python3 -c "import growthlint.cli; growthlint.cli.app()" -- diff
```

3. Add **AI trajectory analysis**:
   - **Growth velocity**: Are scores improving, declining, or stagnant? What's the trend?
   - **What improved and why**: For fixed violations, explain the positive impact
   - **New regressions**: For new violations, explain urgency and impact
   - **Next focus area**: Based on the trajectory, recommend what to focus on next
   - **Milestone tracking**: "At this rate, you'll reach a B+ score in approximately X sprints"

4. If no previous snapshots exist, explain the snapshot/diff workflow and take the first snapshot.
