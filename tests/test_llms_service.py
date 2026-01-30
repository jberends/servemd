"""
Unit tests for llms_service module.
Tests llms.txt generation and URL transformation.
"""

from pathlib import Path

import pytest


def test_transform_relative_to_absolute_simple():
    """Test simple relative link transformation"""
    from docs_server.llms_service import transform_relative_to_absolute

    content = "[Home](index.md)"
    base_url = "https://docs.example.com"

    result = transform_relative_to_absolute(content, base_url)
    assert result == "[Home](https://docs.example.com/index.md)"


def test_transform_relative_to_absolute_with_anchor():
    """Test link transformation with anchor"""
    from docs_server.llms_service import transform_relative_to_absolute

    content = "[Section](page.md#section)"
    base_url = "https://docs.example.com"

    result = transform_relative_to_absolute(content, base_url)
    assert result == "[Section](https://docs.example.com/page.md#section)"


def test_transform_relative_to_absolute_already_absolute():
    """Test that absolute URLs are not modified"""
    from docs_server.llms_service import transform_relative_to_absolute

    content = "[External](https://example.com/file.md)"
    base_url = "https://docs.example.com"

    result = transform_relative_to_absolute(content, base_url)
    assert result == "[External](https://example.com/file.md)"


def test_transform_relative_to_absolute_multiple_links():
    """Test multiple link transformations"""
    from docs_server.llms_service import transform_relative_to_absolute

    content = "[Page 1](page1.md) and [Page 2](page2.md)"
    base_url = "https://docs.example.com"

    result = transform_relative_to_absolute(content, base_url)
    assert result == "[Page 1](https://docs.example.com/page1.md) and [Page 2](https://docs.example.com/page2.md)"


def test_transform_relative_to_absolute_trailing_slash():
    """Test base URL with trailing slash"""
    from docs_server.llms_service import transform_relative_to_absolute

    content = "[Home](index.md)"
    base_url = "https://docs.example.com/"

    result = transform_relative_to_absolute(content, base_url)
    # Should not create double slashes
    assert result == "[Home](https://docs.example.com/index.md)"
    assert "//index" not in result


def test_transform_relative_to_absolute_leading_slash():
    """Test path with leading slash"""
    from docs_server.llms_service import transform_relative_to_absolute

    content = "[Home](/index.md)"
    base_url = "https://docs.example.com"

    result = transform_relative_to_absolute(content, base_url)
    assert result == "[Home](https://docs.example.com/index.md)"


@pytest.mark.asyncio
async def test_generate_llms_txt_content_curated(tmp_path, monkeypatch):
    """Test PRIMARY strategy: serve curated llms.txt"""
    from docs_server import config
    from docs_server.llms_service import generate_llms_txt_content

    # Create curated llms.txt
    llms_txt = tmp_path / "llms.txt"
    curated_content = "# Documentation\n\n[Page](page.md)"
    llms_txt.write_text(curated_content)

    monkeypatch.setattr(config.settings, "DOCS_ROOT", tmp_path)

    result = await generate_llms_txt_content("https://test.com")

    # Should use curated content and transform links
    assert "# Documentation" in result
    assert "https://test.com/page.md" in result
    assert "[Page](page.md)" not in result  # Relative link should be transformed to absolute


@pytest.mark.asyncio
async def test_generate_llms_txt_content_fallback(tmp_path, monkeypatch):
    """Test FALLBACK strategy: generate from sidebar + index"""
    from docs_server import config
    from docs_server.llms_service import generate_llms_txt_content

    # Create sidebar.md and index.md (no llms.txt)
    sidebar = tmp_path / "sidebar.md"
    sidebar.write_text("# Sidebar\n\n* [Link1](link1.md)")

    index = tmp_path / "index.md"
    index.write_text("# Index\n\nWelcome!")

    monkeypatch.setattr(config.settings, "DOCS_ROOT", tmp_path)

    result = await generate_llms_txt_content("https://test.com")

    # Should concatenate sidebar and index with separator
    assert "# Sidebar" in result
    assert "# Index" in result
    assert "---" in result
    assert "https://test.com/link1.md" in result


@pytest.mark.asyncio
async def test_generate_llms_txt_content_fallback_only_index(tmp_path, monkeypatch):
    """Test FALLBACK with only index.md (no sidebar)"""
    from docs_server import config
    from docs_server.llms_service import generate_llms_txt_content

    # Create only index.md
    index = tmp_path / "index.md"
    index.write_text("# Index Only\n\n[Page](page.md)")

    monkeypatch.setattr(config.settings, "DOCS_ROOT", tmp_path)

    result = await generate_llms_txt_content("https://test.com")

    # Should use only index content (no separator)
    assert "# Index Only" in result
    assert "---" not in result
    assert "https://test.com/page.md" in result


@pytest.mark.asyncio
async def test_generate_llms_txt_content_empty(tmp_path, monkeypatch):
    """Test generation with no files"""
    from docs_server import config
    from docs_server.llms_service import generate_llms_txt_content

    monkeypatch.setattr(config.settings, "DOCS_ROOT", tmp_path)

    result = await generate_llms_txt_content("https://test.com")

    # Should return empty string
    assert result == ""


@pytest.mark.asyncio
async def test_generate_llms_txt_content_preserves_non_md_links(tmp_path, monkeypatch):
    """Test that non-.md links are not transformed"""
    from docs_server import config
    from docs_server.llms_service import generate_llms_txt_content

    # Create llms.txt with various link types
    llms_txt = tmp_path / "llms.txt"
    content = """# Test

[MD Link](page.md)
[External](https://example.com/page)
[Anchor](#section)
[Image](image.png)
"""
    llms_txt.write_text(content)

    monkeypatch.setattr(config.settings, "DOCS_ROOT", tmp_path)

    result = await generate_llms_txt_content("https://test.com")

    # Only .md links should be transformed
    assert "https://test.com/page.md" in result
    assert "https://example.com/page" in result  # External unchanged
    assert "[Anchor](#section)" in result  # Anchor unchanged
    assert "[Image](image.png)" in result  # Image unchanged
