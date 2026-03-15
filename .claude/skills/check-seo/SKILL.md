---
description: "Run a focused SEO audit with content quality analysis and actionable recommendations."
user-invocable: true
---

# /check-seo

Run a focused SEO audit combining technical checks with content quality analysis.

## Usage
```
/check-seo <url>
```

## Instructions

1. Run the SEO-focused scan:
```bash
cd /Users/sdm/Desktop/GrowthLint && python3 -c "import growthlint.cli; growthlint.cli.app()" -- scan "$URL" --categories seo --format json --fix
```

2. Also run schema suggestions:
```bash
cd /Users/sdm/Desktop/GrowthLint && python3 -c "import growthlint.cli; growthlint.cli.app()" -- suggest-schema "$URL"
```

3. Add **AI content quality analysis**:
   - **Title tag quality**: Is it compelling? Does it include a keyword AND create curiosity? Would you click this in search results?
   - **Meta description quality**: Does it sell the click? Does it have a call to action?
   - **H1 effectiveness**: Does it match search intent? Is it specific enough?
   - **Content depth**: Is there enough content for the topic? Are key subtopics covered?
   - **Internal linking opportunities**: Based on the page structure, what internal links could strengthen topical authority?
   - **Schema recommendations**: Which schema types would unlock rich results for this specific content?

4. Provide specific rewrite suggestions for title, meta description, and H1.
