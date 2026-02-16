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


def path_to_doc_url(path: str) -> str:
    """
    Convert SearchResult.path (e.g. features/mcp.md) to doc URL (/features/mcp.html).
    """
    if path.endswith(".md"):
        path = path[:-3] + ".html"
    return "/" + path.lstrip("/")


def _strip_whoosh_highlight_html(text: str) -> str:
    """Remove Whoosh highlight tags (<b class='match term0'>...</b>) to get plain text."""
    return re.sub(r"</?b[^>]*>", "", text)


def format_search_results_human(results: list[Any], query: str = "") -> str:
    """
    Format search results as human-readable HTML cards.

    Each result is rendered as a card with title (linked), path breadcrumb,
    snippet, and score badge. The output is a self-contained HTML fragment
    suitable for injection into the search page results div.

    Args:
        results: List of SearchResult objects (path, title, snippet, score, category).
        query: The original search query (used for highlighting).

    Returns:
        HTML string with result cards, or a "no results" message.
    """
    from html import escape as html_escape

    if not results:
        safe_q = html_escape(query) if query else ""
        if safe_q:
            return f"<p class='search-no-results'>No results found for &lsquo;{safe_q}&rsquo;</p>"
        return "<p class='search-no-results'>Enter a search term to find documentation.</p>"

    count = len(results)
    parts: list[str] = [f"<p class='search-result-count'>Found {count} result{'s' if count != 1 else ''}:</p>"]

    for result in results:
        url = path_to_doc_url(result.path)
        safe_title = html_escape(result.title)
        safe_path = html_escape(result.path)
        # Strip Whoosh HTML, escape, then we apply our own highlight
        plain_snippet = _strip_whoosh_highlight_html(result.snippet) if result.snippet else ""
        safe_snippet = html_escape(plain_snippet) if plain_snippet else ""
        safe_category = html_escape(result.category) if result.category else ""

        card = "<div class='search-result-card'>"
        card += f"<a href='{url}' class='search-result-title'>{safe_title}</a>"
        if safe_category:
            card += f"<span class='search-result-category'>{safe_category}</span>"
        card += f"<span class='search-result-path'>{safe_path}</span>"
        if safe_snippet:
            card += f"<p class='search-result-snippet'>{safe_snippet}</p>"
        card += "</div>"
        parts.append(card)

    html_out = "\n".join(parts)
    if query:
        html_out = highlight_search_terms(html_out, query)
    return html_out


def highlight_search_terms(html: str, query: str) -> str:
    """
    Wrap search term matches in <mark class="search-highlight"> for pale yellow highlighting.
    Matches case-insensitively (e.g. q=mcp highlights both "MCP" and "mcp").
    """
    if not query or not query.strip():
        return html
    term = query.strip()
    pattern = re.compile(re.escape(term), re.IGNORECASE)
    return pattern.sub(lambda m: f'<mark class="search-highlight">{m.group(0)}</mark>', html)


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


def _normalize_nav_link_to_root(link: str) -> str:
    """
    Normalize navigation links (from sidebar.md, topbar.md) to be root-relative.
    These files live at DOCS_ROOT, so links like 'dir/page.html' must become
    '/dir/page.html' to resolve correctly regardless of the current page URL.
    """
    link = link.strip()
    if not link:
        return link
    # Skip external URLs
    if link.startswith(("http://", "https://", "//", "mailto:", "tel:")):
        return link
    # Skip same-page anchors and query strings
    if link.startswith("#") or link.startswith("?"):
        return link
    # Make root-relative for internal document links
    if not link.startswith("/"):
        return "/" + link
    return link


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

                # Handle special logo syntax: {{logo}} | [Home](index.html)
                if item_text.startswith("{{logo}}"):
                    # Extract the part after the pipe
                    if "|" in item_text:
                        after_pipe = item_text.split("|", 1)[1].strip()
                        # Check if it's a link
                        link_match = re.match(r"\[([^\]]+)\]\(([^)]+)\)", after_pipe)
                        if link_match:
                            title, link = link_match.groups()
                            if link.endswith(".md"):
                                link = link.replace(".md", ".html")
                            link = _normalize_nav_link_to_root(link)
                            sections[current_section].append({"type": "logo_link", "title": title, "link": link})
                        else:
                            # Just text after pipe
                            sections[current_section].append({"type": "logo_text", "title": after_pipe})
                    else:
                        # Just logo without pipe
                        sections[current_section].append({"type": "logo_only"})
                    logger.debug(f"Added logo item to {current_section}")

                # Handle {{search}} or {{search:params}} placeholder
                elif item_text == "{{search}}" or item_text.startswith("{{search:"):
                    params: dict[str, str] = {}
                    if ":" in item_text:
                        params_str = item_text.split(":", 1)[1].rstrip("}}")
                        for pair in params_str.split(","):
                            pair = pair.strip()
                            if "=" in pair:
                                k, v = pair.split("=", 1)
                                params[k.strip().lower()] = v.strip()
                    sections[current_section].append({"type": "search", "params": params})
                    logger.debug(f"Added search placeholder to {current_section} with params {params}")

                # Handle regular markdown links: [Title](link)
                elif "[" in item_text and "](" in item_text:
                    link_match = re.match(r"\[([^\]]+)\]\(([^)]+)\)", item_text)
                    if link_match:
                        title, link = link_match.groups()
                        if link.endswith(".md"):
                            link = link.replace(".md", ".html")
                        link = _normalize_nav_link_to_root(link)
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
                    html_link = _normalize_nav_link_to_root(html_link)
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
                    html_link = _normalize_nav_link_to_root(html_link)
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
