"""
Unit tests for main module.
Tests CLI argument parsing, main() entry point, and key routes.
"""

import sys
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient


def test_main_calls_clear_cache_when_flag_passed():
    """Test that main() calls settings.clear_cache() when --clear-cache is passed"""
    with (
        patch("docs_server.main.settings") as mock_settings,
        patch("uvicorn.run") as mock_uvicorn,
    ):
        with patch.object(sys, "argv", ["docs_server", "--clear-cache"]):
            from docs_server.main import main

            main()

        mock_settings.clear_cache.assert_called_once()
        mock_uvicorn.assert_called_once()


def test_main_does_not_call_clear_cache_without_flag():
    """Test that main() does not call settings.clear_cache() when flag is omitted"""
    with (
        patch("docs_server.main.settings") as mock_settings,
        patch("uvicorn.run") as mock_uvicorn,
    ):
        with patch.object(sys, "argv", ["docs_server"]):
            from docs_server.main import main

            main()

        mock_settings.clear_cache.assert_not_called()
        mock_uvicorn.assert_called_once()


def test_main_passes_proxy_headers_to_uvicorn():
    """uvicorn.run() must receive proxy_headers=True and forwarded_allow_ips from settings."""
    with (
        patch("docs_server.main.settings") as mock_settings,
        patch("uvicorn.run") as mock_uvicorn,
    ):
        mock_settings.PORT = 8080
        mock_settings.DEBUG = False
        mock_settings.FORWARDED_ALLOW_IPS = "127.0.0.1"
        with patch.object(sys, "argv", ["docs_server"]):
            from docs_server.main import main

            main()

        call_kwargs = mock_uvicorn.call_args.kwargs
        assert call_kwargs.get("proxy_headers") is True
        assert call_kwargs.get("forwarded_allow_ips") == "127.0.0.1"


def test_main_forwards_custom_allow_ips():
    """forwarded_allow_ips is taken from settings.FORWARDED_ALLOW_IPS."""
    with (
        patch("docs_server.main.settings") as mock_settings,
        patch("uvicorn.run") as mock_uvicorn,
    ):
        mock_settings.PORT = 8080
        mock_settings.DEBUG = False
        mock_settings.FORWARDED_ALLOW_IPS = "*"
        with patch.object(sys, "argv", ["docs_server"]):
            from docs_server.main import main

            main()

        assert mock_uvicorn.call_args.kwargs["forwarded_allow_ips"] == "*"


def test_main_parses_clear_cache_with_other_args():
    """Test that --clear-cache is parsed correctly alongside other args (parse_known_args)"""
    with (
        patch("docs_server.main.settings") as mock_settings,
        patch("uvicorn.run") as mock_uvicorn,
    ):
        with patch.object(sys, "argv", ["docs_server", "--clear-cache", "extra"]):
            from docs_server.main import main

            main()

        mock_settings.clear_cache.assert_called_once()
        mock_uvicorn.assert_called_once()


# ---------------------------------------------------------------------------
# /about_servemd route
# ---------------------------------------------------------------------------


@pytest.fixture
def temp_docs_for_servemd(tmp_path):
    """Minimal docs root for /about_servemd route tests."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Home\n\nWelcome.")
    (docs_dir / "sidebar.md").write_text("# Nav\n\n* [Home](index.md)")
    (docs_dir / "topbar.md").write_text("# Top\n\n## right\n* [Docs](index.md)")
    return docs_dir


@pytest.mark.asyncio
async def test_servemd_route_returns_200(temp_docs_for_servemd):
    """GET /about_servemd returns a 200 HTML response."""
    from docs_server.main import app

    with patch("docs_server.main.settings") as mock_settings:
        mock_settings.DOCS_ROOT = temp_docs_for_servemd
        mock_settings.BASE_URL = "https://docs.example.com"
        mock_settings.MCP_ENABLED = True
        mock_settings.SERVEMD_BRANDING_ENABLED = True
        mock_settings.DEBUG = False
        mock_settings.CUSTOM_CSS = "custom.css"

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/about_servemd")

    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "About ServeMD" in response.text
    assert "https://docs.example.com/mcp" in response.text


@pytest.mark.asyncio
async def test_servemd_route_shows_mcp_disabled(temp_docs_for_servemd):
    """GET /about_servemd with MCP disabled shows disabled status, no install buttons."""
    from docs_server.main import app

    with patch("docs_server.main.settings") as mock_settings:
        mock_settings.DOCS_ROOT = temp_docs_for_servemd
        mock_settings.BASE_URL = "https://docs.example.com"
        mock_settings.MCP_ENABLED = False
        mock_settings.SERVEMD_BRANDING_ENABLED = True
        mock_settings.DEBUG = False
        mock_settings.CUSTOM_CSS = "custom.css"

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/about_servemd")

    assert response.status_code == 200
    assert "mcp-status-disabled" in response.text
    # The install buttons (deep links) must not be present when MCP is disabled
    assert "cursor://anysphere.cursor-deeplink" not in response.text
    assert "vscode://mcp/install" not in response.text
