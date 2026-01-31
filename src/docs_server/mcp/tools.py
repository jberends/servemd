"""
MCP Tool implementations.

This module implements the MCP tools:
- search_docs: Full-text search across documentation
- get_doc_page: Retrieve a specific documentation page
- list_doc_pages: List all available documentation pages
"""

from __future__ import annotations

import logging
import re
from typing import Any

from ..helpers import get_file_path
from .indexer import get_index_manager
from .models import GetDocPageInput, ListDocPagesInput, SearchDocsInput
from .search import format_search_results, search_docs

logger = logging.getLogger(__name__)


# =============================================================================
# TOOL DEFINITIONS
# =============================================================================


def get_tool_definitions() -> list[dict[str, Any]]:
    """
    Get the list of available MCP tool definitions.

    Returns:
        List of tool definitions with names, descriptions, and input schemas
    """
    return [
        {
            "name": "search_docs",
            "description": (
                "Search the documentation for relevant content. "
                "Supports fuzzy search (use ~ suffix for typo tolerance), "
                "boolean operators (AND, OR, NOT), "
                "field-specific queries (title:xxx), "
                'and phrase search ("exact phrase").'
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (1-500 characters)",
                        "minLength": 1,
                        "maxLength": 500,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results to return (1-50, default 10)",
                        "minimum": 1,
                        "maximum": 50,
                        "default": 10,
                    },
                },
                "required": ["query"],
            },
        },
        {
            "name": "get_doc_page",
            "description": (
                "Retrieve the content of a specific documentation page. "
                "Optionally filter to specific sections by h2 heading names."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path to the documentation file (e.g., 'api/endpoints.md')",
                        "minLength": 1,
                    },
                    "sections": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of h2 section titles to extract (returns full page if not specified)",
                    },
                },
                "required": ["path"],
            },
        },
        {
            "name": "list_doc_pages",
            "description": ("List all available documentation pages. Optionally filter by category (directory name)."),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Optional category filter (e.g., 'api', 'deployment', 'features')",
                    },
                },
                "required": [],
            },
        },
    ]


# =============================================================================
# SEARCH_DOCS TOOL
# =============================================================================


def call_search_docs(arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Execute the search_docs tool.

    Args:
        arguments: Tool arguments containing 'query' and optional 'limit'

    Returns:
        MCP content response with search results

    Raises:
        ValidationError: If arguments are invalid
        RuntimeError: If search fails
    """
    # Validate input
    input_data = SearchDocsInput.model_validate(arguments)

    logger.info(f"search_docs: query='{input_data.query}', limit={input_data.limit}")

    # Execute search
    results = search_docs(input_data.query, input_data.limit)

    # Format results
    formatted = format_search_results(results)

    return {
        "content": [
            {
                "type": "text",
                "text": formatted,
            }
        ]
    }


# =============================================================================
# GET_DOC_PAGE TOOL
# =============================================================================


def call_get_doc_page(arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Execute the get_doc_page tool.

    Args:
        arguments: Tool arguments containing 'path' and optional 'sections'

    Returns:
        MCP content response with page content

    Raises:
        ValidationError: If arguments are invalid
        FileNotFoundError: If page doesn't exist
    """
    # Validate input
    input_data = GetDocPageInput.model_validate(arguments)

    logger.info(f"get_doc_page: path='{input_data.path}', sections={input_data.sections}")

    # Validate and get file path
    file_path = get_file_path(input_data.path)

    if file_path is None:
        raise FileNotFoundError(f"Documentation page not found: {input_data.path}")

    # Read content
    try:
        content = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise FileNotFoundError(f"Error reading page: {e}") from e

    # Filter sections if requested
    if input_data.sections:
        content = filter_sections(content, input_data.sections)

    return {
        "content": [
            {
                "type": "text",
                "text": content,
            }
        ]
    }


def filter_sections(content: str, section_names: list[str]) -> str:
    """
    Filter markdown content to only include specified h2 sections.

    Args:
        content: Full markdown content
        section_names: List of h2 section titles to extract (case-insensitive)

    Returns:
        Filtered content containing only the requested sections
    """
    if not section_names:
        return content

    # Normalize section names for comparison
    normalized_names = {name.lower().strip() for name in section_names}

    # Split content into sections based on ## headings
    # Pattern matches ## heading at start of line
    section_pattern = r"^(##\s+.+)$"
    lines = content.split("\n")

    result_lines: list[str] = []
    current_section_name: str | None = None
    include_current = False
    title_included = False

    for line in lines:
        # Check if this is a h2 heading
        if re.match(section_pattern, line):
            # Extract section name (remove ## prefix)
            section_name = line.lstrip("#").strip()
            current_section_name = section_name.lower()

            # Check if this section should be included
            include_current = current_section_name in normalized_names

            if include_current:
                if result_lines:
                    result_lines.append("")  # Blank line before new section
                result_lines.append(line)

        elif line.startswith("# ") and not title_included:
            # Include the main title (h1)
            result_lines.append(line)
            result_lines.append("")
            title_included = True

        elif include_current:
            # Check if we hit another heading (h1, h3+) which ends the section
            if re.match(r"^#(?!#)", line):
                include_current = False
            else:
                result_lines.append(line)

    if not result_lines or (len(result_lines) == 2 and result_lines[1] == ""):
        # Only title or empty - no sections found
        requested = ", ".join(section_names)
        return f"No matching sections found for: {requested}\n\nAvailable sections in this document:\n{_list_sections(content)}"

    return "\n".join(result_lines).strip()


def _list_sections(content: str) -> str:
    """List all h2 sections in the content."""
    sections = re.findall(r"^##\s+(.+)$", content, re.MULTILINE)
    if sections:
        return "\n".join(f"- {s}" for s in sections)
    return "No sections found"


# =============================================================================
# LIST_DOC_PAGES TOOL
# =============================================================================


def call_list_doc_pages(arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Execute the list_doc_pages tool.

    Args:
        arguments: Tool arguments containing optional 'category'

    Returns:
        MCP content response with list of pages
    """
    # Validate input
    input_data = ListDocPagesInput.model_validate(arguments)

    logger.info(f"list_doc_pages: category='{input_data.category}'")

    manager = get_index_manager()

    if not manager.is_initialized:
        raise RuntimeError("Search index not initialized")

    whoosh_index = manager.get_whoosh_index()
    if whoosh_index is None:
        raise RuntimeError("Search index not available")

    # Get all documents from index
    pages: list[dict[str, str]] = []

    try:
        with whoosh_index.searcher() as searcher:
            for docnum in searcher.document_numbers():
                stored = searcher.stored_fields(docnum)
                page = {
                    "path": stored.get("path", ""),
                    "title": stored.get("title", "Untitled"),
                    "category": stored.get("category", ""),
                }

                # Filter by category if specified
                if input_data.category:
                    if page["category"].lower() == input_data.category.lower():
                        pages.append(page)
                else:
                    pages.append(page)

        # Sort by category then path
        pages.sort(key=lambda p: (p["category"], p["path"]))

        # Format output
        formatted = format_page_list(pages, input_data.category)

        return {
            "content": [
                {
                    "type": "text",
                    "text": formatted,
                }
            ]
        }

    except Exception as e:
        logger.error(f"Error listing pages: {e}", exc_info=True)
        raise RuntimeError(f"Failed to list pages: {e}") from e


def format_page_list(pages: list[dict[str, str]], category_filter: str | None = None) -> str:
    """
    Format the page list as a markdown string.

    Args:
        pages: List of page dictionaries with path, title, category
        category_filter: Optional category that was used for filtering

    Returns:
        Formatted markdown string
    """
    if not pages:
        if category_filter:
            return f"No pages found in category: {category_filter}"
        return "No documentation pages found."

    lines = []

    if category_filter:
        lines.append(f"# Documentation Pages in '{category_filter}'\n")
    else:
        lines.append("# Available Documentation Pages\n")

    # Group by category
    current_category = None

    for page in pages:
        category = page["category"] or "root"

        if category != current_category:
            current_category = category
            lines.append(f"\n## {category.title()}\n")

        lines.append(f"- [{page['title']}]({page['path']})")

    lines.append(f"\n---\nTotal: {len(pages)} page(s)")

    return "\n".join(lines)


# =============================================================================
# TOOL DISPATCHER
# =============================================================================


def call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Dispatch a tool call to the appropriate handler.

    Args:
        name: Tool name
        arguments: Tool arguments

    Returns:
        MCP content response

    Raises:
        ValueError: If tool name is unknown
        ValidationError: If arguments are invalid
        FileNotFoundError: If resource not found
        RuntimeError: If tool execution fails
    """
    handlers = {
        "search_docs": call_search_docs,
        "get_doc_page": call_get_doc_page,
        "list_doc_pages": call_list_doc_pages,
    }

    if name not in handlers:
        raise ValueError(f"Unknown tool: {name}")

    return handlers[name](arguments)
