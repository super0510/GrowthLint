# Growth Linting Skills for Claude Code and AI Agents

Scan any website or repo for conversion leaks, missing analytics, broken attribution, and SEO issues. Built for technical marketers, growth engineers, and founders who want AI agents to help find where their site is losing revenue.

GrowthLint is an open-source CLI + AI skills toolkit. The **Python CLI** does deterministic scanning against 45+ rules. The **Claude Code skills** layer adds qualitative AI analysis — page psychology, message matching, competitor benchmarking — that rules-based scanning alone cannot provide. Works with Claude Code, Cursor, Windsurf, and any agent that supports skills.

**Contributions welcome!** Found a way to improve a rule or have a new one to add? [Open a PR](#contributing).

Run into a problem or have a question? [Open an issue](https://github.com/super0510/GrowthLint/issues).

## What is GrowthLint?

GrowthLint is a linter for your marketing site. The same way ESLint catches code quality issues before they ship, GrowthLint catches growth issues before they cost you revenue. It scans your pages against 45+ rules across conversion, analytics, attribution, and SEO, then scores your site and tells you exactly what to fix.

## How the CLI and Skills Work Together

The Python CLI handles deterministic scanning, rule evaluation, and scoring. The Claude Code skills layer orchestrates the CLI and adds qualitative AI analysis (page psychology, message matching, competitor benchmarking) that rules-based scanning cannot provide.

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

Skills reference each other and build on shared CLI data. The `/growth-audit` skill is the most comprehensive, combining scan results with page psychology, message consistency, and prioritized action items.

## Available Skills

| Skill | Description |
|-------|-------------|
| [growth-audit](.claude/skills/growth-audit/) | Full growth and conversion audit. Combines CLI scan with AI page psychology, message-market fit analysis, and prioritized... |
| [find-revenue-leaks](.claude/skills/find-revenue-leaks/) | Find the specific conversion issues costing you revenue. Provides dollar estimates, implementation time, and code fixes... |
| [check-seo](.claude/skills/check-seo/) | Focused SEO audit with content depth analysis, title and meta quality scoring, internal linking opportunities, and... |
| [generate-analytics-spec](.claude/skills/generate-analytics-spec/) | Generate a complete analytics tracking plan from your pages. Outputs event taxonomy, implementation code for your detected... |
| [map-funnel](.claude/skills/map-funnel/) | Reconstruct and visualize your conversion funnel from page links. Identifies dead-end pages, missing stages, and suggests... |
| [compare-sites](.claude/skills/compare-sites/) | Side-by-side competitor comparison. Scores, analytics stack, schema, CTAs, trust signals, and a "steal this" action list... |
| [check-integrations](.claude/skills/check-integrations/) | Analytics tool health check. Detects GA4, GTM, Segment, PostHog, Mixpanel, Hotjar, FB Pixel, Clarity, Amplitude, and 2... |
| [find-dead-links](.claude/skills/find-dead-links/) | Concurrent broken link auditor with redirect chain detection. Finds 404s, long redirect chains, and pattern analysis for... |
| [suggest-schema](.claude/skills/suggest-schema/) | Find schema markup opportunities with ready-to-use JSON-LD populated with real values from your page. Includes Google... |
| [growth-diff](.claude/skills/growth-diff/) | Track your growth health score over time. Take snapshots, compare them, and get AI velocity analysis with trajectory... |

## Installation

### Option 1: pip install (Recommended)

```bash
pip install growthlint
```

### Option 2: Claude Code Plugin

Install via Claude Code's plugin system:

```bash
/plugin install growthlint
```

### Option 3: Clone and install

Get both the CLI and all 10 Claude Code skills:

```bash
git clone https://github.com/super0510/GrowthLint.git
cd growthlint
pip install -e .
```

Skills are automatically available in Claude Code via the `.claude/skills/` directory.

### Option 4: Git Submodule

Add as a submodule for easy updates:

```bash
git submodule add https://github.com/super0510/GrowthLint.git .agents/growthlint
pip install -e .agents/growthlint
```

### Option 5: Fork and Customize

1. Fork this repository
2. Add your own rules to `growthlint/data/`
3. Customize skills for your stack
4. Clone your fork into your projects

## Usage

### CLI Commands

Run a scan against any URL or local directory:

```bash
# Scan a live URL
growthlint scan https://yoursite.com

# Scan a local repo (auto-detects Next.js, React, WordPress, Shopify, Webflow)
growthlint scan ./my-project

# Crawl entire site via sitemap
growthlint scan https://yoursite.com --crawl --max-pages 50

# Get JSON or CSV output
growthlint scan https://yoursite.com --format json
growthlint scan https://yoursite.com --format csv --output report.csv

# Get auto-fix code patches
growthlint scan https://yoursite.com --fix
```

### Specialized Commands

```bash
# Find broken links and redirect chains
growthlint check-links https://yoursite.com

# Check analytics tool health (GA4, GTM, Segment, PostHog, etc.)
growthlint check-integrations https://yoursite.com

# Reconstruct your conversion funnel with Mermaid diagram
growthlint map-funnel https://yoursite.com

# Generate analytics tracking plan
growthlint generate-spec https://yoursite.com

# Find schema markup opportunities with ready-to-use JSON-LD
growthlint suggest-schema https://yoursite.com

# Compare your site against a competitor
growthlint compare https://yoursite.com https://competitor.com

# Track growth score over time
growthlint snapshot https://yoursite.com
growthlint diff

# Page psychology and persuasion scoring
growthlint analyze-psychology https://yoursite.com

# Message consistency check
growthlint check-messages https://yoursite.com

# CI/CD threshold check
growthlint check-pr ./my-project --min-score 60

# Reverse-engineer a competitor's entire growth playbook
growthlint harvest https://competitor.com

# Audit tracking compliance (GDPR, CCPA, consent banners)
growthlint consent-audit https://yoursite.com

# Generate a shields.io-style score badge for your README
growthlint badge https://yoursite.com -o growthlint-badge.svg
```

### Claude Code Skills

Once installed, invoke skills directly in Claude Code:

```
/growth-audit https://yoursite.com
→ Full growth audit with AI page psychology and prioritized action plan

/find-revenue-leaks https://yoursite.com
→ Revenue-impacting issues with dollar estimates and implementation priorities

/check-seo https://yoursite.com
→ SEO audit with content depth analysis and internal linking opportunities

/compare-sites https://yoursite.com https://competitor.com
→ Side-by-side comparison with "steal this" action list

/suggest-schema https://yoursite.com
→ Schema opportunities with production-ready JSON-LD
```

## What GrowthLint Detects

### Conversion (7 rules)
- `missing-cta` - No call-to-action found on the page
- `no-above-fold-cta` - CTA not visible without scrolling
- `weak-cta-text` - Generic CTA copy (Learn More, Click Here, Submit)
- `form-friction-high` - Forms with 6+ visible fields
- `no-social-proof` - No testimonials, reviews, or customer counts
- `no-trust-signals` - No guarantees, security badges, or certifications
- `cta-missing-tracking` - CTAs without click event tracking

### Analytics (5 rules)
- `no-analytics` - No analytics tool detected (GA4, Segment, PostHog, etc.)
- `no-event-tracking` - Analytics present but no event tracking
- `no-conversion-tracking` - Analytics without conversion events
- `event-naming-inconsistent` - Mixed event naming conventions
- `no-activation-event` - No user activation event detected

### Attribution (5 rules)
- `no-utm-persistence` - UTM parameters not persisted across pages
- `no-source-properties` - Source properties missing from events
- `no-fb-pixel` - No Meta Pixel detected
- `no-google-ads` - No Google Ads conversion tag
- `no-gtm` - No Google Tag Manager

### SEO (11 rules)
- `missing-title` - No title tag
- `missing-meta-description` - No meta description
- `missing-h1` - No H1 heading
- `multiple-h1` - More than one H1
- `missing-canonical` - No canonical URL
- `missing-og-tags` - Incomplete Open Graph tags
- `images-missing-alt` - Images without alt text
- `no-structured-data` - No schema markup
- `missing-viewport` - No viewport meta tag
- `missing-favicon` - No favicon
- `title-length` / `description-length` - Meta tag length issues

### Platform-Specific
- **Shopify** (5 rules) - Product schema, cart tracking, checkout events, upsell modules
- **WordPress** (5 rules) - Script bloat, caching, breadcrumbs, login exposure
- **Webflow** (4 rules) - Alt text, form tracking, CMS collections

### Psychology (3 rules)
- `no-above-fold-cta` - Primary action not visible on load
- `weak-cta-text` - Generic CTA copy that doesn't convert
- `no-directional-cues` - No visual cues guiding the eye toward CTAs

## Supported Platforms

GrowthLint auto-detects your platform from repo signals (package.json, directory structure) and URL signals (script sources, DOM patterns):

- **React / Next.js / Astro** - Scans JSX/TSX components
- **WordPress** - Scans PHP templates with WP-specific rules
- **Shopify** - Scans Liquid templates with ecommerce rules
- **Webflow** - Detects via CSS patterns with Webflow rules
- **Static sites** - Scans HTML directly

## Scoring

Every scan produces a **Growth Health Score** from 0-100 with a letter grade:

| Grade | Score | Meaning |
|-------|-------|---------|
| A | 90-100 | Excellent growth fundamentals |
| B+ | 80-89 | Strong with minor improvements needed |
| B | 70-79 | Good foundation, several opportunities |
| C+ | 60-69 | Meaningful gaps in growth infrastructure |
| C | 50-59 | Significant issues affecting conversions |
| D | 30-49 | Major growth infrastructure problems |
| F | 0-29 | Critical issues need immediate attention |

Scores are weighted by severity (critical > warning > info) and revenue impact. The report includes an estimated conversion improvement range if issues are fixed.

## CI/CD Integration

Add GrowthLint to your CI pipeline to catch growth regressions on every PR:

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
      - run: pip install -e .
      - run: growthlint check-pr . --min-score 60
```

## Contributing

Found a way to improve a rule? Have a new rule to suggest? PRs and issues welcome!

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on adding rules, writing tests, and improving skills.

## License

[MIT](LICENSE) - Use this however you want.
