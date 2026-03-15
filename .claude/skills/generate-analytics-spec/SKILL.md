---
description: "Generate a complete analytics tracking plan with event taxonomy, code snippets, and QA checklist."
user-invocable: true
---

# /generate-analytics-spec

Generate a complete analytics tracking plan tailored to your site's detected pages and interactions.

## Usage
```
/generate-analytics-spec <url>
```

## Instructions

1. Run the analytics spec generator:
```bash
cd /Users/sdm/Desktop/GrowthLint && python3 -c "import growthlint.cli; growthlint.cli.app()" -- generate-spec "$URL"
```

2. Also check current integration health:
```bash
cd /Users/sdm/Desktop/GrowthLint && python3 -c "import growthlint.cli; growthlint.cli.app()" -- check-integrations "$URL"
```

3. Enhance the spec with **AI-powered additions**:
   - **Implementation code snippets**: For each event, provide the exact code for the detected analytics tool (GA4 gtag, Segment analytics.track, PostHog posthog.capture, etc.)
   - **Dashboard suggestions**: What dashboards should be created? What metrics to track on each?
   - **Funnel definition**: Based on the detected pages, define the conversion funnel stages and which events mark each transition
   - **Alert recommendations**: What anomaly alerts should be set up? (e.g., "Alert if signup rate drops 20% day-over-day")

4. Output as a complete, copy-pasteable tracking plan document.
