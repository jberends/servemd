"""
Helper utilities and navigation parsing for ServeMD Documentation Server.
Contains pure utility functions and navigation structure parsers.
"""

import logging
import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from .config import settings

logger = logging.getLogger(__name__)


def is_safe_path(path: str, base_path: Path) -> bool:
    """
    Validate that the requested path is within the allowed directory boundaries.
    Prevents directory traversal attacks.
    """
    try:
        # Resolve absolute paths
        abs_base = base_path.resolve()
        abs_path = (base_path / path).resolve()

        # Check if the resolved path is within the base directory
        # Use commonpath for compatibility with older Python versions
        return os.path.commonpath([abs_base, abs_path]) == str(abs_base)
    except (ValueError, OSError):
        return False


def get_file_path(requested_path: str) -> Path | None:
    """
    Get the actual file path for a requested resource.
    Returns None if the path is unsafe or file doesn't exist.
    """
    # Remove leading slash and decode URL encoding
    clean_path = unquote(requested_path.lstrip("/"))

    # Security check
    if not is_safe_path(clean_path, settings.DOCS_ROOT):
        logger.warning(f"Unsafe path requested: {clean_path}")
        return None

    file_path = settings.DOCS_ROOT / clean_path

    # Check if file exists
    if not file_path.exists() or not file_path.is_file():
        logger.debug(f"File not found: {file_path}")
        return None

    return file_path


def extract_table_of_contents(html_content: str) -> list[dict[str, str]]:
    """
    Extract table of contents from HTML content by finding headings.
    """
    toc_items = []
    # Find all headings with IDs (h1, h2, h3, h4, h5, h6)
    heading_pattern = r'<(h[1-6])[^>]*id="([^"]+)"[^>]*>(.*?)</\1>'

    for match in re.finditer(heading_pattern, html_content, re.IGNORECASE | re.DOTALL):
        tag, heading_id, title = match.groups()
        level = int(tag[1])  # Extract number from h1, h2, etc.

        # Clean up the title (remove any HTML tags like <a> links and paragraph marks)
        clean_title = re.sub(r"<[^>]+>", "", title).strip()
        # Remove paragraph marks and other symbols
        clean_title = clean_title.replace("¶", "").replace("&para;", "").strip()

        toc_items.append({"id": heading_id, "title": clean_title, "level": level})

    return toc_items


def convert_md_links_to_html(content: str) -> str:
    """
    Convert markdown links from .md to .html for rendered HTML mode.
    """
    # Pattern to match markdown links: [text](file.md)
    pattern = r"\[([^\]]+)\]\(([^)]+\.md)\)"

    def replace_link(match):
        text = match.group(1)
        link = match.group(2)
        html_link = link.replace(".md", ".html")
        return f"[{text}]({html_link})"

    return re.sub(pattern, replace_link, content)


def parse_topbar_links() -> dict[str, list[dict[str, str]]]:
    """
    Parse topbar.md file to create structured top navigation with left/middle/right sections.
    """
    topbar_path = settings.DOCS_ROOT / "topbar.md"
    if not topbar_path.exists():
        logger.debug(f"Topbar file not found: {topbar_path}")
        return {"left": [], "middle": [], "right": []}

    try:
        content = topbar_path.read_text(encoding="utf-8")
        sections = {"left": [], "middle": [], "right": []}
        current_section = None

        for line in content.split("\n"):
            line = line.strip()
            if not line:
                continue

            # Section headers (## left, ## middle, ## right)
            if line.startswith("## "):
                section_name = line[3:].strip().lower()
                if section_name in sections:
                    current_section = section_name
                    logger.debug(f"Parsing topbar section: {section_name}")
                continue

            # Skip main title
            if line.startswith("# "):
                continue

            # Parse items in current section
            if current_section and line.startswith("* "):
                item_text = line[2:].strip()

                # Handle special logo syntax: {logo} | [Home](index.html)
                if item_text.startswith("{logo}"):
                    # Extract the part after the pipe
                    if "|" in item_text:
                        after_pipe = item_text.split("|", 1)[1].strip()
                        # Check if it's a link
                        link_match = re.match(r"\[([^\]]+)\]\(([^)]+)\)", after_pipe)
                        if link_match:
                            title, link = link_match.groups()
                            if link.endswith(".md"):
                                link = link.replace(".md", ".html")
                            sections[current_section].append({"type": "logo_link", "title": title, "link": link})
                        else:
                            # Just text after pipe
                            sections[current_section].append({"type": "logo_text", "title": after_pipe})
                    else:
                        # Just logo without pipe
                        sections[current_section].append({"type": "logo_only"})
                    logger.debug(f"Added logo item to {current_section}")

                # Handle regular markdown links: [Title](link)
                elif "[" in item_text and "](" in item_text:
                    link_match = re.match(r"\[([^\]]+)\]\(([^)]+)\)", item_text)
                    if link_match:
                        title, link = link_match.groups()
                        if link.endswith(".md"):
                            link = link.replace(".md", ".html")
                        sections[current_section].append({"type": "link", "title": title, "link": link})
                        logger.debug(f"Added link to {current_section}: {title} -> {link}")

                # Handle plain text items
                else:
                    sections[current_section].append({"type": "text", "title": item_text})
                    logger.debug(f"Added text to {current_section}: {item_text}")

        total_items = sum(len(items) for items in sections.values())
        logger.debug(f"Parsed {total_items} topbar items across {len([s for s in sections.values() if s])} sections")
        return sections

    except Exception as e:
        logger.error(f"Error parsing topbar: {e}")
        return {"left": [], "middle": [], "right": []}


def parse_sidebar_navigation() -> list[dict[str, Any]]:
    """
    Parse sidebar.md file to create navigation structure with proper grouping.
    """
    sidebar_path = settings.DOCS_ROOT / "sidebar.md"
    if not sidebar_path.exists():
        logger.warning(f"Sidebar file not found: {sidebar_path}")
        return []

    try:
        content = sidebar_path.read_text(encoding="utf-8")
        nav_items = []
        current_section = None

        for line in content.split("\n"):
            line = line.rstrip()  # Keep leading spaces for indentation detection

            if not line.strip():
                continue

            # Section headers (# Title)
            if line.strip().startswith("# "):
                continue  # Skip main title

            # Top-level items (* [Title](link.md))
            elif line.startswith("* ["):
                match = re.match(r"\* \[([^\]]+)\]\(([^)]+)\)", line)
                if match:
                    title, link = match.groups()
                    html_link = link.replace(".md", ".html")
                    current_section = {
                        "title": title,
                        "link": html_link,
                        "children": [],
                        "type": "section",  # Will be updated based on children
                    }
                    nav_items.append(current_section)
                    logger.debug(f"Added section: {title}")

            # Sub-items (  * [Title](link.md)) - note the leading spaces
            elif line.startswith("  * [") and current_section is not None:
                match = re.match(r"  \* \[([^\]]+)\]\(([^)]+)\)", line)
                if match:
                    title, link = match.groups()
                    html_link = link.replace(".md", ".html")
                    current_section["children"].append({"title": title, "link": html_link})
                    logger.debug(f"Added child to {current_section['title']}: {title}")

        # Post-process: Determine item types based on Nuxt UI docs pattern
        for item in nav_items:
            if not item["children"]:
                # Standalone items are clickable links
                item["type"] = "link"
            else:
                # Items with children are clickable group headers with children (like Nuxt UI)
                item["type"] = "group_with_children"
                # Keep the link - group headers are clickable in Nuxt UI

        logger.debug(f"Parsed {len(nav_items)} navigation items")
        return nav_items

    except Exception as e:
        logger.error(f"Error parsing sidebar: {e}")
        return []
