"""Growth Score Badge Generator — shields.io-style SVG badges."""

from __future__ import annotations

from pathlib import Path

from growthlint.models import GrowthScore


# Grade → color mapping (shields.io palette)
GRADE_COLORS = {
    "A": "#4c1",
    "B+": "#a4a61d",
    "B": "#dfb317",
    "C+": "#fe7d37",
    "C": "#e05d44",
    "D": "#e05d44",
    "F": "#cb2431",
}


def _color_for_grade(grade: str) -> str:
    """Return hex color for a grade."""
    return GRADE_COLORS.get(grade, "#9f9f9f")


def _text_width(text: str, font_size: float = 11) -> float:
    """Approximate text width for Verdana at given font size."""
    return len(text) * font_size * 0.6 + 10


def _badge_svg(label: str, value: str, color: str, style: str = "flat") -> str:
    """Generate a shields.io-style SVG badge."""
    label_w = _text_width(label)
    value_w = _text_width(value)
    total_w = label_w + value_w
    h = 28 if style == "for-the-badge" else 20
    font_size = 11 if style != "for-the-badge" else 10
    rx = 0 if style == "flat-square" else 3

    if style == "for-the-badge":
        label = label.upper()
        value = value.upper()
        label_w = _text_width(label, 10) + 6
        value_w = _text_width(value, 10) + 6
        total_w = label_w + value_w

    label_x = label_w / 2
    value_x = label_w + value_w / 2
    text_y = h * 0.72 if style == "for-the-badge" else 15

    gradient = ""
    if style == "flat":
        gradient = (
            '<linearGradient id="s" x2="0" y2="100%">'
            '<stop offset="0" stop-color="#bbb" stop-opacity=".1"/>'
            '<stop offset="1" stop-opacity=".1"/>'
            '</linearGradient>'
        )

    shadow_dy = 1 if style != "for-the-badge" else 1.5
    gradient_rect = (
        f'<rect rx="{rx}" width="{total_w}" height="{h}" fill="url(#s)"/>'
        if style == "flat" else ""
    )
    font_weight = "bold" if style == "for-the-badge" else "bold"
    letter_spacing = ' letter-spacing="0.5"' if style == "for-the-badge" else ""

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="{h}">
  {gradient}
  <clipPath id="r"><rect rx="{rx}" width="{total_w}" height="{h}" fill="#fff"/></clipPath>
  <g clip-path="url(#r)">
    <rect width="{label_w}" height="{h}" fill="#555"/>
    <rect x="{label_w}" width="{value_w}" height="{h}" fill="{color}"/>
    {gradient_rect}
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="{font_size}" font-weight="{font_weight}"{letter_spacing}>
    <text x="{label_x}" y="{text_y + shadow_dy}" fill="#010101" fill-opacity=".3">{label}</text>
    <text x="{label_x}" y="{text_y}">{label}</text>
    <text x="{value_x}" y="{text_y + shadow_dy}" fill="#010101" fill-opacity=".3">{value}</text>
    <text x="{value_x}" y="{text_y}">{value}</text>
  </g>
</svg>"""


def generate_badge(score: GrowthScore, style: str = "flat") -> str:
    """Generate an SVG badge string for the growth score."""
    color = _color_for_grade(score.grade)
    value = f"{score.score}/100 {score.grade}"
    return _badge_svg("GrowthLint", value, color, style)


def generate_badge_markdown(score: GrowthScore, style: str = "flat") -> str:
    """Generate markdown snippet with badge reference."""
    lines = [
        "<!-- GrowthLint Score Badge -->",
        "<!-- Save the SVG file and add this to your README.md -->",
        "",
        "![GrowthLint Score](growthlint-badge.svg)",
    ]
    return "\n".join(lines)


def save_badge(score: GrowthScore, filepath: str, style: str = "flat") -> str:
    """Generate and save badge SVG to a file. Returns the filepath."""
    svg = generate_badge(score, style)
    path = Path(filepath)
    path.write_text(svg)
    return str(path)
