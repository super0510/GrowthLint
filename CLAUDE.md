# GrowthLint

**The ESLint for Growth Marketing** — An open-source CLI + AI skills toolkit that scans repos and live websites for conversion leaks, missing analytics, broken attribution, and SEO issues.

## Architecture

- **Python CLI** (`growthlint/`): Deterministic scanning, YAML-driven rules (45+), scoring (0-100), report generation (markdown/JSON/CSV)
- **Claude Code Skills** (`.claude/skills/`): AI intelligence layer that wraps CLI and adds qualitative analysis (page psychology, message matching, competitor benchmarking)
- **YAML Rules** (`growthlint/data/`): Community-extensible rules across conversion, analytics, attribution, SEO, and platform-specific (Shopify, WordPress, Webflow)

## Key Commands

```bash
growthlint scan <url|dir>              # Scan URL or local repo
growthlint scan <url> --crawl          # Crawl entire site via sitemap
growthlint scan <url> --fix            # Show auto-fix code patches
growthlint check-links <url>           # Find broken links + redirect chains
growthlint check-integrations <url>    # Analytics tool health check
growthlint map-funnel <url>            # Reconstruct conversion funnel
growthlint generate-spec <url>         # Generate analytics tracking plan
growthlint suggest-schema <url>        # Schema markup opportunities + JSON-LD
growthlint compare <url1> <url2>       # Competitor comparison
growthlint snapshot <url> && growthlint diff  # Track score over time
growthlint check-pr <dir>              # CI/CD threshold check
```

## Tech Stack

Python 3.10+, Typer, Pydantic, BeautifulSoup4, requests, PyYAML, Rich, lxml, defusedxml

## Development

```bash
pip install -e .
python -m pytest tests/ -v
```

## Security

- SSRF protection on all outbound HTTP requests (blocks private/internal IPs)
- XXE protection via defusedxml for sitemap parsing
- ReDoS protection with timeout-wrapped regex evaluation
- Snapshot file size limits to prevent DoS

## Rule Categories

- **conversion** (7 rules): CTAs, forms, social proof, trust signals
- **analytics** (5 rules): Analytics tools, event tracking, conversions
- **attribution** (5 rules): FB Pixel, Google Ads, GTM, UTM persistence
- **seo** (11 rules): Title, meta, canonical, OG tags, schema, viewport
- **shopify** (5 rules): Product schema, cart tracking, checkout events
- **wordpress** (5 rules): Script bloat, caching, breadcrumbs
- **webflow** (4 rules): Alt text, form tracking, CMS collections
- **psychology** (3 rules): Above-fold CTA, CTA copy, directional cues
