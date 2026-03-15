"""Repository scanner for analyzing local project files."""

from __future__ import annotations

from pathlib import Path

from growthlint.models import PageData, Platform
from growthlint.scanners.dom_parser import parse_html
from growthlint.scanners.platform_detector import (
    detect_platform_from_repo,
    get_scannable_extensions,
)

# Directories to always skip
SKIP_DIRS = {
    "node_modules", ".git", ".next", ".nuxt", "__pycache__", ".cache",
    "dist", "build", ".output", "vendor", ".venv", "venv",
}

MAX_FILE_SIZE = 500_000  # 500KB


def scan_repo(path: str | Path, platform: Platform | None = None) -> tuple[list[PageData], Platform]:
    """Scan a local repository and return page data for all scannable files.

    Returns:
        Tuple of (list of PageData, detected Platform).
    """
    repo_path = Path(path).resolve()
    if not repo_path.is_dir():
        raise FileNotFoundError(f"Directory not found: {repo_path}")

    if platform is None:
        platform = detect_platform_from_repo(repo_path)

    extensions = get_scannable_extensions(platform)
    files = _find_scannable_files(repo_path, extensions)
    pages = []

    for file_path in files:
        page = _scan_file(file_path, repo_path)
        if page:
            pages.append(page)

    return pages, platform


def _find_scannable_files(root: Path, extensions: list[str]) -> list[Path]:
    """Find all files with matching extensions, skipping excluded dirs."""
    files = []
    for item in root.rglob("*"):
        if item.is_file() and item.suffix in extensions:
            # Skip excluded directories
            if any(skip in item.parts for skip in SKIP_DIRS):
                continue
            # Skip very large files
            if item.stat().st_size > MAX_FILE_SIZE:
                continue
            files.append(item)
    return sorted(files)


def _scan_file(file_path: Path, repo_root: Path) -> PageData | None:
    """Parse a single file into PageData."""
    try:
        content = file_path.read_text(errors="ignore")
    except (OSError, PermissionError):
        return None

    if not content.strip():
        return None

    suffix = file_path.suffix

    if suffix in (".html", ".htm", ".php", ".liquid"):
        page = parse_html(content)
    elif suffix in (".jsx", ".tsx", ".js", ".ts", ".astro"):
        page = _parse_component(content)
    else:
        return None

    page.file_path = str(file_path.relative_to(repo_root))
    return page


def _parse_component(content: str) -> PageData:
    """Extract page data from JSX/TSX/Astro component files.

    Uses regex-based extraction since these aren't pure HTML.
    Focuses on the template/render portion of the file.
    """
    import re

    page = PageData()

    # Extract JSX return block or Astro template
    # For Astro: everything after the --- frontmatter
    astro_match = re.search(r"---\s*\n(.*?)\n\s*---\s*\n(.*)", content, re.DOTALL)
    if astro_match:
        html_portion = astro_match.group(2)
    else:
        # For JSX: find the return statement's JSX
        jsx_match = re.search(r"return\s*\(\s*(.*?)\s*\)\s*;?\s*\}", content, re.DOTALL)
        html_portion = jsx_match.group(1) if jsx_match else content

    # Parse whatever HTML-like content we found
    page = parse_html(html_portion)
    page.html_length = len(content)

    # Also scan the full file for script patterns (imports, analytics calls)
    page.inline_scripts = [content[:3000]]

    return page
