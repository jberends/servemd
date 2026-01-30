"""
Markdown processing service for ServeMD Documentation Server.
Handles markdown-to-HTML conversion with extensions.
"""

import logging
from pathlib import Path

import markdown

from .config import settings
from .helpers import convert_md_links_to_html

logger = logging.getLogger(__name__)


async def render_markdown_to_html(content: str, file_path: Path) -> str:
    """
    Render markdown content to HTML with all extensions and link conversion.
    """
    # Convert .md links to .html for rendered mode
    processed_content = convert_md_links_to_html(content)

    # Initialize markdown processor
    md = markdown.Markdown(
        extensions=settings.markdown_extensions, extension_configs=settings.markdown_extension_configs
    )

    # Render to HTML
    html_content = md.convert(processed_content)

    return html_content
