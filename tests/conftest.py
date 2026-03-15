"""Shared test fixtures for GrowthLint."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "sample_react_site"


@pytest.fixture
def sample_html() -> str:
    """Load the sample React site HTML."""
    return (FIXTURES_DIR / "index.html").read_text()


@pytest.fixture
def minimal_html() -> str:
    """A minimal valid HTML page."""
    return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Minimal Page</title>
    <meta name="description" content="A minimal test page for unit testing.">
    <link rel="canonical" href="https://example.com/">
    <link rel="icon" href="/favicon.ico">
    <meta property="og:title" content="Minimal Page">
    <meta property="og:description" content="A minimal test page.">
</head>
<body>
    <h1>Welcome to Minimal Page</h1>
    <h2>Features</h2>
    <p>Trusted by 10,000+ customers worldwide.</p>
    <p>Money-back guarantee. Cancel anytime.</p>
    <a href="/signup">Get Started Free</a>
    <img src="/logo.png" alt="Company logo">
    <script type="application/ld+json">
    {"@context": "https://schema.org", "@type": "Organization", "name": "Test"}
    </script>
    <script src="https://www.googletagmanager.com/gtag/js?id=G-EXAMPLE"></script>
    <script>
        gtag('config', 'G-EXAMPLE');
        gtag('event', 'page_view');
    </script>
</body>
</html>"""
