"""CLI entry point for GrowthLint."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from growthlint import __version__

app = typer.Typer(
    name="growthlint",
    help="The ESLint for growth marketing. Scan websites for conversion leaks, missing analytics, broken attribution, and SEO issues.",
    no_args_is_help=True,
)
console = Console()


def version_callback(value: bool) -> None:
    if value:
        console.print(f"GrowthLint v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None, "--version", "-v", callback=version_callback, is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """GrowthLint - Find and fix what's killing your conversions."""


def _is_url(target: str) -> bool:
    """Check if a target looks like a URL rather than a local path."""
    return target.startswith(("http://", "https://", "www.")) or "." in target.split("/")[0] and not Path(target).exists()


@app.command()
def scan(
    target: str = typer.Argument(..., help="URL or local directory to scan"),
    format: str = typer.Option("markdown", "--format", "-f", help="Output format: markdown, json, csv"),
    output: str = typer.Option("", "--output", "-o", help="Output file path (prints to stdout if empty)"),
    categories: str = typer.Option("", "--categories", "-c", help="Comma-separated categories to check (e.g., seo,conversion)"),
    platform: str = typer.Option("", "--platform", "-p", help="Override platform detection (nextjs, react, wordpress, shopify, webflow, astro, static)"),
    crawl: bool = typer.Option(False, "--crawl", help="Crawl entire site via sitemap"),
    max_pages: int = typer.Option(50, "--max-pages", help="Max pages to crawl (used with --crawl)"),
    fix: bool = typer.Option(False, "--fix", help="Generate code patches for fixable issues"),
) -> None:
    """Scan a URL or local repo for growth and conversion issues."""
    from growthlint.models import AuditReport, Platform
    from growthlint.reporters.json_report import generate_json
    from growthlint.reporters.markdown_report import generate_markdown
    from growthlint.rules.engine import evaluate_rules
    from growthlint.rules.loader import load_rules
    from growthlint.utils.scoring import calculate_score

    # Parse platform override
    platform_enum = None
    if platform:
        try:
            platform_enum = Platform(platform.lower())
        except ValueError:
            console.print(f"[red]Unknown platform:[/red] {platform}")
            console.print(f"Valid platforms: {', '.join(p.value for p in Platform)}")
            raise typer.Exit(1)

    # Parse categories
    cat_list = [c.strip() for c in categories.split(",") if c.strip()] if categories else None

    # Auto-detect URL vs directory
    target_path = Path(target)
    is_repo = target_path.is_dir()

    if is_repo:
        _scan_repo(target, target_path, format, output, cat_list, platform_enum, fix)
    elif crawl:
        _scan_crawl(target, format, output, cat_list, platform_enum, max_pages)
    else:
        _scan_url(target, format, output, cat_list, platform_enum, fix)


def _scan_url(
    target: str,
    format: str,
    output: str,
    categories: list[str] | None,
    platform_override: "Platform | None",
    show_fixes: bool = False,
) -> None:
    """Scan a live URL."""
    from growthlint.models import AuditReport, Platform
    from growthlint.reporters.json_report import generate_json
    from growthlint.reporters.markdown_report import generate_markdown
    from growthlint.rules.engine import evaluate_rules
    from growthlint.rules.loader import load_rules
    from growthlint.scanners.platform_detector import detect_platform_from_url
    from growthlint.scanners.url_scanner import scan_url
    from growthlint.utils.scoring import calculate_score

    console.print(Panel(
        f"[bold]GrowthLint v{__version__}[/bold]\n"
        f"Scanning: {target}",
        title="🔍 Growth Audit",
        border_style="cyan",
    ))

    with console.status("[bold cyan]Fetching page...[/bold cyan]"):
        try:
            page_data = scan_url(target)
        except Exception as e:
            console.print(f"[red]Error fetching URL:[/red] {e}")
            raise typer.Exit(1)

    console.print(f"  [green]✓[/green] Fetched {page_data.html_length:,} bytes")

    # Detect platform
    detected_platform = platform_override or detect_platform_from_url(page_data)
    platform_str = detected_platform.value if isinstance(detected_platform, Platform) else str(detected_platform)
    console.print(f"  [green]✓[/green] Platform: {platform_str}")

    # Load rules (base + platform-specific) and evaluate
    with console.status("[bold cyan]Evaluating rules...[/bold cyan]"):
        rules = load_rules(categories=categories, platform=platform_str)
        violations = evaluate_rules(page_data, rules)
        score = calculate_score(violations)

    console.print(f"  [green]✓[/green] Evaluated {len(rules)} rules")
    console.print(f"  [green]✓[/green] Found {len(violations)} issues")
    console.print("")

    _print_score(score)

    report = AuditReport(
        target=target,
        scan_date=datetime.now().strftime("%Y-%m-%d %H:%M"),
        platform=platform_str,
        pages_scanned=1,
        score=score,
        violations=violations,
        page_data=[page_data],
    )

    _output_report(report, format, output)

    if show_fixes:
        from growthlint.generators.patch_generator import format_patches, generate_patches
        patches = generate_patches(violations, page_data)
        if patches:
            console.print("")
            console.print(format_patches(patches))


def _scan_repo(
    target: str,
    target_path: Path,
    format: str,
    output: str,
    categories: list[str] | None,
    platform_override: "Platform | None",
    show_fixes: bool = False,
) -> None:
    """Scan a local repository."""
    from growthlint.models import AuditReport, Platform
    from growthlint.reporters.json_report import generate_json
    from growthlint.reporters.markdown_report import generate_markdown
    from growthlint.rules.engine import evaluate_rules
    from growthlint.rules.loader import load_rules
    from growthlint.scanners.repo_scanner import scan_repo
    from growthlint.utils.scoring import calculate_score

    console.print(Panel(
        f"[bold]GrowthLint v{__version__}[/bold]\n"
        f"Scanning: {target_path.resolve()}",
        title="🔍 Repo Audit",
        border_style="cyan",
    ))

    with console.status("[bold cyan]Scanning repository...[/bold cyan]"):
        try:
            pages, detected_platform = scan_repo(target_path, platform_override)
        except FileNotFoundError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

    platform_str = detected_platform.value
    console.print(f"  [green]✓[/green] Platform: {platform_str}")
    console.print(f"  [green]✓[/green] Scanned {len(pages)} files")

    # Evaluate rules across all pages
    with console.status("[bold cyan]Evaluating rules...[/bold cyan]"):
        rules = load_rules(categories=categories, platform=platform_str)
        all_violations = []
        for page in pages:
            violations = evaluate_rules(page, rules)
            # Tag violations with file path
            for v in violations:
                v.page_url = page.file_path
            all_violations.extend(violations)

        # Deduplicate identical rule violations across files
        seen = set()
        unique_violations = []
        for v in all_violations:
            key = (v.rule_id, v.page_url)
            if key not in seen:
                seen.add(key)
                unique_violations.append(v)

        score = calculate_score(unique_violations)

    console.print(f"  [green]✓[/green] Evaluated {len(rules)} rules")
    console.print(f"  [green]✓[/green] Found {len(unique_violations)} issues across {len(pages)} files")
    console.print("")

    _print_score(score)

    report = AuditReport(
        target=str(target_path.resolve()),
        scan_date=datetime.now().strftime("%Y-%m-%d %H:%M"),
        platform=platform_str,
        pages_scanned=len(pages),
        score=score,
        violations=unique_violations,
        page_data=pages,
    )

    _output_report(report, format, output)


def _scan_crawl(
    target: str,
    format: str,
    output: str,
    categories: list[str] | None,
    platform_override: "Platform | None",
    max_pages: int,
) -> None:
    """Crawl a full site via sitemap."""
    from growthlint.models import AuditReport, Platform
    from growthlint.rules.engine import evaluate_rules
    from growthlint.rules.loader import load_rules
    from growthlint.scanners.platform_detector import detect_platform_from_url
    from growthlint.scanners.sitemap_scanner import crawl_site
    from growthlint.utils.scoring import calculate_score

    console.print(Panel(
        f"[bold]GrowthLint v{__version__}[/bold]\n"
        f"Crawling: {target} (max {max_pages} pages)",
        title="🕷️ Site Crawl",
        border_style="cyan",
    ))

    try:
        pages = crawl_site(target, max_pages=max_pages)
    except Exception as e:
        console.print(f"[red]Error crawling site:[/red] {e}")
        raise typer.Exit(1)

    if not pages:
        console.print("[yellow]No pages found to scan.[/yellow]")
        raise typer.Exit(0)

    console.print(f"  [green]✓[/green] Crawled {len(pages)} pages")

    # Detect platform from first page
    detected_platform = platform_override or detect_platform_from_url(pages[0])
    platform_str = detected_platform.value if isinstance(detected_platform, Platform) else str(detected_platform)
    console.print(f"  [green]✓[/green] Platform: {platform_str}")

    # Evaluate rules across all pages
    with console.status("[bold cyan]Evaluating rules...[/bold cyan]"):
        rules = load_rules(categories=categories, platform=platform_str)
        all_violations = []
        for page in pages:
            violations = evaluate_rules(page, rules)
            for v in violations:
                v.page_url = page.url
            all_violations.extend(violations)

        score = calculate_score(all_violations)

    console.print(f"  [green]✓[/green] Evaluated {len(rules)} rules across {len(pages)} pages")
    console.print(f"  [green]✓[/green] Found {len(all_violations)} total issues")
    console.print("")

    _print_score(score)

    report = AuditReport(
        target=target,
        scan_date=datetime.now().strftime("%Y-%m-%d %H:%M"),
        platform=platform_str,
        pages_scanned=len(pages),
        score=score,
        violations=all_violations,
        page_data=pages,
    )

    _output_report(report, format, output)


@app.command(name="check-links")
def check_links_cmd(
    target: str = typer.Argument(..., help="URL to check links for"),
    output: str = typer.Option("", "--output", "-o", help="Output file path"),
) -> None:
    """Check a page for broken links and redirect chains."""
    from growthlint.analyzers.dead_links import check_page_links, format_link_report
    from growthlint.scanners.url_scanner import scan_url

    console.print(Panel(
        f"[bold]GrowthLint v{__version__}[/bold]\n"
        f"Checking links: {target}",
        title="🔗 Link Checker",
        border_style="cyan",
    ))

    with console.status("[bold cyan]Fetching page...[/bold cyan]"):
        try:
            page_data = scan_url(target)
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

    console.print(f"  [green]✓[/green] Found {len(page_data.links)} links")

    results = check_page_links(page_data)
    broken = [r for r in results if r.is_broken]
    chains = [r for r in results if r.has_long_chain and not r.is_broken]

    console.print(f"  [green]✓[/green] Checked {len(results)} links")
    if broken:
        console.print(f"  [red]✗[/red] {len(broken)} broken links")
    if chains:
        console.print(f"  [yellow]![/yellow] {len(chains)} long redirect chains")
    console.print("")

    report_text = format_link_report(results)

    if output:
        Path(output).write_text(report_text)
        console.print(f"[green]Report saved to:[/green] {output}")
    else:
        console.print(report_text)


@app.command(name="check-integrations")
def check_integrations_cmd(
    target: str = typer.Argument(..., help="URL to check integrations for"),
    output: str = typer.Option("", "--output", "-o", help="Output file path"),
) -> None:
    """Check analytics integration health on a page."""
    from growthlint.analyzers.integration_health import check_integrations, format_integration_report
    from growthlint.scanners.url_scanner import scan_url

    console.print(Panel(
        f"[bold]GrowthLint v{__version__}[/bold]\n"
        f"Checking integrations: {target}",
        title="🔌 Integration Health",
        border_style="cyan",
    ))

    with console.status("[bold cyan]Fetching page...[/bold cyan]"):
        try:
            page_data = scan_url(target)
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

    report = check_integrations(page_data)
    detected = report.detected_tools

    console.print(f"  [green]✓[/green] Detected {len(detected)} analytics tools")
    for t in detected:
        health_icon = {"healthy": "🟢", "partial": "🟡", "warning": "🟠"}.get(t.health, "🔴")
        console.print(f"    {health_icon} {t.tool_name}")
    if report.conflicts:
        console.print(f"  [yellow]![/yellow] {len(report.conflicts)} conflicts detected")
    console.print("")

    report_text = format_integration_report(report)

    if output:
        Path(output).write_text(report_text)
        console.print(f"[green]Report saved to:[/green] {output}")
    else:
        console.print(report_text)


@app.command(name="map-funnel")
def map_funnel_cmd(
    target: str = typer.Argument(..., help="URL to map funnel for"),
    output: str = typer.Option("", "--output", "-o", help="Output file path"),
    max_pages: int = typer.Option(20, "--max-pages", help="Max pages to crawl"),
) -> None:
    """Reconstruct the conversion funnel from site structure."""
    from growthlint.generators.funnel_mapper import format_funnel_map, map_funnel
    from growthlint.scanners.sitemap_scanner import crawl_site

    console.print(Panel(
        f"[bold]GrowthLint v{__version__}[/bold]\n"
        f"Mapping funnel: {target}",
        title="🗺️ Funnel Mapper",
        border_style="cyan",
    ))

    pages = crawl_site(target, max_pages=max_pages)
    if not pages:
        console.print("[yellow]No pages found.[/yellow]")
        raise typer.Exit(0)

    funnel = map_funnel(pages)
    console.print(f"  [green]✓[/green] Mapped {funnel.stage_count} pages")
    if funnel.dead_ends:
        console.print(f"  [yellow]![/yellow] {len(funnel.dead_ends)} dead-end pages")
    if funnel.missing_stages:
        console.print(f"  [yellow]![/yellow] Missing: {', '.join(funnel.missing_stages)}")
    console.print("")

    report_text = format_funnel_map(funnel)
    _write_or_print(report_text, output)


@app.command(name="generate-spec")
def generate_spec_cmd(
    target: str = typer.Argument(..., help="URL to generate analytics spec for"),
    output: str = typer.Option("", "--output", "-o", help="Output file path"),
) -> None:
    """Generate an analytics tracking plan from page analysis."""
    from growthlint.generators.analytics_spec import format_analytics_spec, generate_analytics_spec
    from growthlint.scanners.url_scanner import scan_url

    console.print(Panel(
        f"[bold]GrowthLint v{__version__}[/bold]\n"
        f"Generating spec: {target}",
        title="📋 Analytics Spec",
        border_style="cyan",
    ))

    with console.status("[bold cyan]Analyzing page...[/bold cyan]"):
        page_data = scan_url(target)

    spec = generate_analytics_spec([page_data])
    console.print(f"  [green]✓[/green] Generated {len(spec.events)} events")
    if spec.detected_tools:
        console.print(f"  [green]✓[/green] Detected: {', '.join(spec.detected_tools)}")
    console.print("")

    report_text = format_analytics_spec(spec)
    _write_or_print(report_text, output)


@app.command(name="suggest-schema")
def suggest_schema_cmd(
    target: str = typer.Argument(..., help="URL to find schema opportunities for"),
    output: str = typer.Option("", "--output", "-o", help="Output file path"),
) -> None:
    """Find schema markup opportunities with ready-to-use JSON-LD."""
    from growthlint.analyzers.schema_finder import find_schema_opportunities, format_schema_suggestions
    from growthlint.scanners.url_scanner import scan_url

    console.print(Panel(
        f"[bold]GrowthLint v{__version__}[/bold]\n"
        f"Finding schema opportunities: {target}",
        title="🏷️ Schema Finder",
        border_style="cyan",
    ))

    with console.status("[bold cyan]Analyzing page...[/bold cyan]"):
        page_data = scan_url(target)

    suggestions = find_schema_opportunities(page_data)
    console.print(f"  [green]✓[/green] Found {len(suggestions)} schema opportunities")
    for s in suggestions:
        icon = {"high": "🟢", "medium": "🟡", "low": "🔵"}.get(s.confidence, "")
        console.print(f"    {icon} {s.schema_type}")
    console.print("")

    report_text = format_schema_suggestions(suggestions)
    _write_or_print(report_text, output)


@app.command(name="compare")
def compare_cmd(
    your_url: str = typer.Argument(..., help="Your site URL"),
    competitor_url: str = typer.Argument(..., help="Competitor site URL"),
    output: str = typer.Option("", "--output", "-o", help="Output file path"),
) -> None:
    """Compare your site against a competitor."""
    from growthlint.analyzers.competitor_diff import compare_sites, format_comparison

    console.print(Panel(
        f"[bold]GrowthLint v{__version__}[/bold]\n"
        f"Comparing: {your_url} vs {competitor_url}",
        title="🔄 Competitor Comparison",
        border_style="cyan",
    ))

    with console.status("[bold cyan]Scanning both sites...[/bold cyan]"):
        result = compare_sites(your_url, competitor_url)

    console.print(f"  [green]✓[/green] Your score: {result.site_a.score}/100 ({result.site_a.grade})")
    console.print(f"  [green]✓[/green] Competitor:  {result.site_b.score}/100 ({result.site_b.grade})")
    console.print("")

    report_text = format_comparison(result)
    _write_or_print(report_text, output)


@app.command(name="snapshot")
def snapshot_cmd(
    target: str = typer.Argument(..., help="URL or directory to snapshot"),
) -> None:
    """Save a timestamped growth score snapshot for tracking over time."""
    from growthlint.generators.growth_diff import save_snapshot
    from growthlint.models import AuditReport
    from growthlint.rules.engine import evaluate_rules
    from growthlint.rules.loader import load_rules
    from growthlint.scanners.url_scanner import scan_url
    from growthlint.utils.scoring import calculate_score

    console.print(Panel(
        f"[bold]GrowthLint v{__version__}[/bold]\n"
        f"Snapshotting: {target}",
        title="📸 Snapshot",
        border_style="cyan",
    ))

    with console.status("[bold cyan]Scanning...[/bold cyan]"):
        page_data = scan_url(target)
        rules = load_rules()
        violations = evaluate_rules(page_data, rules)
        score = calculate_score(violations)

    from datetime import datetime
    report = AuditReport(
        target=target,
        scan_date=datetime.now().strftime("%Y-%m-%d %H:%M"),
        pages_scanned=1,
        score=score,
        violations=violations,
    )

    filepath = save_snapshot(report)
    console.print(f"  [green]✓[/green] Score: {score.score}/100 ({score.grade})")
    console.print(f"  [green]✓[/green] Snapshot saved: {filepath}")


@app.command(name="diff")
def diff_cmd(
    output: str = typer.Option("", "--output", "-o", help="Output file path"),
) -> None:
    """Compare the latest two snapshots to show growth changes."""
    from growthlint.generators.growth_diff import diff_snapshots, format_diff, load_snapshots

    snapshots = load_snapshots()
    if len(snapshots) < 2:
        console.print("[yellow]Need at least 2 snapshots. Run 'growthlint snapshot <url>' first.[/yellow]")
        raise typer.Exit(0)

    old_name, old_report = snapshots[-2]
    new_name, new_report = snapshots[-1]

    diff = diff_snapshots(old_report, new_report)

    arrow = "↑" if diff.score_delta > 0 else "↓" if diff.score_delta < 0 else "→"
    console.print(f"  Score: {diff.old_score} → {diff.new_score} ({arrow} {abs(diff.score_delta)})")
    if diff.fixed_violations:
        console.print(f"  [green]✓[/green] {len(diff.fixed_violations)} issues fixed")
    if diff.new_violations:
        console.print(f"  [red]✗[/red] {len(diff.new_violations)} new issues")
    console.print("")

    report_text = format_diff(diff)
    _write_or_print(report_text, output)


@app.command(name="check-pr")
def check_pr_cmd(
    path: str = typer.Argument(".", help="Repository path to check"),
    min_score: int = typer.Option(0, "--min-score", help="Minimum acceptable score"),
    max_critical: int = typer.Option(-1, "--max-critical", help="Maximum critical violations allowed (-1 = unlimited)"),
) -> None:
    """CI check - exits with code 1 if thresholds are exceeded."""
    from growthlint.ci import check_pr

    console.print(Panel(
        f"[bold]GrowthLint v{__version__}[/bold]\n"
        f"CI Check: {path}",
        title="🏗️ CI Check",
        border_style="cyan",
    ))

    with console.status("[bold cyan]Running checks...[/bold cyan]"):
        result = check_pr(path, min_score=min_score, max_critical=max_critical)

    console.print(f"  Score: {result.score}/100 ({result.grade})")
    console.print(f"  Critical: {result.critical_count}")
    console.print(f"  Total: {result.total_violations}")
    console.print("")

    if result.passed:
        console.print("[bold green]✓ CI check passed[/bold green]")
    else:
        console.print("[bold red]✗ CI check failed[/bold red]")
        for failure in result.failures:
            console.print(f"  [red]-[/red] {failure}")
        raise typer.Exit(1)


@app.command(name="analyze-psychology")
def analyze_psychology_cmd(
    target: str = typer.Argument(..., help="URL to analyze"),
    output: str = typer.Option("", "--output", "-o", help="Output file path"),
) -> None:
    """Analyze page persuasion psychology - trust, urgency, social proof, clarity."""
    from growthlint.analyzers.page_psychology import analyze_psychology, format_psychology_report
    from growthlint.scanners.url_scanner import scan_url

    console.print(Panel(
        f"[bold]GrowthLint v{__version__}[/bold]\n"
        f"Analyzing psychology: {target}",
        title="🧠 Page Psychology",
        border_style="cyan",
    ))

    with console.status("[bold cyan]Analyzing page...[/bold cyan]"):
        page_data = scan_url(target)

    score = analyze_psychology(page_data)
    console.print(f"  [green]✓[/green] Persuasion Score: {score.overall_score}/100")
    console.print(f"    Trust: {score.trust_score} | Social Proof: {score.social_proof_score} | Clarity: {score.clarity_score}")
    console.print(f"    Risk Reduction: {score.risk_reduction_score} | Urgency: {score.urgency_score}")
    console.print("")

    report_text = format_psychology_report(score)
    _write_or_print(report_text, output)


@app.command(name="check-messages")
def check_messages_cmd(
    target: str = typer.Argument(..., help="URL to check message consistency"),
    output: str = typer.Option("", "--output", "-o", help="Output file path"),
) -> None:
    """Check message consistency across page elements."""
    from growthlint.analyzers.message_matcher import check_messages, format_message_report
    from growthlint.scanners.url_scanner import scan_url

    console.print(Panel(
        f"[bold]GrowthLint v{__version__}[/bold]\n"
        f"Checking messages: {target}",
        title="💬 Message Consistency",
        border_style="cyan",
    ))

    with console.status("[bold cyan]Analyzing page...[/bold cyan]"):
        page_data = scan_url(target)

    report = check_messages(page_data)
    console.print(f"  [green]✓[/green] Consistency Score: {report.consistency_score}/100")
    if report.issues:
        console.print(f"  [yellow]![/yellow] {len(report.issues)} message issues found")
    console.print("")

    report_text = format_message_report(report)
    _write_or_print(report_text, output)


def _write_or_print(text: str, output: str) -> None:
    """Write to file or print to console."""
    if output:
        Path(output).write_text(text)
        console.print(f"[green]Report saved to:[/green] {output}")
    else:
        console.print(text)


def _print_score(score: "GrowthScore") -> None:
    """Print the score panel."""
    grade_color = _grade_color(score.grade)
    console.print(Panel(
        f"[bold {grade_color}]{score.score}/100 (Grade: {score.grade})[/bold {grade_color}]\n"
        f"Critical: {score.critical_count} | Warnings: {score.warning_count} | Info: {score.info_count}\n"
        f"{score.revenue_leak_estimate}",
        title="📊 Growth Score",
        border_style=grade_color,
    ))


def _output_report(report: "AuditReport", format: str, output: str) -> None:
    """Generate and output the report."""
    from growthlint.reporters.csv_report import generate_csv
    from growthlint.reporters.json_report import generate_json
    from growthlint.reporters.markdown_report import generate_markdown

    if format == "json":
        report_text = generate_json(report)
    elif format == "csv":
        report_text = generate_csv(report)
    else:
        report_text = generate_markdown(report)

    if output:
        out_path = Path(output)
        out_path.write_text(report_text)
        console.print(f"\n[green]Report saved to:[/green] {out_path}")
    else:
        console.print("\n" + report_text)


def _grade_color(grade: str) -> str:
    """Return a Rich color for the grade."""
    if grade.startswith("A"):
        return "green"
    if grade.startswith("B"):
        return "yellow"
    if grade.startswith("C"):
        return "dark_orange"
    return "red"


if __name__ == "__main__":
    app()
