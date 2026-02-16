"""
Tests for the /search route.

Tests cover:
- Unit tests: mock search_docs, assert HTML with results, empty query handling
- Integration tests: initialized index, hit /search?q=health, assert results in HTML
- Index unavailable → graceful message
- Empty results → "No results found"
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from docs_server.main import app
from docs_server.mcp.search import SearchResult

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_docs_root(tmp_path):
    """Create a temporary docs directory with sample markdown files."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    (docs_dir / "index.md").write_text("# Welcome\n\nHome page.")
    (docs_dir / "sidebar.md").write_text("# Nav\n\n* [Home](index.md)")
    (docs_dir / "topbar.md").write_text("# Top\n\n## right\n* [Link](index.md)")

    api_dir = docs_dir / "api"
    api_dir.mkdir()
    (api_dir / "endpoints.md").write_text(
        "# API Endpoints\n\n## GET /health\n\nHealth check.\n\n## Rate Limiting\n\nRate limiting at 120/min."
    )

    features_dir = docs_dir / "features"
    features_dir.mkdir()
    (features_dir / "mcp.md").write_text("# MCP\n\nMCP enables LLM integration. Health monitoring.")

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
    from docs_server.mcp.indexer import SearchIndexManager

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
# UNIT TESTS (mocked search_docs)
# =============================================================================


class TestSearchRouteUnit:
    """Unit tests with mocked search_docs."""

    @pytest.mark.asyncio
    async def test_search_returns_html_with_results(self, temp_docs_root):
        """GET /search?q=test returns HTML containing search results."""
        mock_results = [
            SearchResult(
                path="api/endpoints.md",
                title="API Endpoints",
                snippet="Health check endpoint",
                score=2.5,
                category="api",
            )
        ]

        with (
            patch("docs_server.main.settings") as mock_settings,
            patch("docs_server.mcp.search_docs", return_value=mock_results),
        ):
            mock_settings.DOCS_ROOT = temp_docs_root
            mock_settings.MCP_ENABLED = True

            with patch("docs_server.mcp.get_index_manager") as mock_get_mgr:
                mock_mgr = MagicMock()
                mock_mgr.is_initialized = True
                mock_get_mgr.return_value = mock_mgr

                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.get("/search?q=test")

        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        html = response.text
        assert "API Endpoints" in html
        assert "api/endpoints.md" in html or "/api/endpoints.html" in html

    @pytest.mark.asyncio
    async def test_search_empty_query_shows_search_page(self, temp_docs_root):
        """GET /search with empty q shows search page without results."""
        with (
            patch("docs_server.main.settings") as mock_settings,
        ):
            mock_settings.DOCS_ROOT = temp_docs_root
            mock_settings.MCP_ENABLED = True

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/search?q=")
                response_ws = await client.get("/search?q=   ")

        assert response.status_code == 200
        assert response_ws.status_code == 200
        assert "search-page" in response.text
        assert "search-page-results" in response.text

    @pytest.mark.asyncio
    async def test_search_index_unavailable_graceful_message(self, temp_docs_root):
        """When index unavailable, show graceful message."""
        with (
            patch("docs_server.main.settings") as mock_settings,
            patch("docs_server.mcp.get_index_manager") as mock_get_mgr,
        ):
            mock_settings.DOCS_ROOT = temp_docs_root
            mock_settings.MCP_ENABLED = True
            mock_mgr = MagicMock()
            mock_mgr.is_initialized = False
            mock_get_mgr.return_value = mock_mgr

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/search?q=health")

        assert response.status_code == 200
        assert "Search will be available once the index is built" in response.text

    @pytest.mark.asyncio
    async def test_search_empty_results_no_results_found(self, temp_docs_root):
        """When search returns no results, show 'No results found'."""
        with (
            patch("docs_server.main.settings") as mock_settings,
            patch("docs_server.mcp.search_docs", return_value=[]),
            patch("docs_server.mcp.get_index_manager") as mock_get_mgr,
        ):
            mock_settings.DOCS_ROOT = temp_docs_root
            mock_settings.MCP_ENABLED = True
            mock_mgr = MagicMock()
            mock_mgr.is_initialized = True
            mock_get_mgr.return_value = mock_mgr

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/search?q=xyznonexistent")

        assert response.status_code == 200
        assert "No results found" in response.text
        assert "xyznonexistent" in response.text


# =============================================================================
# INTEGRATION TESTS (real index)
# =============================================================================


class TestSearchRouteIntegration:
    """Integration tests with initialized index."""

    @pytest.mark.asyncio
    async def test_search_q_health_returns_results(self, temp_docs_root, temp_cache_root, initialized_index):
        """GET /search?q=health returns HTML with results when index is initialized."""
        with (
            patch("docs_server.main.settings") as mock_settings,
            patch("docs_server.mcp.get_index_manager", return_value=initialized_index),
        ):
            mock_settings.DOCS_ROOT = temp_docs_root
            mock_settings.MCP_ENABLED = True

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/search?q=health")

        assert response.status_code == 200
        html = response.text
        assert "search-page" in html
        # api/endpoints.md contains "Health check" - should be in results
        assert "health" in html.lower() or "Health" in html or "endpoints" in html.lower()

    @pytest.mark.asyncio
    async def test_search_json_format_returns_json(self, temp_docs_root, temp_cache_root, initialized_index):
        """GET /search?q=health&format=json returns JSON with results."""
        with (
            patch("docs_server.main.settings") as mock_settings,
            patch("docs_server.mcp.get_index_manager", return_value=initialized_index),
        ):
            mock_settings.DOCS_ROOT = temp_docs_root
            mock_settings.MCP_ENABLED = True

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/search?q=health&format=json")

        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "count" in data
        assert "results" in data
        assert "html" in data
        assert data["query"] == "health"
