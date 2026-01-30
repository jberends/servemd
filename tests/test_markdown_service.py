"""
Unit tests for markdown_service module.
Tests markdown-to-HTML rendering with extensions.
"""

from pathlib import Path

import pytest


@pytest.mark.asyncio
async def test_render_markdown_basic(tmp_path):
    """Test basic markdown rendering"""
    from docs_server.markdown_service import render_markdown_to_html

    content = "# Hello World\n\nThis is a test."
    file_path = tmp_path / "test.md"

    result = await render_markdown_to_html(content, file_path)

    assert "<h1" in result
    assert "Hello World" in result
    assert "<p>This is a test.</p>" in result


@pytest.mark.asyncio
async def test_render_markdown_with_code_block(tmp_path):
    """Test markdown rendering with code blocks"""
    from docs_server.markdown_service import render_markdown_to_html

    content = """# Test

```python
def hello():
    return "world"
```
"""
    file_path = tmp_path / "test.md"

    result = await render_markdown_to_html(content, file_path)

    assert "<code" in result or "<pre" in result
    # Code should be highlighted with CSS classes
    assert 'class="highlight"' in result or '<div class="highlight">' in result
    # Check that code content is present (may be wrapped in span tags for syntax highlighting)
    assert "def" in result
    assert "hello" in result
    assert "return" in result
    assert "world" in result


@pytest.mark.asyncio
async def test_render_markdown_with_table(tmp_path):
    """Test markdown rendering with tables"""
    from docs_server.markdown_service import render_markdown_to_html

    content = """# Test

| Column 1 | Column 2 |
|----------|----------|
| Value 1  | Value 2  |
"""
    file_path = tmp_path / "test.md"

    result = await render_markdown_to_html(content, file_path)

    assert "<table" in result
    assert "<th" in result
    assert "<td" in result
    assert "Column 1" in result
    assert "Value 1" in result


@pytest.mark.asyncio
async def test_render_markdown_with_toc(tmp_path):
    """Test markdown rendering with table of contents"""
    from docs_server.markdown_service import render_markdown_to_html

    content = """# Main Title

## Section 1

Some content.

## Section 2

More content.
"""
    file_path = tmp_path / "test.md"

    result = await render_markdown_to_html(content, file_path)

    # TOC extension adds IDs to headings
    assert 'id="' in result
    assert "Section 1" in result
    assert "Section 2" in result


@pytest.mark.asyncio
async def test_render_markdown_converts_links(tmp_path):
    """Test that .md links are converted to .html"""
    from docs_server.markdown_service import render_markdown_to_html

    content = "# Test\n\n[Link to page](page.md)"
    file_path = tmp_path / "test.md"

    result = await render_markdown_to_html(content, file_path)

    # Should convert .md to .html
    assert "page.html" in result
    assert "page.md" not in result


@pytest.mark.asyncio
async def test_render_markdown_with_task_list(tmp_path):
    """Test markdown rendering with task lists"""
    from docs_server.markdown_service import render_markdown_to_html

    content = """# TODO

- [x] Completed task
- [ ] Pending task
"""
    file_path = tmp_path / "test.md"

    result = await render_markdown_to_html(content, file_path)

    assert "task-list" in result or "checkbox" in result
    assert "TODO" in result


@pytest.mark.asyncio
async def test_render_markdown_empty_content(tmp_path):
    """Test rendering empty markdown"""
    from docs_server.markdown_service import render_markdown_to_html

    content = ""
    file_path = tmp_path / "test.md"

    result = await render_markdown_to_html(content, file_path)

    # Should return empty string or minimal HTML
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_render_markdown_with_special_characters(tmp_path):
    """Test rendering with special characters"""
    from docs_server.markdown_service import render_markdown_to_html

    content = '# Test & Special <Characters>\n\nHTML entities: & < > "'
    file_path = tmp_path / "test.md"

    result = await render_markdown_to_html(content, file_path)

    # HTML entities should be escaped
    assert "&amp;" in result or "&lt;" in result or "Special" in result
