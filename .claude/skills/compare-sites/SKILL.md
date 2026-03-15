---
description: "Compare your site against a competitor with side-by-side analysis and 'steal this' recommendations."
user-invocable: true
---

# /compare-sites

Compare your site against a competitor and get actionable competitive intelligence.

## Usage
```
/compare-sites <your-url> <competitor-url>
```

## Instructions

1. Run the competitor comparison:
```bash
cd /Users/sdm/Desktop/GrowthLint && python3 -c "import growthlint.cli; growthlint.cli.app()" -- compare "$YOUR_URL" "$COMPETITOR_URL"
```

2. Add **qualitative competitive analysis**:
   - **Messaging comparison**: How does their value proposition compare to yours? Who is more specific? More compelling?
   - **Trust architecture**: Who builds trust better? Compare social proof, security signals, and authority indicators
   - **CTA strategy**: Compare CTA copy, placement, and urgency. Who makes the next step clearer?
   - **Design/UX impressions**: Based on the page structure, who has a cleaner, more focused experience?
   - **"Steal This" list**: 3-5 specific things the competitor does well that could be adapted
   - **Your unique advantages**: Things you do that they don't - double down on these

3. End with a prioritized list of competitive improvements.
