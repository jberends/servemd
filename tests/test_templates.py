"""
Unit tests for templates module.
Tests HTML template generation.
"""

import pytest


def test_create_html_template_basic():
    """Test basic template generation"""
    from docs_server.templates import create_html_template

    content = "<h1>Test Content</h1>"
    result = create_html_template(content)

    assert "<!DOCTYPE html>" in result
    assert "<html lang=\"nl\">" in result
    assert "<h1>Test Content</h1>" in result
    assert "Documentation" in result


def test_create_html_template_with_title():
    """Test template with custom title"""
    from docs_server.templates import create_html_template

    content = "<p>Content</p>"
    title = "Custom Page Title"
    result = create_html_template(content, title=title)

    assert f"<title>{title}</title>" in result


def test_create_html_template_with_navigation():
    """Test template with navigation"""
    from docs_server.templates import create_html_template

    content = "<p>Content</p>"
    navigation = [
        {"type": "link", "title": "Home", "link": "index.html"},
        {
            "type": "group_with_children",
            "title": "Guide",
            "link": "guide.html",
            "children": [{"title": "Getting Started", "link": "getting-started.html"}],
        },
    ]

    result = create_html_template(content, navigation=navigation)

    assert "<nav class='sidebar'>" in result
    assert "Home" in result
    assert "Guide" in result
    assert "Getting Started" in result


def test_create_html_template_with_topbar():
    """Test template with topbar sections"""
    from docs_server.templates import create_html_template

    content = "<p>Content</p>"
    topbar_sections = {
        "left": [{"type": "logo_link", "title": "Docs", "link": "index.html"}],
        "middle": [],
        "right": [{"type": "link", "title": "Contact", "link": "contact.html"}],
    }

    result = create_html_template(content, topbar_sections=topbar_sections)

    assert "<div class='topbar'>" in result
    assert "topbar-left" in result
    assert "topbar-right" in result
    assert "Docs" in result
    assert "Contact" in result


def test_create_html_template_with_toc():
    """Test template with table of contents"""
    from docs_server.templates import create_html_template

    content = "<p>Content</p>"
    toc_items = [
        {"id": "section-1", "title": "Section 1", "level": 2},
        {"id": "section-2", "title": "Section 2", "level": 2},
        {"id": "subsection", "title": "Subsection", "level": 3},
    ]

    result = create_html_template(content, toc_items=toc_items)

    assert "<aside class='toc-sidebar'>" in result
    assert "On this page" in result
    assert "Section 1" in result
    assert "Section 2" in result
    assert "Subsection" in result
    assert "#section-1" in result


def test_create_html_template_active_link_highlighting():
    """Test that active links are highlighted"""
    from docs_server.templates import create_html_template

    content = "<p>Content</p>"
    current_path = "guide.html"
    navigation = [
        {"type": "link", "title": "Home", "link": "index.html"},
        {"type": "link", "title": "Guide", "link": "guide.html"},
    ]

    result = create_html_template(content, current_path=current_path, navigation=navigation)

    # Active link should have 'active' class
    assert "nav-standalone-link active" in result


def test_create_html_template_with_group_children_active():
    """Test active highlighting for child items"""
    from docs_server.templates import create_html_template

    content = "<p>Content</p>"
    current_path = "getting-started.html"
    navigation = [
        {
            "type": "group_with_children",
            "title": "Guide",
            "link": "guide.html",
            "children": [
                {"title": "Getting Started", "link": "getting-started.html"},
                {"title": "Advanced", "link": "advanced.html"},
            ],
        }
    ]

    result = create_html_template(content, current_path=current_path, navigation=navigation)

    # Child item should be marked active
    assert "nav-group-item active" in result


def test_create_html_template_css_included():
    """Test that CSS is included in template"""
    from docs_server.templates import create_html_template

    content = "<p>Content</p>"
    result = create_html_template(content)

    # Check for key CSS classes
    assert "--accent-primary: #f26a28" in result
    assert ".sidebar {" in result
    assert ".topbar {" in result
    assert ".content {" in result
    assert ".toc-sidebar {" in result


def test_create_html_template_responsive_design():
    """Test that responsive CSS is included"""
    from docs_server.templates import create_html_template

    content = "<p>Content</p>"
    result = create_html_template(content)

    # Check for media queries
    assert "@media (max-width: 1200px)" in result
    assert "@media (max-width: 768px)" in result


def test_create_html_template_empty_navigation():
    """Test template with empty navigation"""
    from docs_server.templates import create_html_template

    content = "<p>Content</p>"
    result = create_html_template(content, navigation=[])

    # Sidebar should not be rendered when empty
    assert "<nav class='sidebar'>" not in result


def test_create_html_template_empty_topbar():
    """Test template with empty topbar"""
    from docs_server.templates import create_html_template

    content = "<p>Content</p>"
    topbar_sections = {"left": [], "middle": [], "right": []}
    result = create_html_template(content, topbar_sections=topbar_sections)

    # Topbar should not be rendered when all sections empty
    assert "<div class='topbar'>" not in result


def test_create_html_template_external_links():
    """Test that external links have proper attributes"""
    from docs_server.templates import create_html_template

    content = "<p>Content</p>"
    topbar_sections = {"left": [{"type": "link", "title": "GitHub", "link": "https://github.com"}], "middle": [], "right": []}

    result = create_html_template(content, topbar_sections=topbar_sections)

    # External links should have target="_blank" and rel attributes
    assert 'target="_blank"' in result
    assert 'rel="noopener noreferrer"' in result
