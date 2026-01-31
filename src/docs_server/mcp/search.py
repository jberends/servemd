"""
MCP Search Implementation using Whoosh.

This module provides full-text search functionality for documentation.
Uses Whoosh's MultifieldParser for searching across title, content, and headings,
with FuzzyTermPlugin for typo tolerance.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from whoosh.qparser import FuzzyTermPlugin, MultifieldParser

from ..config import settings
from .indexer import get_index_manager

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Represents a single search result."""

    path: str
    title: str
    snippet: str
    score: float
    category: str = ""


def search_docs(query: str, limit: int | None = None) -> list[SearchResult]:
    """
    Search documentation using Whoosh full-text search.

    Features:
    - Multi-field search (title, content, headings)
    - Fuzzy search support for typo tolerance (use ~ suffix)
    - Boolean operators (AND, OR, NOT)
    - Field-specific queries (title:xxx, content:xxx)
    - BM25 scoring with title/headings boosting

    Args:
        query: Search query string. Supports:
            - Simple terms: "authentication"
            - Fuzzy terms: "authentiction~" (typo tolerance)
            - Boolean: "auth AND login"
            - Field-specific: "title:configuration"
            - Phrases: '"rate limiting"'
        limit: Maximum number of results (default: MCP_MAX_SEARCH_RESULTS)

    Returns:
        List of SearchResult objects, sorted by relevance score

    Raises:
        RuntimeError: If search index is not initialized
    """
    if limit is None:
        limit = settings.MCP_MAX_SEARCH_RESULTS

    manager = get_index_manager()

    if not manager.is_initialized:
        logger.error("Search index not initialized")
        raise RuntimeError("Search index not initialized")

    whoosh_index = manager.get_whoosh_index()
    if whoosh_index is None:
        logger.error("Whoosh index not available")
        raise RuntimeError("Search index not available")

    results: list[SearchResult] = []

    try:
        # Create parser for multi-field search
        # Fields: title (2x boost), content, headings (1.5x boost)
        parser = MultifieldParser(
            ["title", "content", "headings"],
            schema=whoosh_index.schema,
        )

        # Add fuzzy search support for typo tolerance
        parser.add_plugin(FuzzyTermPlugin())

        # Parse the query
        parsed_query = parser.parse(query)
        logger.debug(f"Parsed search query: {parsed_query}")

        with whoosh_index.searcher() as searcher:
            # Execute search
            hits = searcher.search(parsed_query, limit=limit)

            for hit in hits:
                # Extract snippet with highlighting
                snippet = _extract_snippet(hit, query)

                results.append(
                    SearchResult(
                        path=hit["path"],
                        title=hit["title"],
                        snippet=snippet,
                        score=hit.score,
                        category=hit.get("category", ""),
                    )
                )

        logger.info(f"Search '{query}' returned {len(results)} results")
        return results

    except Exception as e:
        logger.error(f"Search error for query '{query}': {e}", exc_info=True)
        raise RuntimeError(f"Search failed: {e}") from e


def _extract_snippet(hit, query: str) -> str:
    """
    Extract a relevant snippet from the search hit with highlighting.

    Args:
        hit: Whoosh search hit object
        query: Original search query for highlighting

    Returns:
        Snippet string with relevant content
    """
    try:
        # Try to get highlighted snippet from content_stored field
        snippet = hit.highlights("content_stored", top=1)

        if snippet:
            # Clean up and return the snippet
            return _clean_snippet(snippet)

        # Fall back to headings if no content match
        snippet = hit.highlights("headings", top=1)
        if snippet:
            return _clean_snippet(snippet)

        # Last resort: return beginning of stored content
        content = hit.get("content_stored", "")
        if content:
            # Return first N characters
            max_len = settings.MCP_SNIPPET_LENGTH
            if len(content) > max_len:
                # Try to break at word boundary
                content = content[:max_len].rsplit(" ", 1)[0] + "..."
            return content

        return hit.get("title", "No content available")

    except Exception as e:
        logger.warning(f"Error extracting snippet: {e}")
        return hit.get("title", "No snippet available")


def _clean_snippet(snippet: str) -> str:
    """
    Clean up a Whoosh highlight snippet.

    Removes excessive whitespace and normalizes the text.

    Args:
        snippet: Raw snippet from Whoosh highlighting

    Returns:
        Cleaned snippet string
    """
    # Replace multiple whitespace with single space
    import re

    cleaned = re.sub(r"\s+", " ", snippet)
    # Strip leading/trailing whitespace
    cleaned = cleaned.strip()
    return cleaned


def format_search_results(results: list[SearchResult]) -> str:
    """
    Format search results as a text string for MCP response.

    Args:
        results: List of SearchResult objects

    Returns:
        Formatted string suitable for MCP content response
    """
    if not results:
        return "No results found for your query."

    lines = [f"Found {len(results)} result(s):\n"]

    for i, result in enumerate(results, 1):
        lines.append(f"{i}. **{result.title}** (`{result.path}`)")
        if result.category:
            lines.append(f"   Category: {result.category}")
        lines.append(f"   Score: {result.score:.2f}")
        if result.snippet:
            # Indent snippet
            snippet_lines = result.snippet.split("\n")
            for line in snippet_lines[:3]:  # Max 3 lines of snippet
                lines.append(f"   {line}")
        lines.append("")  # Blank line between results

    # Add search tip
    lines.append("---")
    lines.append("**Tip:** Use `~` for fuzzy search (e.g., `configuraton~` finds 'configuration')")

    return "\n".join(lines)
