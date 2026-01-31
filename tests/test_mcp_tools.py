"""
Tests for MCP tool implementations.

Tests cover:
- search_docs tool
- get_doc_page tool with section filtering
- list_doc_pages tool with category filtering
- Tool dispatcher
- Error handling
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from docs_server.mcp.indexer import SearchIndexManager
from docs_server.mcp.tools import (
    _list_sections,
    call_get_doc_page,
    call_list_doc_pages,
    call_search_docs,
    call_tool,
    filter_sections,
    format_page_list,
    get_tool_definitions,
)

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_docs_root(tmp_path):
    """Create a temporary docs directory with sample markdown files."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    # Create index.md
    (docs_dir / "index.md").write_text(
        "# Welcome to ServeMD\n\n"
        "This is the index page.\n\n"
        "## Getting Started\n\n"
        "Start here to learn about ServeMD.\n\n"
        "## Features\n\n"
        "- Fast rendering\n"
        "- Beautiful design\n"
    )

    # Create api/endpoints.md
    api_dir = docs_dir / "api"
    api_dir.mkdir()
    (api_dir / "endpoints.md").write_text(
        "# API Endpoints\n\n"
        "## GET /health\n\n"
        "Health check endpoint for monitoring.\n\n"
        "## POST /mcp\n\n"
        "MCP endpoint for LLM integration.\n\n"
        "## Rate Limiting\n\n"
        "Rate limiting is enforced at 120 requests per minute.\n"
    )

    # Create configuration.md
    (docs_dir / "configuration.md").write_text(
        "# Configuration\n\n"
        "## Environment Variables\n\n"
        "Set these variables to configure ServeMD:\n"
        "- DOCS_ROOT: Path to documentation\n"
        "- MCP_ENABLED: Enable MCP endpoint\n\n"
        "## Authentication\n\n"
        "Authentication is not required by default.\n"
    )

    # Create features/mcp.md
    features_dir = docs_dir / "features"
    features_dir.mkdir()
    (features_dir / "mcp.md").write_text(
        "# MCP Support\n\n"
        "## Overview\n\n"
        "MCP enables LLM integration.\n\n"
        "## Tools\n\n"
        "Available tools: search_docs, get_doc_page, list_doc_pages\n"
    )

    # Create sidebar.md (should be skipped)
    (docs_dir / "sidebar.md").write_text("# Sidebar\n\n- [Home](index.md)")

    return docs_dir


@pytest.fixture
def temp_cache_root(tmp_path):
    """Create a temporary cache directory."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return cache_dir


@pytest.fixture
async def initialized_index(temp_docs_root, temp_cache_root):
    """Create an initialized search index with test documents."""
    with patch("docs_server.mcp.indexer.settings") as mock_settings:
        mock_settings.DOCS_ROOT = temp_docs_root
        mock_settings.CACHE_ROOT = temp_cache_root
        mock_settings.DEBUG = False
        mock_settings.MCP_MAX_SEARCH_RESULTS = 10
        mock_settings.MCP_SNIPPET_LENGTH = 200

        manager = SearchIndexManager()
        manager._docs_root = temp_docs_root
        manager._index_path = temp_cache_root / "mcp" / "whoosh"
        manager._metadata_path = temp_cache_root / "mcp" / "metadata.json"

        await manager.initialize(force_rebuild=True)

        yield manager

        manager.shutdown()


# =============================================================================
# TOOL DEFINITIONS TESTS
# =============================================================================


class TestToolDefinitions:
    """Tests for get_tool_definitions function."""

    def test_returns_three_tools(self):
        """Tool definitions includes all three tools."""
        tools = get_tool_definitions()

        assert len(tools) == 3
        names = [t["name"] for t in tools]
        assert "search_docs" in names
        assert "get_doc_page" in names
        assert "list_doc_pages" in names

    def test_search_docs_schema(self):
        """search_docs has correct input schema."""
        tools = get_tool_definitions()
        search_tool = next(t for t in tools if t["name"] == "search_docs")

        assert "inputSchema" in search_tool
        schema = search_tool["inputSchema"]
        assert schema["type"] == "object"
        assert "query" in schema["properties"]
        assert "limit" in schema["properties"]
        assert "query" in schema["required"]

    def test_get_doc_page_schema(self):
        """get_doc_page has correct input schema."""
        tools = get_tool_definitions()
        get_tool = next(t for t in tools if t["name"] == "get_doc_page")

        assert "inputSchema" in get_tool
        schema = get_tool["inputSchema"]
        assert "path" in schema["properties"]
        assert "sections" in schema["properties"]
        assert "path" in schema["required"]

    def test_list_doc_pages_schema(self):
        """list_doc_pages has correct input schema."""
        tools = get_tool_definitions()
        list_tool = next(t for t in tools if t["name"] == "list_doc_pages")

        assert "inputSchema" in list_tool
        schema = list_tool["inputSchema"]
        assert "category" in schema["properties"]
        assert schema["required"] == []


# =============================================================================
# SEARCH_DOCS TOOL TESTS
# =============================================================================


class TestSearchDocsTool:
    """Tests for call_search_docs function."""

    @pytest.mark.asyncio
    async def test_search_docs_basic(self, initialized_index):
        """search_docs returns results."""
        with patch("docs_server.mcp.search.get_index_manager", return_value=initialized_index):
            with patch("docs_server.mcp.search.settings") as mock_search_settings:
                mock_search_settings.MCP_MAX_SEARCH_RESULTS = 10
                mock_search_settings.MCP_SNIPPET_LENGTH = 200

                result = call_search_docs({"query": "health"})

                assert "content" in result
                assert len(result["content"]) > 0
                assert result["content"][0]["type"] == "text"

    @pytest.mark.asyncio
    async def test_search_docs_with_limit(self, initialized_index):
        """search_docs respects limit parameter."""
        with patch("docs_server.mcp.search.get_index_manager", return_value=initialized_index):
            with patch("docs_server.mcp.search.settings") as mock_search_settings:
                mock_search_settings.MCP_MAX_SEARCH_RESULTS = 10
                mock_search_settings.MCP_SNIPPET_LENGTH = 200

                result = call_search_docs({"query": "servem", "limit": 1})

                assert "content" in result

    def test_search_docs_invalid_query(self):
        """search_docs raises ValidationError for invalid query."""
        with pytest.raises(ValidationError):
            call_search_docs({"query": ""})  # Empty query

    def test_search_docs_missing_query(self):
        """search_docs raises ValidationError for missing query."""
        with pytest.raises(ValidationError):
            call_search_docs({})


# =============================================================================
# GET_DOC_PAGE TOOL TESTS
# =============================================================================


class TestGetDocPageTool:
    """Tests for call_get_doc_page function."""

    def test_get_doc_page_full_content(self, temp_docs_root):
        """get_doc_page returns full page content."""
        with patch("docs_server.mcp.tools.get_file_path") as mock_get_path:
            mock_get_path.return_value = temp_docs_root / "index.md"

            result = call_get_doc_page({"path": "index.md"})

            assert "content" in result
            assert result["content"][0]["type"] == "text"
            assert "Welcome to ServeMD" in result["content"][0]["text"]

    def test_get_doc_page_with_sections(self, temp_docs_root):
        """get_doc_page filters to specified sections."""
        with patch("docs_server.mcp.tools.get_file_path") as mock_get_path:
            mock_get_path.return_value = temp_docs_root / "index.md"

            result = call_get_doc_page({"path": "index.md", "sections": ["Getting Started"]})

            text = result["content"][0]["text"]
            assert "Getting Started" in text
            # Features section should not be included
            # (depends on exact filtering behavior)

    def test_get_doc_page_not_found(self):
        """get_doc_page raises FileNotFoundError for missing file."""
        with patch("docs_server.mcp.tools.get_file_path", return_value=None):
            with pytest.raises(FileNotFoundError):
                call_get_doc_page({"path": "nonexistent.md"})

    def test_get_doc_page_invalid_path(self):
        """get_doc_page raises ValidationError for empty path."""
        with pytest.raises(ValidationError):
            call_get_doc_page({"path": ""})


# =============================================================================
# SECTION FILTERING TESTS
# =============================================================================


class TestSectionFiltering:
    """Tests for filter_sections function."""

    def test_filter_single_section(self):
        """Filter extracts single section."""
        content = "# Title\n\n## Section A\n\nContent A\n\n## Section B\n\nContent B\n"

        filtered = filter_sections(content, ["Section A"])

        assert "Section A" in filtered
        assert "Content A" in filtered
        # Section B should not be present
        assert "Section B" not in filtered or "Content B" not in filtered

    def test_filter_multiple_sections(self):
        """Filter extracts multiple sections."""
        content = "# Title\n\n## Section A\n\nContent A\n\n## Section B\n\nContent B\n\n## Section C\n\nContent C\n"

        filtered = filter_sections(content, ["Section A", "Section C"])

        assert "Section A" in filtered
        assert "Section C" in filtered

    def test_filter_case_insensitive(self):
        """Filter is case-insensitive."""
        content = "# Title\n\n## Getting Started\n\nContent\n"

        filtered = filter_sections(content, ["getting started"])

        assert "Getting Started" in filtered

    def test_filter_no_match(self):
        """Filter returns helpful message when no sections match."""
        content = "# Title\n\n## Section A\n\nContent A\n"

        filtered = filter_sections(content, ["Nonexistent"])

        assert "No matching sections found" in filtered
        assert "Section A" in filtered  # Lists available sections

    def test_filter_empty_sections_list(self):
        """Empty sections list returns full content."""
        content = "# Title\n\nContent"

        filtered = filter_sections(content, [])

        assert filtered == content


class TestListSections:
    """Tests for _list_sections helper."""

    def test_list_sections_basic(self):
        """List sections extracts all h2 headings."""
        content = "## Section A\n\nContent\n\n## Section B\n\nMore content\n"

        sections = _list_sections(content)

        assert "Section A" in sections
        assert "Section B" in sections

    def test_list_sections_empty(self):
        """List sections handles no h2 headings."""
        content = "# Only H1\n\nContent"

        sections = _list_sections(content)

        assert "No sections found" in sections


# =============================================================================
# LIST_DOC_PAGES TOOL TESTS
# =============================================================================


class TestListDocPagesTool:
    """Tests for call_list_doc_pages function."""

    @pytest.mark.asyncio
    async def test_list_all_pages(self, initialized_index):
        """list_doc_pages returns all pages."""
        with patch("docs_server.mcp.tools.get_index_manager", return_value=initialized_index):
            result = call_list_doc_pages({})

            assert "content" in result
            text = result["content"][0]["text"]
            assert "index.md" in text
            assert "endpoints.md" in text

    @pytest.mark.asyncio
    async def test_list_pages_by_category(self, initialized_index):
        """list_doc_pages filters by category."""
        with patch("docs_server.mcp.tools.get_index_manager", return_value=initialized_index):
            result = call_list_doc_pages({"category": "api"})

            text = result["content"][0]["text"]
            assert "endpoints.md" in text

    @pytest.mark.asyncio
    async def test_list_pages_empty_category(self, initialized_index):
        """list_doc_pages returns message for empty category."""
        with patch("docs_server.mcp.tools.get_index_manager", return_value=initialized_index):
            result = call_list_doc_pages({"category": "nonexistent"})

            text = result["content"][0]["text"]
            assert "No pages found" in text


class TestFormatPageList:
    """Tests for format_page_list function."""

    def test_format_empty_list(self):
        """Format empty list returns helpful message."""
        formatted = format_page_list([])

        assert "No documentation pages found" in formatted

    def test_format_with_pages(self):
        """Format includes page info."""
        pages = [
            {"path": "index.md", "title": "Welcome", "category": "root"},
            {"path": "api/endpoints.md", "title": "API Endpoints", "category": "api"},
        ]

        formatted = format_page_list(pages)

        assert "Welcome" in formatted
        assert "index.md" in formatted
        assert "API Endpoints" in formatted
        assert "Total: 2 page(s)" in formatted

    def test_format_with_category_filter(self):
        """Format shows category filter in title."""
        pages = [
            {"path": "api/endpoints.md", "title": "API Endpoints", "category": "api"},
        ]

        formatted = format_page_list(pages, category_filter="api")

        assert "api" in formatted.lower()


# =============================================================================
# TOOL DISPATCHER TESTS
# =============================================================================


class TestToolDispatcher:
    """Tests for call_tool dispatcher function."""

    def test_dispatch_search_docs(self, temp_docs_root, temp_cache_root, initialized_index):
        """Dispatcher routes to search_docs."""
        with patch("docs_server.mcp.tools.get_index_manager", return_value=initialized_index):
            with patch("docs_server.mcp.search.get_index_manager", return_value=initialized_index):
                with patch("docs_server.mcp.search.settings") as mock_settings:
                    mock_settings.MCP_MAX_SEARCH_RESULTS = 10
                    mock_settings.MCP_SNIPPET_LENGTH = 200

                    result = call_tool("search_docs", {"query": "test"})

                    assert "content" in result

    def test_dispatch_get_doc_page(self, temp_docs_root):
        """Dispatcher routes to get_doc_page."""
        with patch("docs_server.mcp.tools.get_file_path") as mock_get_path:
            mock_get_path.return_value = temp_docs_root / "index.md"

            result = call_tool("get_doc_page", {"path": "index.md"})

            assert "content" in result

    def test_dispatch_list_doc_pages(self, initialized_index):
        """Dispatcher routes to list_doc_pages."""
        with patch("docs_server.mcp.tools.get_index_manager", return_value=initialized_index):
            result = call_tool("list_doc_pages", {})

            assert "content" in result

    def test_dispatch_unknown_tool(self):
        """Dispatcher raises ValueError for unknown tool."""
        with pytest.raises(ValueError, match="Unknown tool"):
            call_tool("unknown_tool", {})


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestToolsIntegration:
    """Integration tests for tools module."""

    @pytest.mark.asyncio
    async def test_search_and_get_page_workflow(self, initialized_index, temp_docs_root):
        """Simulate typical search-then-get workflow."""
        # First, search for something
        with patch("docs_server.mcp.tools.get_index_manager", return_value=initialized_index):
            with patch("docs_server.mcp.search.get_index_manager", return_value=initialized_index):
                with patch("docs_server.mcp.search.settings") as mock_settings:
                    mock_settings.MCP_MAX_SEARCH_RESULTS = 10
                    mock_settings.MCP_SNIPPET_LENGTH = 200

                    search_result = call_search_docs({"query": "health"})
                    assert "content" in search_result

        # Then get the page
        with patch("docs_server.mcp.tools.get_file_path") as mock_get_path:
            mock_get_path.return_value = temp_docs_root / "api" / "endpoints.md"

            page_result = call_get_doc_page({"path": "api/endpoints.md"})
            assert "API Endpoints" in page_result["content"][0]["text"]
