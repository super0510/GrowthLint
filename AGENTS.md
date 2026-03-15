# AGENTS.md

Guidelines for AI agents working in this repository.

## Repository Overview

This repository contains **GrowthLint** — a growth marketing linter with both a Python CLI and AI agent skills. The CLI handles deterministic scanning (rules, scoring, reports). The skills layer adds qualitative AI analysis on top.

- **Name**: GrowthLint
- **GitHub**: [super0510/GrowthLint](https://github.com/super0510/GrowthLint)
- **License**: MIT

## Repository Structure

```
growthlint/
├── .claude/
│   └── skills/              # Claude Code skills (10 skills)
│       └── skill-name/
│           └── SKILL.md
├── .claude-plugin/
│   └── marketplace.json     # Claude Code plugin manifest
├── growthlint/              # Python CLI package
│   ├── scanners/            # URL, repo, sitemap, DOM parsing
│   ├── rules/               # YAML rule engine + loader
│   ├── reporters/           # Markdown, JSON, CSV output
│   ├── analyzers/           # Dead links, integrations, psychology, schema
│   ├── generators/          # Funnel maps, analytics specs, patches, diffs
│   ├── data/                # 45+ YAML rules (8 files)
│   ├── cli.py               # Typer CLI entry point
│   ├── models.py            # Pydantic data models
│   └── ci.py                # CI/CD threshold checks
├── tests/                   # 120+ tests
├── examples/                # Sample output files
├── CONTRIBUTING.md
├── LICENSE
└── README.md
```

## Skills

Skills live in `.claude/skills/` and each wraps the Python CLI with AI intelligence:

| Skill | CLI Command | AI Adds |
|-------|-------------|---------|
| growth-audit | `growthlint scan` | Page psychology, prioritized action plan |
| find-revenue-leaks | `growthlint scan` | Dollar estimates, implementation priorities |
| check-seo | `growthlint scan --categories seo` | Content depth analysis, internal linking |
| generate-analytics-spec | `growthlint generate-spec` | Code snippets, QA checklist |
| map-funnel | `growthlint map-funnel` | A/B test ideas, benchmarks |
| compare-sites | `growthlint compare` | Qualitative trust/messaging comparison |
| check-integrations | `growthlint check-integrations` | Conflict analysis, stack recommendations |
| find-dead-links | `growthlint check-links` | Pattern detection, SEO impact |
| suggest-schema | `growthlint suggest-schema` | Complete JSON-LD, SERP preview |
| growth-diff | `growthlint diff` | Velocity assessment, trajectory analysis |

## Development

```bash
pip install -e .
python -m pytest tests/ -v
```

## Rules

Rules are YAML files in `growthlint/data/`. Each rule has:
- `id`, `name`, `category`, `severity` (critical/warning/info)
- `check` block with `type` (presence/absence/count/pattern/attribute/analytics/meta_quality)
- `impact` description and `fix` recommendation
- `revenue_weight` (0.0-1.0) for scoring

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full rule writing guide.

## Agent Compatibility

This repository works with any agent that can:
1. Run Python CLI commands via shell
2. Read SKILL.md files for skill instructions

Skills are in standard markdown format compatible with Claude Code, Cursor, Windsurf, and any agent supporting the skills pattern.
