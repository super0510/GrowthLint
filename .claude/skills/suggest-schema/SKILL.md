---
description: "Find schema markup opportunities with ready-to-use JSON-LD and Google SERP previews."
user-invocable: true
---

# /suggest-schema

Discover schema markup opportunities and get ready-to-use JSON-LD with real values from your page.

## Usage
```
/suggest-schema <url>
```

## Instructions

1. Run the schema finder:
```bash
cd /Users/sdm/Desktop/GrowthLint && python3 -c "import growthlint.cli; growthlint.cli.app()" -- suggest-schema "$URL"
```

2. Add **AI enhancements**:
   - **Populate with real values**: Take the JSON-LD templates and fill them with actual content extracted from the page (real product names, real prices, real FAQs, etc.)
   - **Google SERP preview**: Describe how the rich result would look in Google search with this schema
   - **Priority ranking**: Which schemas will have the biggest search visibility impact for this specific page?
   - **Implementation guide**: For each schema, explain where to add the JSON-LD and how to validate it (Google Rich Results Test)
   - **Additional schema types**: Suggest any schemas the CLI missed based on deeper content analysis

3. Output complete, production-ready JSON-LD blocks that can be copy-pasted directly into the page.
