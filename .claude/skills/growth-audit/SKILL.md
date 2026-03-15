---
description: "Run a full growth and conversion audit on a URL or repo. Combines CLI scan with AI qualitative analysis."
user-invocable: true
---

# /growth-audit

Run a comprehensive growth audit combining deterministic scanning with AI qualitative analysis.

## Usage
```
/growth-audit <url-or-directory>
```

## Instructions

1. Run the GrowthLint CLI scan:
```bash
cd /Users/sdm/Desktop/GrowthLint && python3 -c "import growthlint.cli; growthlint.cli.app()" -- scan "$URL" --format json --fix
```

2. Parse the JSON output and analyze the results.

3. Provide a **qualitative AI analysis** that goes beyond the CLI output:

   a. **Page Psychology Assessment**: Evaluate the visitor's emotional journey. Is the value proposition clear within 5 seconds? Does the page build trust before asking for commitment? Is there a logical visual hierarchy guiding the eye?

   b. **Message-Market Fit**: Does the H1 speak to the target audience's pain point? Is the language specific enough (avoid "powerful", "innovative", "best-in-class")? Would a first-time visitor understand what this product does?

   c. **Conversion Architecture**: Is the CTA above the fold? Is there a clear primary action vs. secondary actions? Does the page reduce friction and anxiety at the right moments?

   d. **Prioritized Action Items**: Rank the top 5 fixes by estimated revenue impact. For each, explain WHY it matters (not just what to fix) and estimate implementation difficulty (quick win / medium / heavy lift).

4. Format the output as a complete audit report with:
   - Growth Health Score card
   - Critical findings with revenue impact
   - AI qualitative analysis sections
   - Prioritized action plan with implementation guidance
