# GrowthLint — The ESLint for Growth Marketing

Scan any website for conversion leaks, missing analytics, broken attribution, and SEO issues. Reverse-engineer competitor playbooks. Audit GDPR/CCPA compliance. Generate score badges for your README.

Built for growth engineers, technical marketers, and founders who want to stop guessing and start fixing what's actually killing their conversions.

**Open-source CLI + AI skills toolkit.** 45+ deterministic rules. 18 CLI commands. 10 Claude Code skills. Works with Claude Code, Cursor, Windsurf, and any agent that supports skills.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

---

## What Makes GrowthLint Different

Most website auditors check for broken HTML. GrowthLint checks for **broken revenue**.

- **`growthlint harvest`** — Reverse-engineer any competitor's entire growth stack. Tools, CTAs, funnel structure, retargeting pixels, pricing psychology, lead capture — extracted into an actionable playbook you can steal.
- **`growthlint consent-audit`** — The only open-source tool that checks if your tracking fires before consent. Detects 12 CMPs, validates Google Consent Mode v2, finds GDPR/CCPA violations with exact fixes.
- **`growthlint badge`** — Generate a shields.io-style score badge for your README. Like "build passing" but for conversion health.
- **45+ rules** across conversion, analytics, attribution, SEO, and platform-specific (Shopify, WordPress, Webflow)
- **AI skills layer** adds page psychology analysis, message matching, and competitor benchmarking on top of deterministic scanning

---

## Quick Start

```bash
pip install growthlint

# Scan any URL
growthlint scan https://yoursite.com

# Steal a competitor's playbook
growthlint harvest https://competitor.com

# Check if your tracking is GDPR compliant
growthlint consent-audit https://yoursite.com

# Generate a score badge for your README
growthlint badge https://yoursite.com
```

## Installation

```bash
# Option 1: pip (recommended)
pip install growthlint

# Option 2: Clone and install (includes Claude Code skills)
git clone https://github.com/super0510/GrowthLint.git
cd GrowthLint
pip install -e .

# Option 3: Git submodule
git submodule add https://github.com/super0510/GrowthLint.git .agents/growthlint
pip install -e .agents/growthlint
```

Skills are automatically available in Claude Code via the `.claude/skills/` directory.

---

## All Commands

### Core Scanning

```bash
growthlint scan <url|dir>                    # Scan URL or local repo
growthlint scan <url> --crawl --max-pages 50 # Crawl entire site via sitemap
growthlint scan <url> --fix                  # Show auto-fix code patches
growthlint scan <url> --format json          # Output as JSON or CSV
```

### Competitor Intelligence

```bash
growthlint harvest <url>                     # Reverse-engineer growth playbook
growthlint compare <url1> <url2>             # Side-by-side competitor comparison
```

### Compliance & Privacy

```bash
growthlint consent-audit <url>               # GDPR/CCPA tracking compliance audit
```

### Analytics & Attribution

```bash
growthlint check-integrations <url>          # Analytics tool health check
growthlint generate-spec <url>               # Generate analytics tracking plan
```

### SEO & Content

```bash
growthlint check-links <url>                 # Find broken links + redirect chains
growthlint suggest-schema <url>              # Schema markup opportunities + JSON-LD
```

### Conversion Optimization

```bash
growthlint map-funnel <url>                  # Reconstruct conversion funnel
growthlint analyze-psychology <url>          # Page persuasion scoring
growthlint check-messages <url>              # Message consistency check
```

### Tracking & CI/CD

```bash
growthlint snapshot <url>                    # Save point-in-time score
growthlint diff                              # Compare latest snapshots
growthlint check-pr <dir> --min-score 60     # CI/CD threshold check
growthlint badge <url> -o badge.svg          # Generate score badge
```

---

## Feature Highlights

### Harvest — Competitor Growth Playbook Extractor

```bash
growthlint harvest https://competitor.com
```

Reverse-engineers a competitor's entire growth stack from their live site:

- **40+ tools detected** — Analytics (GA4, Mixpanel, PostHog), email (Klaviyo, Mailchimp, HubSpot), chat (Intercom, Drift, Zendesk), retargeting (Meta Pixel, LinkedIn, TikTok, Pinterest)
- **CTA strategy** — Primary/secondary CTAs, above/below fold positioning, copy patterns
- **Social proof audit** — Customer counts, review scores, trust badges, partner logos
- **Pricing psychology** — Free trials, annual discounts, "Most Popular" badges, urgency tactics
- **Funnel map** — Classifies internal links into pricing, signup, blog, docs, demo, careers, etc.
- **Lead capture methods** — Forms, popups (OptinMonster, Sumo), chatbots, newsletter signups
- **"Steal This Playbook"** — Top 10 actionable items you can implement from what they're doing

### Consent Audit — GDPR/CCPA Compliance Scanner

```bash
growthlint consent-audit https://yoursite.com
```

Checks whether your tracking setup is actually compliant:

- **Consent banner detection** — Detects 12 CMPs (OneTrust, CookieBot, TrustArc, Osano, Termly, Iubenda, and more)
- **Pre-consent firing** — The #1 violation: checks if analytics/marketing scripts load BEFORE the consent banner
- **Google Consent Mode v2** — Validates the configuration required since March 2024 for all Google advertising tools
- **Privacy links** — Privacy policy, cookie policy, terms, "Do Not Sell" (CCPA)
- **Reject-all option** — GDPR requires equal prominence for accept and reject
- **Compliance score** — 0-100 with critical/warning/info issues and a fix checklist
- **Script categorization** — Every external script classified as essential, analytics, marketing, or functional

### Badge — Growth Score for Your README

```bash
growthlint badge https://yoursite.com -o growthlint-badge.svg
```

Generate a shields.io-style SVG badge showing your growth health score:

- 3 styles: `flat`, `flat-square`, `for-the-badge`
- Color-coded by grade (green for A, yellow for B, orange for C, red for D/F)
- Add to your README: `![GrowthLint Score](growthlint-badge.svg)`

---

## Claude Code Skills

Once installed, invoke skills directly in Claude Code for AI-powered analysis:

| Skill | Description |
|-------|-------------|
| `/growth-audit` | Full growth audit with AI page psychology and prioritized action plan |
| `/find-revenue-leaks` | Revenue-impacting issues with dollar estimates and code fixes |
| `/check-seo` | SEO audit with content depth analysis and internal linking opportunities |
| `/generate-analytics-spec` | Complete analytics tracking plan with event taxonomy and implementation code |
| `/map-funnel` | Conversion funnel visualization with dead-end detection and A/B test ideas |
| `/compare-sites` | Side-by-side competitor comparison with "steal this" action list |
| `/check-integrations` | Analytics stack health check with conflict detection |
| `/find-dead-links` | Broken link audit with SEO impact assessment |
| `/suggest-schema` | Schema opportunities with ready-to-use JSON-LD and SERP previews |
| `/growth-diff` | Growth tracking with velocity analysis and trajectory forecasting |

---

## What GrowthLint Detects (45+ Rules)

### Conversion (7 rules)
- `missing-cta` - No call-to-action found
- `no-above-fold-cta` - CTA not visible without scrolling
- `weak-cta-text` - Generic CTA copy (Learn More, Submit)
- `form-friction-high` - Forms with 6+ visible fields
- `no-social-proof` - No testimonials, reviews, or customer counts
- `no-trust-signals` - No guarantees, badges, or certifications
- `cta-missing-tracking` - CTAs without click event tracking

### Analytics (5 rules)
- `no-analytics` - No analytics tool detected
- `no-event-tracking` - Analytics present but no events
- `no-conversion-tracking` - No conversion-specific events
- `event-naming-inconsistent` - Mixed naming conventions
- `no-activation-event` - No user activation event

### Attribution (5 rules)
- `no-utm-persistence` - UTM params lost on navigation
- `no-source-properties` - Missing source on events
- `no-fb-pixel` / `no-google-ads` / `no-gtm` - Missing ad pixels

### SEO (11 rules)
- Title, meta description, H1, canonical, OG tags, schema, viewport, favicon, alt text, and length checks

### Platform-Specific
- **Shopify** (5) - Product schema, cart tracking, checkout events, upsells, reviews
- **WordPress** (5) - Script bloat, caching, breadcrumbs, SEO plugin, contact forms
- **Webflow** (4) - Alt text, form tracking, interactions, CMS collections

### Psychology (3 rules)
- Above-fold CTA placement, CTA copy quality, directional cues

---

## Scoring

Every scan produces a **Growth Health Score** from 0-100:

| Grade | Score | Meaning |
|-------|-------|---------|
| A | 90-100 | Excellent growth fundamentals |
| B+ | 80-89 | Strong with minor improvements needed |
| B | 70-79 | Good foundation, several opportunities |
| C+ | 60-69 | Meaningful gaps in growth infrastructure |
| C | 50-59 | Significant issues affecting conversions |
| D | 30-49 | Major growth infrastructure problems |
| F | 0-29 | Critical issues need immediate attention |

Scores are weighted by severity and revenue impact. Reports include estimated conversion improvement ranges.

---

## Architecture

```
                            ┌──────────────────────────────────────┐
                            │         Claude Code Skills           │
                            │      (AI intelligence layer)         │
                            │   /growth-audit  /compare-sites      │
                            │   /check-seo     /find-revenue-leaks │
                            └──────────────────┬───────────────────┘
                                               │
                                         invokes via CLI
                                               │
    ┌──────────────┬───────────────────────────┼───────────────────────────────────────┐
    │              │        Python CLI (growthlint)                                    │
    │              │                                                                   │
    │  Scanners    │  Rules Engine     Reporters      Analyzers       Generators       │
    │  url_scanner │  45+ YAML rules   markdown       dead_links      funnel_mapper    │
    │  repo_scanner│  7 check types    json           integrations    analytics_spec   │
    │  sitemap     │  scoring          csv            psychology      patch_generator   │
    │  dom_parser  │                                  competitor      schema_finder    │
    │  platform_det│                                  message_match   growth_diff      │
    │              │                                  consent_audit   badge_generator  │
    │              │                                  playbook_harv                    │
    └──────────────┴───────────────────────────────────────────────────────────────────┘
```

## Supported Platforms

Auto-detects from repo signals and URL patterns:

- **React / Next.js / Astro** - JSX/TSX component scanning
- **WordPress** - PHP templates with WP-specific rules
- **Shopify** - Liquid templates with ecommerce rules
- **Webflow** - CSS pattern detection with Webflow rules
- **Static sites** - Direct HTML scanning

## CI/CD Integration

```yaml
# .github/workflows/growthlint.yml
name: GrowthLint
on: [pull_request]
jobs:
  growthlint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev]"
      - run: growthlint check-pr . --min-score 60
```

## Contributing

Found a way to improve a rule? Have a new one to add? PRs and issues welcome!

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on adding rules, writing tests, and improving skills.

## License

[MIT](LICENSE) - Use this however you want.
