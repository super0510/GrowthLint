"""Growth Playbook Extractor — reverse-engineers a competitor's growth stack."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

from growthlint.config import ANALYTICS_PATTERNS, CTA_PATTERNS
from growthlint.models import PageData


# ---------------------------------------------------------------------------
# Extra detection patterns (beyond config.ANALYTICS_PATTERNS)
# ---------------------------------------------------------------------------

MARKETING_TOOL_PATTERNS: dict[str, list[str]] = {
    "HubSpot": [r"hs-scripts\.com", r"hs-analytics", r"hubspot\.com", r"hbspt\.forms"],
    "Mailchimp": [r"mailchimp\.com", r"chimpstatic\.com", r"list-manage\.com"],
    "Klaviyo": [r"klaviyo\.com", r"static\.klaviyo\.com", r"_learnq\.push"],
    "ConvertKit": [r"convertkit\.com", r"ck\.page"],
    "ActiveCampaign": [r"activecampaign\.com", r"trackcmp\.net"],
}

SUPPORT_TOOL_PATTERNS: dict[str, list[str]] = {
    "Intercom": [r"widget\.intercom\.io", r"intercomSettings", r"Intercom\("],
    "Drift": [r"js\.driftt\.com", r"drift\.com", r"drift\.load\("],
    "Zendesk": [r"zdassets\.com", r"zendesk\.com"],
    "Crisp": [r"crisp\.chat", r"client\.crisp\.chat"],
    "LiveChat": [r"livechatinc\.com", r"__lc\.license"],
    "Tidio": [r"tidio\.co", r"tidioChatCode"],
}

RETARGETING_PATTERNS: dict[str, list[str]] = {
    "Meta Pixel": [r"connect\.facebook\.net.*fbevents", r"fbq\(['\"]init"],
    "Google Ads": [r"googleads\.g\.doubleclick", r"gtag\(['\"]config['\"],\s*['\"]AW-"],
    "LinkedIn Insight": [r"snap\.licdn\.com", r"linkedin\.com/px", r"_linkedin_partner_id"],
    "Twitter/X Pixel": [r"static\.ads-twitter\.com", r"t\.co/i/adsct", r"twq\("],
    "TikTok Pixel": [r"analytics\.tiktok\.com", r"ttq\.load"],
    "Pinterest Tag": [r"pintrk", r"ct\.pinterest\.com"],
    "Reddit Pixel": [r"alb\.reddit\.com", r"rdt\("],
    "Snapchat Pixel": [r"sc-static\.net/scevent", r"snaptr\("],
}

POPUP_PATTERNS: dict[str, list[str]] = {
    "OptinMonster": [r"optinmonster", r"optmstr", r"omapi"],
    "Sumo": [r"sumo\.com", r"load\.sumome\.com"],
    "Hello Bar": [r"hellobar", r"my\.hellobar\.com"],
    "Privy": [r"privy\.com", r"widget\.privy\.com"],
}

FRAMEWORK_PATTERNS: dict[str, list[str]] = {
    "Next.js": [r"_next/", r"__next", r"__NEXT_DATA__"],
    "Nuxt.js": [r"_nuxt/", r"__nuxt"],
    "React": [r"react\.production", r"react-dom", r"__react"],
    "Vue.js": [r"vue\.js", r"vue\.min\.js", r"vue\.runtime"],
    "Angular": [r"ng-version", r"angular\.min\.js", r"ng-app"],
    "Svelte": [r"svelte", r"__svelte"],
    "WordPress": [r"wp-content", r"wp-includes", r"wp-json"],
    "Shopify": [r"cdn\.shopify\.com", r"myshopify\.com", r"Shopify\.theme"],
    "Webflow": [r"webflow\.com", r"wf-page"],
    "Wix": [r"wix\.com", r"parastorage\.com", r"wixstatic\.com"],
    "Squarespace": [r"squarespace\.com", r"sqsp", r"static1\.squarespace"],
    "Ghost": [r"ghost\.org", r"ghost\.io"],
    "Gatsby": [r"gatsby", r"__gatsby"],
}

FUNNEL_PAGE_PATTERNS: dict[str, list[str]] = {
    "pricing": [r"/pricing", r"/plans", r"/packages"],
    "signup": [r"/signup", r"/register", r"/join", r"/start", r"/create-account", r"/get-started"],
    "login": [r"/login", r"/signin", r"/auth"],
    "blog": [r"/blog", r"/articles", r"/posts", r"/news"],
    "docs": [r"/docs", r"/documentation", r"/help", r"/support", r"/kb", r"/knowledge"],
    "about": [r"/about", r"/team", r"/company", r"/story", r"/our-story"],
    "contact": [r"/contact", r"/get-in-touch"],
    "careers": [r"/careers", r"/jobs", r"/hiring"],
    "legal": [r"/privacy", r"/terms", r"/tos", r"/legal", r"/gdpr", r"/cookie"],
    "demo": [r"/demo", r"/schedule", r"/book-a-demo", r"/book-demo"],
    "changelog": [r"/changelog", r"/updates", r"/whats-new"],
    "integrations": [r"/integrations", r"/apps", r"/marketplace"],
    "case-studies": [r"/case-stud", r"/customers", r"/success-stor"],
}

SOCIAL_PROOF_PATTERNS = [
    r"trusted\s+by\s+[\d,]+",
    r"used\s+by\s+[\d,]+",
    r"[\d,]+\+?\s*(customers|companies|teams|users|businesses)",
    r"\d\.\d\s*/\s*5",
    r"\d\.\d\s+out\s+of\s+5",
    r"[\d,]+\+?\s*reviews?",
    r"★|⭐|star",
    r"as\s+seen\s+(in|on)",
    r"featured\s+(in|on|by)",
    r"SOC\s*2|GDPR|ISO\s*27001|HIPAA",
    r"SSL|encrypted|secure\s+checkout",
    r"money.back\s+guarantee",
]

PRICING_PATTERNS = [
    (r"free\s*(trial|plan|tier|version)", "Free tier offered"),
    (r"(\d+).day\s*(free\s*)?trial", "Free trial offered"),
    (r"money.back\s*guarantee", "Money-back guarantee"),
    (r"cancel\s*any\s*time", "Cancel anytime policy"),
    (r"save\s*\d+%", "Annual discount"),
    (r"(annual|yearly)\s*(plan|billing|pricing)", "Annual billing option"),
    (r"most\s*popular", "\"Most Popular\" badge on plan"),
    (r"(recommended|best\s*value)", "Recommended plan highlighted"),
    (r"limited\s*time", "Limited-time offer"),
    (r"enterprise|custom\s*pricing|contact\s*sales", "Enterprise/custom pricing tier"),
    (r"per\s*(user|seat|month|year)", "Per-seat/usage pricing"),
    (r"starter|pro|business|enterprise", "Multi-tier pricing"),
]


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class ToolDetection:
    name: str
    category: str  # analytics, marketing, support, retargeting, email, popup
    detected_via: str


@dataclass
class CTAInsight:
    text: str
    element_type: str  # button, link
    position: str  # above-fold, below-fold
    href: str


@dataclass
class LeadCaptureMethod:
    method_type: str  # form, popup, chatbot, newsletter
    details: str


@dataclass
class FunnelPage:
    page_type: str
    url: str


@dataclass
class GrowthPlaybook:
    url: str
    tools: list[ToolDetection] = field(default_factory=list)
    cta_strategy: list[CTAInsight] = field(default_factory=list)
    social_proof: list[str] = field(default_factory=list)
    pricing_psychology: list[str] = field(default_factory=list)
    funnel_pages: list[FunnelPage] = field(default_factory=list)
    lead_capture: list[LeadCaptureMethod] = field(default_factory=list)
    retargeting: list[ToolDetection] = field(default_factory=list)
    seo_strategy: dict = field(default_factory=dict)
    tech_stack: list[str] = field(default_factory=list)
    steal_this: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Core harvesting logic
# ---------------------------------------------------------------------------

def harvest_playbook(page_data: PageData) -> GrowthPlaybook:
    """Reverse-engineer a competitor's growth playbook from their page."""
    all_scripts = " ".join(page_data.scripts + page_data.inline_scripts)
    all_sources = " ".join(page_data.script_sources)
    search_text = all_scripts + " " + all_sources

    playbook = GrowthPlaybook(url=page_data.url)

    # 1. Detect analytics tools (from existing config)
    for tool_id, patterns in ANALYTICS_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, search_text, re.IGNORECASE):
                display = tool_id.replace("_", " ").title()
                playbook.tools.append(ToolDetection(
                    name=display, category="analytics", detected_via=pattern,
                ))
                break

    # 2. Detect marketing tools
    for name, patterns in MARKETING_TOOL_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, search_text, re.IGNORECASE):
                playbook.tools.append(ToolDetection(
                    name=name, category="email & marketing", detected_via=pattern,
                ))
                break

    # 3. Detect support/chat tools
    for name, patterns in SUPPORT_TOOL_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, search_text, re.IGNORECASE):
                playbook.tools.append(ToolDetection(
                    name=name, category="support & chat", detected_via=pattern,
                ))
                playbook.lead_capture.append(LeadCaptureMethod(
                    method_type="chatbot", details=f"Live chat via {name}",
                ))
                break

    # 4. Detect retargeting pixels
    for name, patterns in RETARGETING_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, search_text, re.IGNORECASE):
                tool = ToolDetection(name=name, category="retargeting", detected_via=pattern)
                playbook.retargeting.append(tool)
                playbook.tools.append(tool)
                break

    # 5. Detect popup tools
    for name, patterns in POPUP_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, search_text, re.IGNORECASE):
                playbook.tools.append(ToolDetection(
                    name=name, category="popup & lead capture", detected_via=pattern,
                ))
                playbook.lead_capture.append(LeadCaptureMethod(
                    method_type="popup", details=f"Popup tool: {name}",
                ))
                break

    # 6. Detect tech stack / framework
    for name, patterns in FRAMEWORK_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, search_text + " " + page_data.text_content, re.IGNORECASE):
                playbook.tech_stack.append(name)
                break

    # 7. Extract CTA strategy
    for i, cta in enumerate(page_data.ctas):
        position = "above-fold" if i < 5 else "below-fold"
        playbook.cta_strategy.append(CTAInsight(
            text=cta.text,
            element_type=cta.tag,
            position=position,
            href=cta.href,
        ))

    # 8. Detect social proof
    text = page_data.text_content.lower()
    for pattern in SOCIAL_PROOF_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            # Get context around match
            match_obj = re.search(pattern, page_data.text_content, re.IGNORECASE)
            if match_obj:
                start = max(0, match_obj.start() - 20)
                end = min(len(page_data.text_content), match_obj.end() + 40)
                context = page_data.text_content[start:end].strip()
                if context and context not in playbook.social_proof:
                    playbook.social_proof.append(context)

    # 9. Detect pricing psychology
    for pattern, description in PRICING_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            if description not in playbook.pricing_psychology:
                playbook.pricing_psychology.append(description)

    # 10. Classify funnel pages from internal links
    seen_types: set[str] = set()
    for link in page_data.internal_links:
        path = urlparse(link).path.lower()
        for page_type, patterns in FUNNEL_PAGE_PATTERNS.items():
            if page_type in seen_types:
                continue
            for pattern in patterns:
                if re.search(pattern, path):
                    playbook.funnel_pages.append(FunnelPage(page_type=page_type, url=link))
                    seen_types.add(page_type)
                    break

    # 11. Forms as lead capture
    for form in page_data.forms:
        field_names = " ".join(form.fields).lower()
        if "email" in field_names and ("subscribe" in field_names or "newsletter" in field_names or form.field_count <= 2):
            playbook.lead_capture.append(LeadCaptureMethod(
                method_type="newsletter", details=f"Email signup form ({form.field_count} fields)",
            ))
        else:
            playbook.lead_capture.append(LeadCaptureMethod(
                method_type="form", details=f"Form with {form.field_count} fields ({', '.join(form.fields[:3])})",
            ))

    # 12. SEO strategy
    playbook.seo_strategy = {
        "has_title": bool(page_data.meta.title),
        "has_description": bool(page_data.meta.description),
        "has_canonical": bool(page_data.meta.canonical),
        "has_og_tags": bool(page_data.meta.og_title and page_data.meta.og_image),
        "has_favicon": bool(page_data.meta.favicon),
        "schema_types": [s.get("@type", "unknown") for s in page_data.schema_markup],
        "h1_count": len(page_data.headings.get("h1", [])),
        "images_with_alt": sum(1 for img in page_data.images if img.text),
        "images_total": len(page_data.images),
    }

    # 13. Generate "Steal This" recommendations
    playbook.steal_this = _generate_steal_this(playbook)

    return playbook


def _generate_steal_this(playbook: GrowthPlaybook) -> list[str]:
    """Generate actionable 'steal this' items from the playbook."""
    items: list[str] = []

    # Chat tools
    chat_tools = [t for t in playbook.tools if t.category == "support & chat"]
    if chat_tools:
        names = ", ".join(t.name for t in chat_tools)
        items.append(f"Add live chat — competitor uses {names} for real-time support")

    # Retargeting
    if playbook.retargeting:
        platforms = ", ".join(t.name for t in playbook.retargeting)
        items.append(f"Set up retargeting on {len(playbook.retargeting)} platform(s) — competitor runs {platforms}")

    # Email marketing
    email_tools = [t for t in playbook.tools if t.category == "email & marketing"]
    if email_tools:
        names = ", ".join(t.name for t in email_tools)
        items.append(f"Set up email automation — competitor uses {names}")

    # Social proof
    if playbook.social_proof:
        items.append(f"Add social proof — competitor showcases {len(playbook.social_proof)} trust signals")

    # Pricing tactics
    for tactic in playbook.pricing_psychology[:3]:
        items.append(f"Copy pricing tactic — {tactic}")

    # CTA strategy
    above_fold = [c for c in playbook.cta_strategy if c.position == "above-fold"]
    if above_fold:
        primary = above_fold[0]
        items.append(f'Use action-oriented CTA — competitor leads with "{primary.text}"')

    # Popup tools
    popups = [t for t in playbook.tools if t.category == "popup & lead capture"]
    if popups:
        items.append(f"Add lead capture popups — competitor uses {popups[0].name}")

    # Funnel pages
    competitor_pages = {p.page_type for p in playbook.funnel_pages}
    suggested = {"pricing", "blog", "case-studies", "demo", "docs"} - competitor_pages
    if not suggested and "case-studies" in competitor_pages:
        items.append("Add case studies — competitor has a dedicated customer stories section")
    if "demo" in competitor_pages:
        items.append("Offer a demo/booking page — competitor has a dedicated demo page")
    if "changelog" in competitor_pages:
        items.append("Add a changelog — competitor publicly tracks product updates")

    # SEO
    schema_types = playbook.seo_strategy.get("schema_types", [])
    if schema_types:
        items.append(f"Add schema markup — competitor uses {', '.join(schema_types)}")

    return items[:10]  # Cap at 10


# ---------------------------------------------------------------------------
# Markdown formatter
# ---------------------------------------------------------------------------

def format_playbook(playbook: GrowthPlaybook) -> str:
    """Format the growth playbook as markdown."""
    domain = urlparse(playbook.url).netloc or playbook.url
    lines: list[str] = []
    lines.append(f"# Growth Playbook: {domain}")
    lines.append("")

    # Tech stack
    if playbook.tech_stack:
        lines.append("## Tech Stack")
        lines.append("")
        for tech in playbook.tech_stack:
            lines.append(f"- {tech}")
        lines.append("")

    # Growth tools
    if playbook.tools:
        lines.append(f"## Growth Tools ({len(playbook.tools)} detected)")
        lines.append("")

        categories: dict[str, list[ToolDetection]] = {}
        for tool in playbook.tools:
            categories.setdefault(tool.category, []).append(tool)

        for category, tools in categories.items():
            lines.append(f"### {category.title()}")
            lines.append("")
            lines.append("| Tool | Detected Via |")
            lines.append("|------|-------------|")
            for t in tools:
                lines.append(f"| {t.name} | `{t.detected_via}` |")
            lines.append("")

    # CTA strategy
    if playbook.cta_strategy:
        lines.append("## CTA Strategy")
        lines.append("")
        above = [c for c in playbook.cta_strategy if c.position == "above-fold"]
        below = [c for c in playbook.cta_strategy if c.position == "below-fold"]
        if above:
            lines.append(f'- **Primary CTA:** "{above[0].text}" ({above[0].element_type}, above fold)')
            if len(above) > 1:
                secondary = ", ".join(f'"{c.text}"' for c in above[1:3])
                lines.append(f"- **Secondary CTAs:** {secondary}")
        if below:
            lines.append(f"- **Below-fold CTAs:** {len(below)} additional CTAs")
        lines.append(f"- **Total CTAs:** {len(playbook.cta_strategy)}")
        lines.append("")

    # Social proof
    if playbook.social_proof:
        lines.append("## Social Proof")
        lines.append("")
        for proof in playbook.social_proof[:8]:
            lines.append(f'- "{proof}"')
        lines.append("")

    # Pricing psychology
    if playbook.pricing_psychology:
        lines.append("## Pricing Psychology")
        lines.append("")
        for tactic in playbook.pricing_psychology:
            lines.append(f"- {tactic}")
        lines.append("")

    # Funnel structure
    if playbook.funnel_pages:
        lines.append("## Funnel Structure")
        lines.append("")
        lines.append("| Page Type | URL |")
        lines.append("|-----------|-----|")
        for page in playbook.funnel_pages:
            lines.append(f"| {page.page_type} | {page.url} |")
        lines.append("")

    # Lead capture
    if playbook.lead_capture:
        lines.append("## Lead Capture")
        lines.append("")
        for method in playbook.lead_capture:
            lines.append(f"- **{method.method_type.title()}:** {method.details}")
        lines.append("")

    # Retargeting
    if playbook.retargeting:
        lines.append("## Retargeting Setup")
        lines.append("")
        for pixel in playbook.retargeting:
            lines.append(f"- {pixel.name}")
        lines.append("")

    # SEO
    seo = playbook.seo_strategy
    if seo:
        lines.append("## SEO Setup")
        lines.append("")
        lines.append(f"- Title: {'Set' if seo.get('has_title') else 'Missing'}")
        lines.append(f"- Meta Description: {'Set' if seo.get('has_description') else 'Missing'}")
        lines.append(f"- Canonical: {'Set' if seo.get('has_canonical') else 'Missing'}")
        lines.append(f"- Open Graph: {'Complete' if seo.get('has_og_tags') else 'Incomplete'}")
        schemas = seo.get("schema_types", [])
        if schemas:
            lines.append(f"- Schema: {', '.join(schemas)}")
        else:
            lines.append("- Schema: None detected")
        total_img = seo.get("images_total", 0)
        alt_img = seo.get("images_with_alt", 0)
        if total_img:
            lines.append(f"- Images: {alt_img}/{total_img} have alt text")
        lines.append("")

    # Steal this
    if playbook.steal_this:
        lines.append("## Steal This Playbook")
        lines.append("")
        for i, item in enumerate(playbook.steal_this, 1):
            lines.append(f"{i}. **{item.split(' — ')[0]}**" + (" — " + item.split(" — ", 1)[1] if " — " in item else ""))
        lines.append("")

    return "\n".join(lines)
