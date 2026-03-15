---
description: "Visualize conversion funnel, identify dead-end pages, and suggest A/B tests for each stage."
user-invocable: true
---

# /map-funnel

Reconstruct and visualize the conversion funnel with dead-end detection and optimization suggestions.

## Usage
```
/map-funnel <url>
```

## Instructions

1. Run the funnel mapper:
```bash
cd /Users/sdm/Desktop/GrowthLint && python3 -c "import growthlint.cli; growthlint.cli.app()" -- map-funnel "$URL"
```

2. Add **AI funnel analysis**:
   - **Funnel flow assessment**: Is the path from awareness to conversion clear and logical? Are there unnecessary steps?
   - **Dead-end remediation**: For each dead-end page, suggest specific CTAs or navigation elements to add
   - **Missing stages**: If key funnel stages are missing (e.g., no pricing page, no social proof page), explain why they matter
   - **A/B test ideas**: For each funnel stage, suggest 2-3 specific A/B tests (e.g., "Test adding a comparison table on pricing page")
   - **Mobile vs Desktop**: Note any funnel differences that might affect mobile users differently
   - **Industry benchmarks**: Reference typical conversion rates for each funnel stage in the relevant industry

3. Present the Mermaid diagram and a prioritized list of funnel improvements.
