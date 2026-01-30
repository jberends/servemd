"""
Unit tests for caching module.
Tests cache read/write operations for HTML and llms.txt files.
"""

from pathlib import Path

import pytest


@pytest.mark.asyncio
async def test_save_and_get_cached_html(tmp_path, monkeypatch):
    """Test saving and retrieving HTML cache"""
    from docs_server import config
    from docs_server.caching import get_cached_html, save_cached_html

    # Setup paths
    docs_root = tmp_path / "docs"
    cache_root = tmp_path / "cache"
    docs_root.mkdir()
    cache_root.mkdir()

    monkeypatch.setattr(config.settings, "DOCS_ROOT", docs_root)
    monkeypatch.setattr(config.settings, "CACHE_ROOT", cache_root)

    # Create test file
    test_file = docs_root / "test.md"
    test_file.write_text("# Test")

    # Save HTML to cache
    html_content = "<h1>Test</h1>"
    await save_cached_html(test_file, html_content)

    # Retrieve from cache
    cached = await get_cached_html(test_file)
    assert cached == html_content


@pytest.mark.asyncio
async def test_get_cached_html_miss(tmp_path, monkeypatch):
    """Test cache miss returns None"""
    from docs_server import config
    from docs_server.caching import get_cached_html

    docs_root = tmp_path / "docs"
    cache_root = tmp_path / "cache"
    docs_root.mkdir()
    cache_root.mkdir()

    monkeypatch.setattr(config.settings, "DOCS_ROOT", docs_root)
    monkeypatch.setattr(config.settings, "CACHE_ROOT", cache_root)

    test_file = docs_root / "test.md"
    test_file.write_text("# Test")

    cached = await get_cached_html(test_file)
    assert cached is None


@pytest.mark.asyncio
async def test_save_cached_html_creates_subdirectories(tmp_path, monkeypatch):
    """Test that save_cached_html creates necessary subdirectories"""
    from docs_server import config
    from docs_server.caching import save_cached_html

    docs_root = tmp_path / "docs"
    cache_root = tmp_path / "cache"
    docs_root.mkdir()
    cache_root.mkdir()

    monkeypatch.setattr(config.settings, "DOCS_ROOT", docs_root)
    monkeypatch.setattr(config.settings, "CACHE_ROOT", cache_root)

    # Create nested file
    subdir = docs_root / "guides"
    subdir.mkdir()
    test_file = subdir / "test.md"
    test_file.write_text("# Test")

    # Save HTML to cache
    html_content = "<h1>Test</h1>"
    await save_cached_html(test_file, html_content)

    # Check that subdirectory was created in cache
    expected_cache = cache_root / "guides" / "test.html"
    assert expected_cache.exists()
    assert expected_cache.read_text() == html_content


@pytest.mark.asyncio
async def test_save_and_get_cached_llms(tmp_path, monkeypatch):
    """Test saving and retrieving llms.txt cache"""
    from docs_server import config
    from docs_server.caching import get_cached_llms, save_cached_llms

    cache_root = tmp_path / "cache"
    cache_root.mkdir()

    monkeypatch.setattr(config.settings, "CACHE_ROOT", cache_root)

    # Save llms content to cache
    llms_content = "# LLMs.txt\n\n[Page](page.md)"
    await save_cached_llms("llms.txt", llms_content)

    # Retrieve from cache
    cached = await get_cached_llms("llms.txt")
    assert cached == llms_content


@pytest.mark.asyncio
async def test_get_cached_llms_miss(tmp_path, monkeypatch):
    """Test llms cache miss returns None"""
    from docs_server import config
    from docs_server.caching import get_cached_llms

    cache_root = tmp_path / "cache"
    cache_root.mkdir()

    monkeypatch.setattr(config.settings, "CACHE_ROOT", cache_root)

    cached = await get_cached_llms("nonexistent.txt")
    assert cached is None


@pytest.mark.asyncio
async def test_save_cached_llms_creates_cache_dir(tmp_path, monkeypatch):
    """Test that save_cached_llms creates cache directory if needed"""
    from docs_server import config
    from docs_server.caching import save_cached_llms

    cache_root = tmp_path / "cache"
    # Don't create cache_root yet

    monkeypatch.setattr(config.settings, "CACHE_ROOT", cache_root)

    # Save should create directory
    await save_cached_llms("test.txt", "content")

    assert cache_root.exists()
    assert (cache_root / "test.txt").exists()


@pytest.mark.asyncio
async def test_cache_handles_unicode(tmp_path, monkeypatch):
    """Test caching with unicode content"""
    from docs_server import config
    from docs_server.caching import get_cached_llms, save_cached_llms

    cache_root = tmp_path / "cache"
    cache_root.mkdir()

    monkeypatch.setattr(config.settings, "CACHE_ROOT", cache_root)

    # Unicode content
    unicode_content = "# Test\n\nUnicode: émojis 🎉 日本語 العربية"
    await save_cached_llms("unicode.txt", unicode_content)

    cached = await get_cached_llms("unicode.txt")
    assert cached == unicode_content


@pytest.mark.asyncio
async def test_cache_handles_large_content(tmp_path, monkeypatch):
    """Test caching with large content"""
    from docs_server import config
    from docs_server.caching import get_cached_llms, save_cached_llms

    cache_root = tmp_path / "cache"
    cache_root.mkdir()

    monkeypatch.setattr(config.settings, "CACHE_ROOT", cache_root)

    # Generate large content
    large_content = "# Test\n\n" + ("Lorem ipsum dolor sit amet.\n" * 10000)
    await save_cached_llms("large.txt", large_content)

    cached = await get_cached_llms("large.txt")
    assert cached == large_content
    assert len(cached) > 100000
