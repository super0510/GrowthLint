"""Auto-fix patch generator for common violations."""

from __future__ import annotations

from dataclasses import dataclass, field

from growthlint.models import PageData, RuleViolation


@dataclass
class Patch:
    """A code fix for a violation."""

    rule_id: str
    description: str
    code: str
    language: str = "html"
    location: str = ""  # where to insert (head, body_start, body_end)


def generate_patches(violations: list[RuleViolation], page_data: PageData) -> list[Patch]:
    """Generate code patches for fixable violations."""
    patches = []

    for v in violations:
        patch = _generate_patch(v, page_data)
        if patch:
            patches.append(patch)

    return patches


def _generate_patch(v: RuleViolation, page_data: PageData) -> Patch | None:
    """Generate a patch for a single violation."""
    generators = {
        "missing-title": _patch_title,
        "missing-meta-description": _patch_meta_description,
        "missing-viewport": _patch_viewport,
        "missing-canonical": _patch_canonical,
        "missing-og-tags": _patch_og_tags,
        "missing-favicon": _patch_favicon,
        "no-structured-data": _patch_schema,
        "no-analytics": _patch_analytics,
        "no-gtm": _patch_gtm,
    }

    generator = generators.get(v.rule_id)
    if generator:
        return generator(v, page_data)
    return None


def _patch_title(v: RuleViolation, page_data: PageData) -> Patch:
    return Patch(
        rule_id=v.rule_id,
        description="Add a page title tag",
        location="head",
        code='<title>Your Page Title - Brand Name</title>',
    )


def _patch_meta_description(v: RuleViolation, page_data: PageData) -> Patch:
    return Patch(
        rule_id=v.rule_id,
        description="Add a meta description",
        location="head",
        code='<meta name="description" content="Your compelling description here (120-160 chars). Include your value prop and a call to action.">',
    )


def _patch_viewport(v: RuleViolation, page_data: PageData) -> Patch:
    return Patch(
        rule_id=v.rule_id,
        description="Add viewport meta tag for mobile responsiveness",
        location="head",
        code='<meta name="viewport" content="width=device-width, initial-scale=1">',
    )


def _patch_canonical(v: RuleViolation, page_data: PageData) -> Patch:
    url = page_data.url or "https://yoursite.com/page"
    return Patch(
        rule_id=v.rule_id,
        description="Add canonical URL",
        location="head",
        code=f'<link rel="canonical" href="{url}">',
    )


def _patch_og_tags(v: RuleViolation, page_data: PageData) -> Patch:
    title = page_data.meta.title or "Your Page Title"
    desc = page_data.meta.description or "Your page description"
    url = page_data.url or "https://yoursite.com"
    return Patch(
        rule_id=v.rule_id,
        description="Add Open Graph meta tags for social sharing",
        location="head",
        code=f'''<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{url}/og-image.png">
<meta property="og:url" content="{url}">
<meta property="og:type" content="website">''',
    )


def _patch_favicon(v: RuleViolation, page_data: PageData) -> Patch:
    return Patch(
        rule_id=v.rule_id,
        description="Add favicon",
        location="head",
        code='<link rel="icon" href="/favicon.ico" sizes="any">\n<link rel="icon" href="/favicon.svg" type="image/svg+xml">',
    )


def _patch_schema(v: RuleViolation, page_data: PageData) -> Patch:
    name = page_data.meta.title or "Your Organization"
    url = page_data.url or "https://yoursite.com"
    return Patch(
        rule_id=v.rule_id,
        description="Add Organization structured data",
        location="head",
        language="json",
        code=f'''<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "{name}",
  "url": "{url}",
  "logo": "{url}/logo.png",
  "sameAs": [
    "https://twitter.com/yourbrand",
    "https://linkedin.com/company/yourbrand"
  ]
}}
</script>''',
    )


def _patch_analytics(v: RuleViolation, page_data: PageData) -> Patch:
    return Patch(
        rule_id=v.rule_id,
        description="Add Google Analytics 4",
        location="head",
        language="html",
        code='''<!-- Google Analytics 4 -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>''',
    )


def _patch_gtm(v: RuleViolation, page_data: PageData) -> Patch:
    return Patch(
        rule_id=v.rule_id,
        description="Add Google Tag Manager",
        location="head",
        language="html",
        code='''<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
})(window,document,'script','dataLayer','GTM-XXXXXXX');</script>
<!-- End Google Tag Manager -->

<!-- Add this immediately after <body>: -->
<!-- <noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-XXXXXXX" height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript> -->''',
    )


def format_patches(patches: list[Patch]) -> str:
    """Format patches as markdown."""
    lines: list[str] = []
    lines.append("# Suggested Code Fixes")
    lines.append("")
    lines.append(f"**{len(patches)} auto-fixable issues found**")
    lines.append("")

    for patch in patches:
        lines.append(f"### {patch.description}")
        lines.append("")
        lines.append(f"**Rule:** `{patch.rule_id}` | **Insert in:** `<{patch.location}>`")
        lines.append("")
        lines.append(f"```{patch.language}")
        lines.append(patch.code)
        lines.append("```")
        lines.append("")

    return "\n".join(lines)
