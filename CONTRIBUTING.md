# Contributing

Thanks for your interest in contributing to GrowthLint! This guide covers adding new rules, improving skills, and writing tests.

## Requesting a Rule

Suggest new rules by [opening an issue](https://github.com/super0510/GrowthLint/issues/new) with the `rule-request` label.

## Adding a New Rule

### 1. Choose the right YAML file

Rules live in `growthlint/data/`. Pick the category:

- `conversion_rules.yaml` - CTAs, forms, social proof, trust signals
- `analytics_rules.yaml` - Analytics tools, event tracking, conversion events
- `attribution_rules.yaml` - UTM, source properties, ad pixels
- `seo_rules.yaml` - Meta tags, headings, schema, images
- `shopify_rules.yaml` / `wordpress_rules.yaml` / `webflow_rules.yaml` - Platform-specific

### 2. Write your rule

Every rule follows this format:

```yaml
- id: my-rule-id
  name: "Human-Readable Rule Name"
  category: conversion          # conversion, analytics, attribution, seo
  severity: warning             # critical, warning, info
  description: "What the violation means in plain language."
  check:
    type: presence              # See check types below
    field: ctas                 # What to check
    text_pattern: "regex here"  # Optional regex
  impact: "Why this matters. Include data if possible."
  fix: "What to do about it. Be specific and actionable."
  revenue_weight: 0.5           # 0.0-1.0, how much this affects revenue
```

### 3. Check types

| Type | What it does | Required fields |
|------|-------------|-----------------|
| `presence` | Violation if element is missing | `field` or `selector`, optional `text_pattern` |
| `absence` | Violation if element is found | `field` or `selector`, optional `text_pattern` |
| `count` | Violation if count is out of range | `field`, `min_count` and/or `max_count` |
| `pattern` | Violation if pattern NOT found in content | `field`, `text_pattern` |
| `attribute` | Violation if attributes are missing | `field` (images, links) |
| `analytics` | Analytics-specific checks | `field` (analytics_tools, event_tracking, conversion_tracking) |
| `meta_quality` | Meta tag length checks | `field` (title_length, description_length), `min_count`, `max_count` |

### 4. Available fields

`ctas`, `h1`, `h2`, `images`, `links`, `forms`, `scripts`, `script_sources`, `schema_markup`, `title`, `description`, `canonical`, `viewport`, `og_tags`, `favicon`, `social_proof`, `trust_signals`, `text_content`, `inline_scripts`

### 5. Test your rule

```bash
# Run all tests
python -m pytest tests/ -v

# Test against a live URL
growthlint scan https://example.com --format json | python -m json.tool
```

## Adding a Claude Code Skill

### 1. Create the skill directory

```bash
mkdir -p .claude/skills/your-skill-name
```

### 2. Create SKILL.md

```yaml
---
description: "When to use this skill. Include trigger phrases."
user-invocable: true
---

# /your-skill-name

What this skill does in one sentence.

## Usage
/your-skill-name <url>

## Instructions

1. Run the CLI command:
(bash command here)

2. Add AI analysis that goes beyond the CLI:
   - What qualitative insight does the AI add?
   - What patterns can AI spot that rules can't?
```

### 3. Skill quality checklist

- [ ] Description clearly explains when to trigger
- [ ] CLI command is correct and tested
- [ ] AI analysis sections add genuine value beyond raw CLI output
- [ ] Instructions are specific and actionable

## Development Setup

```bash
# Clone and install
git clone https://github.com/super0510/GrowthLint.git
cd growthlint
pip install -e ".[dev]"

# Run tests
python -m pytest tests/ -v

# Run linter
ruff check growthlint/

# Test a scan
growthlint scan https://example.com
```

## Project Structure

```
growthlint/
  scanners/       # URL, repo, sitemap, DOM parsing, platform detection
  rules/          # YAML rule loader and evaluation engine
  reporters/      # Markdown, JSON, CSV report generators
  analyzers/      # Dead links, integrations, psychology, competitor, schema
  generators/     # Funnel mapper, analytics spec, patches, growth diff
  data/           # YAML rule files
  utils/          # HTTP, scoring
  cli.py          # Typer CLI (12 commands)
  models.py       # Pydantic data models
  ci.py           # CI/CD threshold checks
tests/
  fixtures/       # Test HTML and project fixtures
.claude/skills/   # Claude Code slash commands
```

## Submitting Your Contribution

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-rule-name`)
3. Make your changes
4. Run `python -m pytest tests/ -v` to verify
5. Submit a pull request

## Questions?

Open an issue if you have questions or need help with your contribution.
