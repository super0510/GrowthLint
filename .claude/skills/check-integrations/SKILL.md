---
description: "Check analytics tool health, detect conflicts, and get stack recommendations."
user-invocable: true
---

# /check-integrations

Audit your analytics stack for health issues, conflicts, and missing tools.

## Usage
```
/check-integrations <url>
```

## Instructions

1. Run the integration health check:
```bash
cd /Users/sdm/Desktop/GrowthLint && python3 -c "import growthlint.cli; growthlint.cli.app()" -- check-integrations "$URL"
```

2. Add **AI-powered analysis**:
   - **Misconfiguration detection**: Explain each config issue in plain language with fix instructions
   - **Conflict resolution**: For detected conflicts (e.g., double pageviews), provide step-by-step fix
   - **Stack recommendations**: Based on what's detected, suggest complementary tools (e.g., "You have GA4 but no heatmapping - consider Clarity (free)")
   - **Data quality assessment**: Are there signals of data quality issues? (duplicate tracking, missing noscript fallbacks, etc.)
   - **Privacy compliance**: Note any GDPR/CCPA considerations for the detected stack

3. Output a clear integration health report with action items.
