# GrowthLint

**The ESLint for Growth Marketing** - An open-source CLI tool that scans repos and live websites for conversion leaks, missing analytics, broken attribution, and SEO issues.

## Architecture

- **Python CLI** (`growthlint/`): Deterministic scanning, YAML-driven rules, scoring, report generation
- **Claude Code Skills** (`.claude/skills/`): AI intelligence layer that wraps CLI + adds qualitative analysis
- **YAML Rules** (`growthlint/data/`): Community-extensible rules across conversion, analytics, attribution, SEO

## Key Commands

```bash
growthlint scan <url>              # Scan a live URL
growthlint scan <dir>              # Scan a local repo
growthlint scan <url> --crawl      # Crawl entire site via sitemap
growthlint scan <url> --fix        # Show code patches
growthlint check-links <url>       # Find broken links
growthlint check-integrations <url> # Analytics health check
growthlint map-funnel <url>        # Reconstruct conversion funnel
growthlint generate-spec <url>     # Generate analytics tracking plan
growthlint suggest-schema <url>    # Find schema markup opportunities
growthlint compare <url1> <url2>   # Competitor comparison
growthlint snapshot <url>          # Save point-in-time snapshot
growthlint diff                    # Compare latest snapshots
growthlint check-pr <dir>          # CI/CD threshold check
```

## Tech Stack

Python 3.10+, Typer, Pydantic, BeautifulSoup4, requests, PyYAML, Rich, lxml

## Development

```bash
pip install -e .
python -m pytest tests/ -v
```

## Rule Categories

- **conversion**: CTAs, forms, social proof, trust signals, headings
- **analytics**: Analytics tools, event tracking, conversion tracking
- **attribution**: FB Pixel, Google Ads, GTM, UTM persistence
- **seo**: Title, meta, canonical, OG tags, schema, viewport, images
- **Platform-specific**: Shopify, WordPress, Webflow rules
