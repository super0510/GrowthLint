---
description: "Find specific conversion issues that are costing revenue. Provides dollar estimates and implementation priorities."
user-invocable: true
---

# /find-revenue-leaks

Identify the specific conversion issues costing you revenue, with estimated impact and fix priority.

## Usage
```
/find-revenue-leaks <url>
```

## Instructions

1. Run the scan:
```bash
cd /Users/sdm/Desktop/GrowthLint && python3 -c "import growthlint.cli; growthlint.cli.app()" -- scan "$URL" --format json --fix
```

2. Focus exclusively on **revenue-impacting issues**:
   - Filter to critical and warning severity violations
   - Sort by revenue_weight (highest impact first)
   - Group by category

3. For each revenue leak, provide:
   - **What's happening**: Describe the issue in plain language a marketer understands
   - **Revenue impact**: Estimate conversion rate impact (e.g., "This likely costs you 5-15% of signups")
   - **Implementation time**: Quick win (< 1 hour), Medium (1 day), Heavy lift (1+ week)
   - **Code fix**: If applicable, show the exact code to add/change
   - **CRO recommendation**: Beyond the code fix, what CRO best practice applies here

4. End with a **Revenue Recovery Roadmap**: "Fix these 3 things this week to recover an estimated X% conversion improvement"
