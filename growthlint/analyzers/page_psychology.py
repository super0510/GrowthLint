"""Page psychology analyzer - trust, urgency, social proof, persuasion scoring."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from growthlint.models import PageData


@dataclass
class PsychologyScore:
    """Psychology/persuasion analysis results."""

    overall_score: int = 0  # 0-100
    trust_score: int = 0
    urgency_score: int = 0
    social_proof_score: int = 0
    clarity_score: int = 0
    risk_reduction_score: int = 0
    findings: list[PsychologyFinding] = field(default_factory=list)


@dataclass
class PsychologyFinding:
    """A single psychology finding."""

    category: str  # trust, urgency, social_proof, clarity, risk_reduction
    signal_type: str  # present or missing
    name: str
    description: str
    impact: str


# Patterns for each psychology dimension
TRUST_PATTERNS = {
    "Security badges": r"ssl|secure|encrypted|https|lock|shield|verified",
    "Compliance certifications": r"soc\s*2|iso\s*27001|hipaa|gdpr|pci|ccpa",
    "Company longevity": r"since\s+\d{4}|founded\s+in|years?\s+of\s+experience|\d+\+?\s+years",
    "Partner/client logos": r"trusted\s+by|our\s+partners?|as\s+seen\s+(in|on)|featured\s+(in|on)",
    "Press mentions": r"forbes|techcrunch|product\s*hunt|hacker\s*news|y\s*combinator",
    "Team/about section": r"our\s+team|meet\s+the|about\s+us|our\s+story",
}

URGENCY_PATTERNS = {
    "Limited time offer": r"limited\s+time|ends?\s+(soon|today|tonight)|hurry|last\s+chance",
    "Countdown/scarcity": r"only\s+\d+\s+left|spots?\s+remaining|limited\s+(spots?|seats?|availability)",
    "Today-only pricing": r"today\s+only|flash\s+sale|special\s+offer|exclusive\s+deal",
}

SOCIAL_PROOF_PATTERNS = {
    "Customer count": r"\d[\d,]*\+?\s*(customers?|users?|companies|businesses|teams?|people|subscribers?)",
    "Star ratings": r"\d(\.\d)?\s*\/\s*5|★|(\d(\.\d)?)\s*stars?|rated\s+\d",
    "Testimonials": r"testimonial|what\s+(our\s+)?(customers?|clients?|users?)\s+say|hear\s+from",
    "Case studies": r"case\s+stud(y|ies)|success\s+stor(y|ies)|customer\s+stor(y|ies)",
    "Review mentions": r"\d+\+?\s*reviews?|verified\s+reviews?|customer\s+reviews?",
    "Social media proof": r"\d+[kK]\+?\s+followers?|community\s+of\s+\d|join\s+\d",
}

CLARITY_PATTERNS = {
    "Benefit-driven H1": r"^(get|save|grow|boost|increase|improve|double|triple|reduce|eliminate|stop)",
    "Specific numbers": r"\d+%|(\$|€|£)\d+|\d+x\s+(faster|better|more)",
    "Target audience mention": r"for\s+(teams?|startups?|agencies|marketers?|developers?|founders?|small\s+business)",
    "How it works": r"how\s+it\s+works|in\s+\d+\s+(easy\s+)?steps|simple\s+\d.*step",
}

RISK_REDUCTION_PATTERNS = {
    "Money-back guarantee": r"money[- ]back\s+guarantee|\d+[- ]day\s+guarantee|full\s+refund",
    "Free trial": r"free\s+trial|try\s+(it\s+)?free|no\s+credit\s+card\s+(required|needed)",
    "Cancel anytime": r"cancel\s+any\s*time|no\s+commitment|no\s+lock[- ]in|no\s+contract",
    "Free tier": r"free\s+(plan|tier|forever|to\s+start)|starts?\s+free|freemium|\$0",
    "Satisfaction guarantee": r"100%\s+satisfaction|satisfaction\s+guarantee|risk[- ]free",
    "Support promise": r"24/7\s+support|live\s+chat|dedicated\s+support|help\s+center",
}


def analyze_psychology(page_data: PageData) -> PsychologyScore:
    """Analyze a page's persuasion psychology."""
    text = page_data.text_content.lower()
    h1_text = " ".join(page_data.headings.get("h1", [])).lower()

    findings: list[PsychologyFinding] = []

    # Trust signals
    trust_count = 0
    for name, pattern in TRUST_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            trust_count += 1
            findings.append(PsychologyFinding(
                category="trust", signal_type="present", name=name,
                description=f"Detected: {name}",
                impact="Builds visitor confidence and credibility",
            ))
    trust_score = min(100, trust_count * 20)

    if trust_count == 0:
        findings.append(PsychologyFinding(
            category="trust", signal_type="missing", name="No trust signals",
            description="No security badges, certifications, or company history found",
            impact="Visitors may hesitate to engage without trust indicators",
        ))

    # Urgency
    urgency_count = 0
    for name, pattern in URGENCY_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            urgency_count += 1
            findings.append(PsychologyFinding(
                category="urgency", signal_type="present", name=name,
                description=f"Detected: {name}",
                impact="Creates motivation to act now rather than later",
            ))
    urgency_score = min(100, urgency_count * 35)

    # Social proof
    sp_count = 0
    for name, pattern in SOCIAL_PROOF_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            sp_count += 1
            findings.append(PsychologyFinding(
                category="social_proof", signal_type="present", name=name,
                description=f"Detected: {name}",
                impact="Reduces uncertainty through peer validation",
            ))
    social_proof_score = min(100, sp_count * 20)

    if sp_count == 0:
        findings.append(PsychologyFinding(
            category="social_proof", signal_type="missing", name="No social proof",
            description="No customer counts, testimonials, ratings, or case studies found",
            impact="92% of consumers read reviews. Missing social proof significantly reduces trust.",
        ))

    # Clarity
    clarity_count = 0
    for name, pattern in CLARITY_PATTERNS.items():
        target = h1_text if "H1" in name else text
        if re.search(pattern, target, re.IGNORECASE):
            clarity_count += 1
            findings.append(PsychologyFinding(
                category="clarity", signal_type="present", name=name,
                description=f"Detected: {name}",
                impact="Helps visitors quickly understand value and relevance",
            ))

    # Check H1 exists and has reasonable length
    if page_data.headings.get("h1"):
        h1 = page_data.headings["h1"][0]
        if len(h1) > 10:
            clarity_count += 1
    clarity_score = min(100, clarity_count * 25)

    # Risk reduction
    rr_count = 0
    for name, pattern in RISK_REDUCTION_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            rr_count += 1
            findings.append(PsychologyFinding(
                category="risk_reduction", signal_type="present", name=name,
                description=f"Detected: {name}",
                impact="Reduces perceived risk and objections to converting",
            ))
    risk_reduction_score = min(100, rr_count * 20)

    if rr_count == 0:
        findings.append(PsychologyFinding(
            category="risk_reduction", signal_type="missing", name="No risk reducers",
            description="No guarantees, free trials, or cancellation policies found",
            impact="Visitors with objections have no reassurance. Conversion anxiety increases.",
        ))

    overall = int(
        trust_score * 0.25 +
        social_proof_score * 0.25 +
        clarity_score * 0.25 +
        risk_reduction_score * 0.15 +
        urgency_score * 0.10
    )

    return PsychologyScore(
        overall_score=overall,
        trust_score=trust_score,
        urgency_score=urgency_score,
        social_proof_score=social_proof_score,
        clarity_score=clarity_score,
        risk_reduction_score=risk_reduction_score,
        findings=findings,
    )


def format_psychology_report(score: PsychologyScore) -> str:
    """Format psychology analysis as markdown."""
    lines: list[str] = []
    lines.append("# Page Psychology Analysis")
    lines.append("")
    lines.append(f"### Persuasion Score: {score.overall_score}/100")
    lines.append("")

    lines.append("| Dimension | Score |")
    lines.append("|-----------|-------|")
    for name, val in [
        ("Trust", score.trust_score),
        ("Social Proof", score.social_proof_score),
        ("Clarity", score.clarity_score),
        ("Risk Reduction", score.risk_reduction_score),
        ("Urgency", score.urgency_score),
    ]:
        bar = "█" * (val // 10) + "░" * (10 - val // 10)
        lines.append(f"| {name} | {bar} {val}/100 |")
    lines.append("")

    # Present signals
    present = [f for f in score.findings if f.signal_type == "present"]
    if present:
        lines.append("## Detected Signals")
        lines.append("")
        for f in present:
            lines.append(f"- **{f.name}** ({f.category})")
        lines.append("")

    # Missing signals
    missing = [f for f in score.findings if f.signal_type == "missing"]
    if missing:
        lines.append("## Missing Elements")
        lines.append("")
        for f in missing:
            lines.append(f"- **{f.name}**: {f.description}")
            lines.append(f"  - Impact: {f.impact}")
        lines.append("")

    return "\n".join(lines)
