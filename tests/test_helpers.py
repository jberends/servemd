"""
Unit tests for helpers module.
Tests utility functions and navigation parsing.
"""

from pathlib import Path


def test_format_search_results_human_empty_no_query():
    """format_search_results_human with empty results and no query returns 'Enter a search term'."""
    from docs_server.helpers import format_search_results_human

    result = format_search_results_human([], "")
    assert "Enter a search term to find documentation" in result
    assert "search-no-results" in result


def test_highlight_search_terms():
    """Test search term highlighting wraps matches in mark tags case-insensitively."""
    from docs_server.helpers import highlight_search_terms

    html = "<p>MCP enables LLM integration. Use mcp for search.</p>"
    result = highlight_search_terms(html, "mcp")
    assert '<mark class="search-highlight">MCP</mark>' in result
    assert '<mark class="search-highlight">mcp</mark>' in result
    assert "MCP enables" not in result  # Original text replaced
    result_empty = highlight_search_terms(html, "")
    assert result_empty == html
    result_ws = highlight_search_terms(html, "   ")
    assert result_ws == html


def test_highlight_search_terms_does_not_modify_html_tags():
    """Search terms matching tag names (div, span) must not break HTML structure."""
    from docs_server.helpers import highlight_search_terms

    html = '<div class="search-result-card"><span>div and span are HTML elements</span></div>'
    result = highlight_search_terms(html, "div")
    # Tag names must remain intact
    assert "<div" in result
    assert "</div>" in result
    # Text content "div" should be highlighted
    assert '<mark class="search-highlight">div</mark>' in result


def test_build_chatgpt_url():
    """Test build_chatgpt_url produces correct prompt format."""
    from docs_server.helpers import build_chatgpt_url

    raw_url = "https://docs.example.com/features/mcp.md"
    result = build_chatgpt_url(raw_url)
    assert result.startswith("https://chatgpt.com/?prompt=")
    assert "Read+" in result
    assert "so+I+can+ask+questions+about+it." in result
    assert "https%3A%2F%2Fdocs.example.com%2Ffeatures%2Fmcp.md" in result


def test_build_claude_url():
    """Test build_claude_url produces correct query format."""
    from docs_server.helpers import build_claude_url

    raw_url = "https://docs.example.com/features/mcp.md"
    result = build_claude_url(raw_url)
    assert result.startswith("https://claude.ai/new?q=")
    assert "Read%20" in result
    assert "so%20I%20can%20ask%20questions%20about%20it." in result
    assert "https%3A%2F%2Fdocs.example.com%2Ffeatures%2Fmcp.md" in result


def test_build_mistral_url():
    """Test build_mistral_url produces correct query format."""
    from docs_server.helpers import build_mistral_url

    raw_url = "https://docs.example.com/features/mcp.md"
    result = build_mistral_url(raw_url)
    assert result.startswith("https://chat.mistral.ai/chat?q=")
    assert "Read+" in result
    assert "so+I+can+ask+questions+about+it." in result
    assert "https%3A%2F%2Fdocs.example.com%2Ffeatures%2Fmcp.md" in result


def test_path_to_doc_url():
    """Test path_to_doc_url converts SearchResult.path to doc URL."""
    from docs_server.helpers import path_to_doc_url

    assert path_to_doc_url("features/mcp.md") == "/features/mcp.html"
    assert path_to_doc_url("index.md") == "/index.html"
    assert path_to_doc_url("api/endpoints.md") == "/api/endpoints.html"
    assert path_to_doc_url("/features/mcp.md") == "/features/mcp.html"


def test_is_safe_path():
    """Test path traversal security validation"""
    from docs_server.helpers import is_safe_path

    base_path = Path("/app/docs")

    # Safe paths
    assert is_safe_path("index.md", base_path) is True
    assert is_safe_path("folder/file.md", base_path) is True
    assert is_safe_path("./file.md", base_path) is True

    # Unsafe paths (directory traversal attempts)
    assert is_safe_path("../../../etc/passwd", base_path) is False
    assert is_safe_path("/etc/passwd", base_path) is False
    # Note: Windows backslashes are treated as literal characters on Unix, so we don't test them


def test_get_file_path_success(tmp_path, monkeypatch):
    """Test get_file_path returns correct path for existing files"""
    from docs_server import config
    from docs_server.helpers import get_file_path

    # Create test file
    test_file = tmp_path / "test.md"
    test_file.write_text("# Test")

    # Mock DOCS_ROOT
    monkeypatch.setattr(config.settings, "DOCS_ROOT", tmp_path)

    result = get_file_path("test.md")
    assert result == test_file
    assert result.exists()


def test_get_file_path_not_found(tmp_path, monkeypatch):
    """Test get_file_path returns None for non-existent files"""
    from docs_server import config
    from docs_server.helpers import get_file_path

    monkeypatch.setattr(config.settings, "DOCS_ROOT", tmp_path)

    result = get_file_path("nonexistent.md")
    assert result is None


def test_get_file_path_unsafe(tmp_path, monkeypatch):
    """Test get_file_path returns None for unsafe paths"""
    from docs_server import config
    from docs_server.helpers import get_file_path

    monkeypatch.setattr(config.settings, "DOCS_ROOT", tmp_path)

    result = get_file_path("../../../etc/passwd")
    assert result is None


def test_extract_table_of_contents():
    """Test TOC extraction from HTML"""
    from docs_server.helpers import extract_table_of_contents

    html_content = """
    <h1 id="main-title">Main Title</h1>
    <p>Some content</p>
    <h2 id="section-1">Section 1</h2>
    <p>More content</p>
    <h3 id="subsection">Subsection</h3>
    <h2 id="section-2">Section 2 <a class="headerlink" href="#section-2">¶</a></h2>
    """

    toc_items = extract_table_of_contents(html_content)

    assert len(toc_items) == 4
    assert toc_items[0]["id"] == "main-title"
    assert toc_items[0]["title"] == "Main Title"
    assert toc_items[0]["level"] == 1

    assert toc_items[1]["id"] == "section-1"
    assert toc_items[1]["level"] == 2

    assert toc_items[2]["id"] == "subsection"
    assert toc_items[2]["level"] == 3

    # Check that paragraph marks are removed
    assert toc_items[3]["title"] == "Section 2"
    assert "¶" not in toc_items[3]["title"]


def test_extract_table_of_contents_empty():
    """Test TOC extraction with no headings"""
    from docs_server.helpers import extract_table_of_contents

    html_content = "<p>Just a paragraph</p>"
    toc_items = extract_table_of_contents(html_content)

    assert toc_items == []


def test_convert_md_links_to_html():
    """Test markdown link conversion to HTML"""
    from docs_server.helpers import convert_md_links_to_html

    # Single link
    content = "[Home](index.md)"
    result = convert_md_links_to_html(content)
    assert result == "[Home](index.html)"

    # Multiple links
    content = "[Page 1](page1.md) and [Page 2](page2.md)"
    result = convert_md_links_to_html(content)
    assert result == "[Page 1](page1.html) and [Page 2](page2.html)"

    # Link with path
    content = "[Guide](guides/getting-started.md)"
    result = convert_md_links_to_html(content)
    assert result == "[Guide](guides/getting-started.html)"

    # Non-.md links should not be changed
    content = "[External](https://example.com)"
    result = convert_md_links_to_html(content)
    assert result == "[External](https://example.com)"


def test_parse_topbar_links_no_file(tmp_path, monkeypatch):
    """Test topbar parsing when file doesn't exist"""
    from docs_server import config
    from docs_server.helpers import parse_topbar_links

    monkeypatch.setattr(config.settings, "DOCS_ROOT", tmp_path)

    result = parse_topbar_links()
    assert result == {"left": [], "middle": [], "right": []}


def test_parse_topbar_links_with_content(tmp_path, monkeypatch):
    """Test topbar parsing with actual content"""
    from docs_server import config
    from docs_server.helpers import parse_topbar_links

    # Create test topbar.md
    topbar_content = """# Topbar Navigation

## left
* {{logo}} | [Home](index.md)
* [Docs](docs.md)

## right
* [Contact](contact.md)
* Plain text item
"""
    topbar_file = tmp_path / "topbar.md"
    topbar_file.write_text(topbar_content)

    monkeypatch.setattr(config.settings, "DOCS_ROOT", tmp_path)

    result = parse_topbar_links()

    # Check structure
    assert "left" in result
    assert "middle" in result
    assert "right" in result

    # Check left section - links are root-relative for correct resolution from any page
    assert len(result["left"]) == 2
    assert result["left"][0]["type"] == "logo_link"
    assert result["left"][0]["title"] == "Home"
    assert result["left"][0]["link"] == "/index.html"

    assert result["left"][1]["type"] == "link"
    assert result["left"][1]["title"] == "Docs"
    assert result["left"][1]["link"] == "/docs.html"

    # Check right section
    assert len(result["right"]) == 2
    assert result["right"][0]["type"] == "link"
    assert result["right"][1]["type"] == "text"


def test_parse_topbar_links_with_search_placeholder(tmp_path, monkeypatch):
    """Test topbar parsing with {search} placeholder and params."""
    from docs_server import config
    from docs_server.helpers import parse_topbar_links

    topbar_content = """# Top Bar

## right
* [GitHub](https://github.com/project)
* {{search}}
* [Docker](https://hub.docker.com)
"""
    topbar_file = tmp_path / "topbar.md"
    topbar_file.write_text(topbar_content)

    monkeypatch.setattr(config.settings, "DOCS_ROOT", tmp_path)

    result = parse_topbar_links()

    assert len(result["right"]) == 3
    assert result["right"][0]["type"] == "link"
    assert result["right"][1]["type"] == "search"
    assert result["right"][1]["params"] == {}
    assert result["right"][2]["type"] == "link"


def test_parse_topbar_links_search_with_params(tmp_path, monkeypatch):
    """Test topbar parsing with {search:params} placeholder."""
    from docs_server import config
    from docs_server.helpers import parse_topbar_links

    topbar_content = """# Top Bar

## right
* {{search:icon=lucide-search,mode=button,placeholder=Zoeken...}}
"""
    topbar_file = tmp_path / "topbar.md"
    topbar_file.write_text(topbar_content)

    monkeypatch.setattr(config.settings, "DOCS_ROOT", tmp_path)

    result = parse_topbar_links()

    assert len(result["right"]) == 1
    assert result["right"][0]["type"] == "search"
    assert result["right"][0]["params"]["icon"] == "lucide-search"
    assert result["right"][0]["params"]["mode"] == "button"
    assert result["right"][0]["params"]["placeholder"] == "Zoeken..."


def test_parse_sidebar_navigation_no_file(tmp_path, monkeypatch):
    """Test sidebar parsing when file doesn't exist"""
    from docs_server import config
    from docs_server.helpers import parse_sidebar_navigation

    monkeypatch.setattr(config.settings, "DOCS_ROOT", tmp_path)

    result = parse_sidebar_navigation()
    assert result == []


def test_parse_sidebar_navigation_with_content(tmp_path, monkeypatch):
    """Test sidebar parsing with actual content"""
    from docs_server import config
    from docs_server.helpers import parse_sidebar_navigation

    # Create test sidebar.md
    sidebar_content = """# Navigation

* [Overview](overview.md)
* [Getting Started](getting-started.md)
  * [Installation](installation.md)
  * [Configuration](configuration.md)
* [API Reference](api.md)
"""
    sidebar_file = tmp_path / "sidebar.md"
    sidebar_file.write_text(sidebar_content)

    monkeypatch.setattr(config.settings, "DOCS_ROOT", tmp_path)

    result = parse_sidebar_navigation()

    # Check structure
    assert len(result) == 3

    # First item - standalone link - links are root-relative for correct resolution from any page
    assert result[0]["type"] == "link"
    assert result[0]["title"] == "Overview"
    assert result[0]["link"] == "/overview.html"
    assert len(result[0]["children"]) == 0

    # Second item - group with children
    assert result[1]["type"] == "group_with_children"
    assert result[1]["title"] == "Getting Started"
    assert result[1]["link"] == "/getting-started.html"
    assert len(result[1]["children"]) == 2
    assert result[1]["children"][0]["title"] == "Installation"
    assert result[1]["children"][0]["link"] == "/installation.html"

    # Third item - standalone link
    assert result[2]["type"] == "link"
    assert result[2]["title"] == "API Reference"


def test_parse_sidebar_navigation_root_relative_links(tmp_path, monkeypatch):
    """Test that sidebar links in subdirs and external URLs are handled correctly"""
    from docs_server import config
    from docs_server.helpers import parse_sidebar_navigation

    sidebar_content = """# Navigation

* [Home](index.html)
* [Subdir Page](deployment/docker.html)
* [External](https://example.com)
"""
    sidebar_file = tmp_path / "sidebar.md"
    sidebar_file.write_text(sidebar_content)

    monkeypatch.setattr(config.settings, "DOCS_ROOT", tmp_path)

    result = parse_sidebar_navigation()

    # Root-level link gets leading slash
    assert result[0]["link"] == "/index.html"
    # Subdir link gets leading slash (fixes /dir/dir/page.html bug when viewing from subdir)
    assert result[1]["link"] == "/deployment/docker.html"
    # External URLs are left unchanged
    assert result[2]["link"] == "https://example.com"


def test_parse_sidebar_navigation_only_main_title(tmp_path, monkeypatch):
    """Test sidebar parsing with only main title"""
    from docs_server import config
    from docs_server.helpers import parse_sidebar_navigation

    sidebar_content = "# Navigation\n\n"
    sidebar_file = tmp_path / "sidebar.md"
    sidebar_file.write_text(sidebar_content)

    monkeypatch.setattr(config.settings, "DOCS_ROOT", tmp_path)

    result = parse_sidebar_navigation()
    assert result == []
