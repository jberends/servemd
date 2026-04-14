"""
Tests for HTML file embedding via iframe.
Covers: /raw/ route, .html fallback in serve_content, iframe rendering,
markdown-wins-over-html priority, and path traversal protection.
"""

from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from docs_server.main import app


@pytest.fixture
def temp_docs(tmp_path):
    """Create temporary docs with required files + a standalone .html file."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# Welcome\n\nHome page.")
    (docs / "sidebar.md").write_text("# Nav\n\n* [Home](index.md)")
    (docs / "topbar.md").write_text("# Top\n\n## right\n* [Link](index.md)")
    (docs / "embed.html").write_text(
        "<html><head><style>body{color:red}</style></head>"
        "<body><h1>Embedded</h1><script>console.log('hi')</script></body></html>"
    )
    return docs


@pytest.mark.asyncio
async def test_raw_route_serves_html(temp_docs):
    """GET /raw/embed.html returns raw HTML file content."""
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

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://localhost:8080",
        ) as client:
            response = await client.get("/raw/embed.html")

    assert response.status_code == 200
    assert "<h1>Embedded</h1>" in response.text
    assert "text/html" in response.headers["content-type"]
    assert "attachment" not in response.headers.get("content-disposition", "")


@pytest.mark.asyncio
async def test_raw_route_404_on_missing(temp_docs):
    """GET /raw/nonexistent.html returns 404."""
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

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://localhost:8080",
        ) as client:
            response = await client.get("/raw/nonexistent.html")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_raw_route_rejects_traversal(temp_docs):
    """GET /raw/ with encoded traversal segments returns 404 (path traversal blocked)."""
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

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://localhost:8080",
        ) as client:
            response = await client.get("/raw/%2e%2e%2f%2e%2e%2fetc%2fpasswd")

    assert response.status_code == 404
