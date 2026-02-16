"""
Tests for custom CSS injection feature.
"""

from pathlib import Path
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
    return docs


@pytest.mark.asyncio
async def test_custom_css_endpoint_200_when_file_exists(temp_docs):
    """GET /custom.css returns 200 with text/css when custom.css exists."""
    (temp_docs / "custom.css").write_text("/* custom */ body { color: red; }")

    from docs_server.config import settings

    with (
        patch.object(settings, "DOCS_ROOT", temp_docs),
        patch.object(settings, "CUSTOM_CSS", "custom.css"),
        patch.object(settings, "DEBUG", False),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://localhost:8080",
        ) as client:
            response = await client.get("/custom.css")

    assert response.status_code == 200
    assert "text/css" in response.headers.get("content-type", "")
    assert "body { color: red; }" in response.text


@pytest.mark.asyncio
async def test_custom_css_endpoint_404_when_file_missing(temp_docs):
    """GET /custom.css returns 404 when custom.css does not exist."""
    from docs_server.config import settings

    with (
        patch.object(settings, "DOCS_ROOT", temp_docs),
        patch.object(settings, "CUSTOM_CSS", "custom.css"),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://localhost:8080",
        ) as client:
            response = await client.get("/custom.css")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_custom_css_serves_theme_css_when_configured(temp_docs):
    """CUSTOM_CSS=theme.css serves theme.css at /custom.css."""
    (temp_docs / "theme.css").write_text("/* theme */ :root { --accent: blue; }")

    from docs_server.config import settings

    with (
        patch.object(settings, "DOCS_ROOT", temp_docs),
        patch.object(settings, "CUSTOM_CSS", "theme.css"),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://localhost:8080",
        ) as client:
            response = await client.get("/custom.css")

    assert response.status_code == 200
    assert "--accent: blue" in response.text


def test_template_includes_custom_css_link_when_passed():
    """Template includes link when custom_css_url is passed."""
    from docs_server.templates import create_html_template

    result = create_html_template("<p>Hi</p>", custom_css_url="/custom.css")
    assert 'href="/custom.css"' in result
    assert '<link rel="stylesheet"' in result


def test_template_no_custom_css_link_when_none():
    """Template has no custom CSS link when custom_css_url is None."""
    from docs_server.templates import create_html_template

    result = create_html_template("<p>Hi</p>", custom_css_url=None)
    assert 'href="/custom.css"' not in result


def test_get_custom_css_path_returns_path_when_exists(tmp_path, monkeypatch):
    """get_custom_css_path returns Path when file exists."""
    from docs_server.config import settings
    from docs_server.helpers import get_custom_css_path

    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "custom.css").write_text("/* test */")
    monkeypatch.setattr(settings, "DOCS_ROOT", docs)
    monkeypatch.setattr(settings, "CUSTOM_CSS", "custom.css")

    path = get_custom_css_path()
    assert path is not None
    assert path.name == "custom.css"


def test_get_custom_css_path_returns_none_when_missing(tmp_path, monkeypatch):
    """get_custom_css_path returns None when file does not exist."""
    from docs_server.config import settings
    from docs_server.helpers import get_custom_css_path

    docs = tmp_path / "docs"
    docs.mkdir()
    monkeypatch.setattr(settings, "DOCS_ROOT", docs)
    monkeypatch.setattr(settings, "CUSTOM_CSS", "custom.css")

    path = get_custom_css_path()
    assert path is None
