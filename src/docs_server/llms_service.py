"""
LLMs.txt generation service for ServeMD Documentation Server.
Handles llms.txt content generation with PRIMARY/FALLBACK strategy.
"""

import logging
import re

from .config import settings

logger = logging.getLogger(__name__)


def transform_relative_to_absolute(markdown_content: str, base_url: str) -> str:
    """
    Transform relative .md links to absolute URLs.

    Examples:
        [Title](file.md) -> [Title](https://docs.example.com/file.md)
        [Title](file.md#section) -> [Title](https://docs.example.com/file.md#section)
    """
    # Pattern matches: [text](path.md) or [text](path.md#anchor)
    pattern = r"\[([^\]]+)\]\(([^)]+\.md(?:#[^)]*)?)\)"

    def replace_link(match):
        title = match.group(1)
        rel_path = match.group(2)

        # Skip if already absolute URL
        if rel_path.startswith("http://") or rel_path.startswith("https://"):
            return match.group(0)

        # Create absolute URL
        abs_url = f"{base_url.rstrip('/')}/{rel_path.lstrip('/')}"
        return f"[{title}]({abs_url})"

    return re.sub(pattern, replace_link, markdown_content)


async def generate_llms_txt_content(base_url: str) -> str:
    """
    Generate llms.txt content with fallback strategy:
    1. PRIMARY: Use curated llms.txt from DOCS_ROOT if exists
    2. FALLBACK: Generate from sidebar.md + index.md
    Returns the content as a string.
    """
    # PRIMARY: Check if curated llms.txt exists in DOCS_ROOT
    llms_txt_path = settings.DOCS_ROOT / "llms.txt"

    if llms_txt_path.exists():
        # Use curated llms.txt (manually created, follows spec)
        content = llms_txt_path.read_text(encoding="utf-8")
        logger.info("Using curated llms.txt from DOCS_ROOT")
    else:
        # FALLBACK: Generate from sidebar.md + index.md
        logger.info("llms.txt not found, generating from sidebar.md + index.md")

        sidebar_path = settings.DOCS_ROOT / "sidebar.md"
        index_path = settings.DOCS_ROOT / "index.md"

        sidebar_content = ""
        if sidebar_path.exists():
            sidebar_content = sidebar_path.read_text(encoding="utf-8")

        index_content = ""
        if index_path.exists():
            index_content = index_path.read_text(encoding="utf-8")

        # Concatenate with separator
        content = f"{sidebar_content}\n\n---\n\n{index_content}" if sidebar_content else index_content

    # Transform relative links to absolute URLs
    result = transform_relative_to_absolute(content, base_url)
    return result
