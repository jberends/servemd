"""Tests for search result anchor link generation."""

import asyncio

import pytest


@pytest.fixture
def tmp_docs_root(tmp_path, monkeypatch):
    """Temporary docs root with anchor test content."""
    import docs_server.config as cfg
    import docs_server.mcp.indexer as idx_module

    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    monkeypatch.setattr(cfg.settings, "DOCS_ROOT", docs_root)
    monkeypatch.setattr(cfg.settings, "CACHE_ROOT", tmp_path / "cache")
    # Reset global index manager so each test gets a fresh one
    idx_module.reset_index_manager()
    yield docs_root
    idx_module.reset_index_manager()


def test_generate_anchor_id_basic():
    """generate_anchor_id converts heading text to anchor-safe string."""
    from docs_server.mcp.indexer import generate_anchor_id

    assert generate_anchor_id("UC-2-002 Manage Template Versions") == "uc-2-002-manage-template-versions"
    assert generate_anchor_id("Hello World") == "hello-world"
    assert generate_anchor_id("AUTH_01 Login") == "auth01-login"


def test_extract_identifier_to_anchor_map():
    """extract_identifier_to_anchor_map returns identifier -> anchor mapping."""
    from docs_server.mcp.indexer import extract_identifier_to_anchor_map

    content = """# Use Cases

## UC-2-001 First Use Case

Details.

### UC-2-002 Manage Template Versions

More details.
"""
    mapping = extract_identifier_to_anchor_map(content)
    assert "uc-2-001" in mapping
    assert mapping["uc-2-001"] == "uc-2-001-first-use-case"
    assert "uc-2-002" in mapping
    assert mapping["uc-2-002"] == "uc-2-002-manage-template-versions"


def test_search_result_has_anchor_for_identifier_match(tmp_docs_root):
    """Searching for an identifier returns a result with an anchor link."""
    from docs_server.mcp.indexer import get_index_manager
    from docs_server.mcp.search import search_docs

    content = """# Use Cases

## UC-2-002 Manage Template Versions

This use case describes how to manage template versions.
"""
    (tmp_docs_root / "use_cases.md").write_text(content, encoding="utf-8")

    manager = get_index_manager()
    asyncio.run(manager.initialize(force_rebuild=True))

    results = search_docs("UC-2-002")

    assert len(results) > 0
    result = results[0]
    assert result.anchor == "uc-2-002-manage-template-versions"
    assert result.url.endswith("#uc-2-002-manage-template-versions")


def test_search_result_url_without_anchor_for_no_identifier(tmp_docs_root):
    """Content matches without identifier do not get an anchor."""
    from docs_server.mcp.indexer import get_index_manager
    from docs_server.mcp.search import search_docs

    content = """# Documentation

This page discusses authentication concepts.
"""
    (tmp_docs_root / "auth.md").write_text(content, encoding="utf-8")

    manager = get_index_manager()
    asyncio.run(manager.initialize(force_rebuild=True))

    results = search_docs("authentication")

    assert len(results) > 0
    result = results[0]
    assert result.anchor == ""
    assert result.url == "/auth.html"
