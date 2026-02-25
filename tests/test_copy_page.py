"""
Tests for the Copy page dropdown (Nuxt UI-style) on doc pages.

Tests cover:
- Dropdown present on doc pages with correct ChatGPT/Claude URLs
- Dropdown absent on search page
- URL formats for AI links
"""

from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from docs_server.main import app


@pytest.fixture
def temp_docs(tmp_path):
    """Create temporary docs with required files."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# Welcome\n\nHome page.")
    (docs / "sidebar.md").write_text("# Nav\n\n* [Home](index.md)")
    (docs / "topbar.md").write_text("# Top\n\n## right\n* [Link](index.md)")
    features = docs / "features"
    features.mkdir()
    (features / "mcp.md").write_text("# MCP\n\nModel Context Protocol.")
    return docs


@pytest.mark.asyncio
async def test_doc_page_has_copy_page_dropdown(temp_docs):
    """GET doc page returns HTML with Copy page dropdown."""
    from docs_server import config

    with (
        patch("docs_server.main.settings") as mock_settings,
        patch.object(config.settings, "DOCS_ROOT", temp_docs),
        patch.object(config.settings, "CACHE_ROOT", temp_docs / "cache"),
    ):
        mock_settings.DOCS_ROOT = temp_docs
        mock_settings.CACHE_ROOT = temp_docs / "cache"
        mock_settings.MCP_ENABLED = False
        mock_settings.SERVEMD_BRANDING_ENABLED = True
        mock_settings.BASE_URL = None

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://localhost:8080",
        ) as client:
            response = await client.get("/features/mcp.html")

    assert response.status_code == 200
    html = response.text
    assert "page-actions" in html
    assert "Copy page" in html
    assert "Open in Mistral Le Chat" in html
    assert "Open in ChatGPT" in html
    assert "Open in Claude" in html
    assert "View as Markdown" in html
    assert "chatgpt.com/?prompt=Read+" in html
    assert "claude.ai/new?q=Read%20" in html
    assert "features/mcp.md" in html


@pytest.mark.asyncio
async def test_search_page_has_no_copy_page_dropdown(temp_docs):
    """GET /search returns HTML without Copy page dropdown."""
    with (
        patch("docs_server.main.settings") as mock_settings,
        patch("docs_server.mcp.get_index_manager") as mock_get_manager,
    ):
        mock_settings.DOCS_ROOT = temp_docs
        mock_settings.CACHE_ROOT = temp_docs / "cache"
        mock_settings.MCP_ENABLED = False
        mock_settings.SERVEMD_BRANDING_ENABLED = True

        mock_manager = type("Manager", (), {"is_initialized": False})()
        mock_get_manager.return_value = mock_manager

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://localhost:8080",
        ) as client:
            response = await client.get("/search?q=test")

    assert response.status_code == 200
    html = response.text
    assert "search-page" in html
    # Dropdown menu item only appears when page_actions rendered (not on search page)
    assert "Copy Markdown link" not in html


@pytest.mark.asyncio
async def test_copy_page_uses_base_url_when_set(temp_docs):
    """When BASE_URL is set, AI links use it for raw markdown URL."""
    from docs_server import config

    with (
        patch.object(config.settings, "DOCS_ROOT", temp_docs),
        patch.object(config.settings, "CACHE_ROOT", temp_docs / "cache"),
        patch.object(config.settings, "BASE_URL", "https://docs.example.com"),
        patch.object(config.settings, "MCP_ENABLED", False),
        patch.object(config.settings, "SERVEMD_BRANDING_ENABLED", True),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://localhost:8080",
        ) as client:
            response = await client.get("/features/mcp.html")

    assert response.status_code == 200
    html = response.text
    assert "https://docs.example.com/features/mcp.md" in html
    assert "chat.mistral.ai/chat?q=Read+" in html
    assert "chatgpt.com/?prompt=Read+https%3A%2F%2Fdocs.example.com%2Ffeatures%2Fmcp.md" in html


@pytest.mark.asyncio
async def test_copy_page_upgrades_http_to_https_via_forwarded_proto(temp_docs):
    """When X-Forwarded-Proto: https is present and BASE_URL is unset, AI links use https://."""
    from docs_server import config

    with (
        patch.object(config.settings, "DOCS_ROOT", temp_docs),
        patch.object(config.settings, "CACHE_ROOT", temp_docs / "cache"),
        patch.object(config.settings, "BASE_URL", None),
        patch.object(config.settings, "MCP_ENABLED", False),
        patch.object(config.settings, "SERVEMD_BRANDING_ENABLED", True),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://localhost:8080",
        ) as client:
            response = await client.get(
                "/features/mcp.html",
                headers={"x-forwarded-proto": "https"},
            )

    assert response.status_code == 200
    html = response.text
    assert "https://localhost:8080/features/mcp.md" in html
    assert "http://localhost:8080/features/mcp.md" not in html
    assert "chatgpt.com/?prompt=Read+https%3A%2F%2Flocalhost%3A8080%2Ffeatures%2Fmcp.md" in html
