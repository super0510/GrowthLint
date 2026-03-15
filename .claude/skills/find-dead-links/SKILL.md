---
description: "Find broken links and redirect chains with SEO impact assessment and pattern detection."
user-invocable: true
---

# /find-dead-links

Audit a page for broken links and redirect chains with impact analysis.

## Usage
```
/find-dead-links <url>
```

## Instructions

1. Run the link checker:
```bash
cd /Users/sdm/Desktop/GrowthLint && python3 -c "import growthlint.cli; growthlint.cli.app()" -- check-links "$URL"
```

2. Add **AI analysis**:
   - **Pattern detection**: Are broken links clustered? (e.g., all from a migration, all to a deprecated domain)
   - **SEO impact estimate**: Which broken links are most damaging for SEO? (links in main nav vs footer)
   - **User experience impact**: Which broken links are in the critical user path?
   - **Fix priority**: Rank broken links by importance (CTA links > nav links > footer links > sidebar links)
   - **Redirect optimization**: For long chains, suggest the direct URL to use instead

3. Provide a prioritized fix list with copy-pasteable redirects or URL replacements.
