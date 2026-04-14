"""Tests for search term highlighting on destination pages."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client_with_docs(tmp_path, monkeypatch):
    """TestClient with a temporary docs root containing a test markdown page."""
    import docs_server.config as cfg

    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    (docs_root / "sidebar.md").write_text("# Nav\n", encoding="utf-8")
    (docs_root / "topbar.md").write_text("# Top\n", encoding="utf-8")
    monkeypatch.setattr(cfg.settings, "DOCS_ROOT", docs_root)
    monkeypatch.setattr(cfg.settings, "MCP_ENABLED", False)

    content = """# Test Page

This page contains the word authentication multiple times.
Authentication is important for security. We do authentication here.
"""
    (docs_root / "test.md").write_text(content, encoding="utf-8")

    from docs_server.main import app

    return TestClient(app, raise_server_exceptions=True)


def test_page_without_highlight_has_no_highlight_script(client_with_docs):
    """Normal page load (no highlight param) has no highlight script."""
    response = client_with_docs.get("/test.html")
    assert response.status_code == 200
    # Should not inject highlight JS when no parameter
    assert "highlightSearchTerms" not in response.text


def test_page_with_highlight_param_injects_script(client_with_docs):
    """Requesting a page with ?highlight=foo injects client-side highlight JS."""
    response = client_with_docs.get("/test.html?highlight=authentication")
    assert response.status_code == 200
    assert "highlightSearchTerms" in response.text
    assert "authentication" in response.text


def test_highlight_script_contains_escaped_term(client_with_docs):
    """The injected script safely embeds the search term (HTML-escaped)."""
    response = client_with_docs.get('/test.html?highlight=auth"<script>')
    assert response.status_code == 200
    # The raw injection string should NOT appear unescaped
    assert "<script>" not in response.text.split("highlightSearchTerms")[1][:200]


def test_search_page_script_has_add_highlight_to_links(client_with_docs):
    """The search page HTML includes the client-side addHighlightToLinks helper."""
    response = client_with_docs.get("/search?q=authentication")
    assert response.status_code == 200
    assert "addHighlightToLinks" in response.text


def test_search_result_url_uses_clean_url(tmp_path, monkeypatch):
    """format_search_results_human uses the result URL as-is (no server-side ?highlight=).
    The ?highlight= param is added client-side by the search page JS."""
    from docs_server.helpers import format_search_results_human
    from docs_server.mcp.search import SearchResult

    results = [
        SearchResult(
            path="use_cases.md",
            title="Use Cases",
            snippet="Test snippet",
            score=1.0,
            category="",
            anchor="",
            url="/use_cases.html",
        )
    ]

    html = format_search_results_human(results, query="authentication")
    assert "href='/use_cases.html'" in html
    assert "?highlight=" not in html


def test_search_result_url_with_anchor_preserved_clean(tmp_path, monkeypatch):
    """When result has an anchor, the clean URL (path#anchor) is used without ?highlight=."""
    from docs_server.helpers import format_search_results_human
    from docs_server.mcp.search import SearchResult

    results = [
        SearchResult(
            path="use_cases.md",
            title="Use Cases",
            snippet="Test snippet",
            score=1.0,
            category="",
            anchor="uc-2-002-manage-template-versions",
            url="/use_cases.html#uc-2-002-manage-template-versions",
        )
    ]

    html = format_search_results_human(results, query="UC-2-002")
    assert "href='/use_cases.html#uc-2-002-manage-template-versions'" in html
    assert "?highlight=" not in html
