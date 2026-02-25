"""
Unit tests for templates module.
Tests HTML template generation.
"""


def test_create_html_template_basic():
    """Test basic template generation"""
    from docs_server.templates import create_html_template

    content = "<h1>Test Content</h1>"
    result = create_html_template(content)

    assert "<!DOCTYPE html>" in result
    assert '<html lang="nl">' in result
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
    assert "@media (max-width: 1024px)" in result


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
    topbar_sections = {
        "left": [{"type": "link", "title": "GitHub", "link": "https://github.com"}],
        "middle": [],
        "right": [],
    }

    result = create_html_template(content, topbar_sections=topbar_sections)

    # External links should have target="_blank" and rel attributes
    assert 'target="_blank"' in result
    assert 'rel="noopener noreferrer"' in result


def test_create_html_template_with_search_bar():
    """Test that search bar is rendered when show_search is True"""
    from docs_server.templates import create_html_template

    content = "<p>Content</p>"
    result = create_html_template(content, show_search=True)

    assert "/search" in result and "action=" in result
    assert 'name="q"' in result
    assert "Search..." in result
    assert "topbar-search-form" in result
    assert "topbar-search-input" in result
    assert "search-bar-wrapper" in result


def test_create_html_template_search_bar_prefill():
    """Test that search query is pre-filled when provided"""
    from docs_server.templates import create_html_template

    content = "<p>Content</p>"
    result = create_html_template(content, show_search=True, search_query="mcp")

    assert 'value="mcp"' in result


def test_create_html_template_search_bar_with_topbar():
    """Test that search bar appears in topbar right with other items"""
    from docs_server.templates import create_html_template

    content = "<p>Content</p>"
    topbar_sections = {
        "left": [{"type": "logo_link", "title": "Docs", "link": "index.html"}],
        "middle": [],
        "right": [{"type": "link", "title": "GitHub", "link": "https://github.com"}],
    }
    result = create_html_template(content, topbar_sections=topbar_sections, show_search=True)

    assert "/search" in result and "action=" in result
    assert "GitHub" in result


def test_create_html_template_i_lucide_icon():
    """Test that i-lucide-star uses Iconify CDN (Nuxt UI compatible)"""
    from docs_server.templates import create_html_template

    content = "<p>Content</p>"
    topbar_sections = {
        "left": [],
        "middle": [],
        "right": [{"type": "search", "params": {"icon": "i-lucide-star"}}],
    }
    result = create_html_template(content, topbar_sections=topbar_sections, show_search=True)

    assert "api.iconify.design/lucide/star.svg" in result


def test_create_html_template_search_mode_button():
    """Test that mode=button renders search toggle (icon only, tap to expand)."""
    from docs_server.templates import create_html_template

    content = "<p>Content</p>"
    topbar_sections = {
        "left": [],
        "middle": [],
        "right": [{"type": "search", "params": {"mode": "button"}}],
    }
    result = create_html_template(content, topbar_sections=topbar_sections, show_search=True)

    assert "search-toggle" in result
    assert "data-search-mode='button'" in result
    assert "aria-label='Open search'" in result


def test_create_html_template_search_mode_input():
    """Test that mode=input renders input only, no trailing icon."""
    from docs_server.templates import create_html_template

    content = "<p>Content</p>"
    topbar_sections = {
        "left": [],
        "middle": [],
        "right": [{"type": "search", "params": {"mode": "input"}}],
    }
    result = create_html_template(content, topbar_sections=topbar_sections, show_search=True)

    assert "data-search-mode='input'" in result
    assert 'name="q"' in result
    # mode=input has no search-input-trailing (icon) span
    search_section = result.split("data-search-mode='input'")[1].split("</form>")[0]
    assert "search-input-trailing" not in search_section


def test_create_html_template_search_params_xss_safe():
    """Search params (mode, placeholder) from topbar.md must not allow XSS injection."""
    from docs_server.templates import create_html_template

    content = "<p>Content</p>"
    topbar_sections = {
        "left": [],
        "middle": [],
        "right": [
            {
                "type": "search",
                "params": {
                    "mode": "full' onload='alert(1)",
                    "placeholder": "Search' onclick='alert(1)",
                },
            }
        ],
    }
    result = create_html_template(content, topbar_sections=topbar_sections, show_search=True)

    # Mode must be sanitized to valid value (malicious mode ignored)
    assert "data-search-mode='full'" in result
    # Must not have attribute breakout: ' onload=' as separate attribute
    assert "' onload='" not in result
    # Placeholder must be escaped (quotes as &#x27;)
    assert "&#x27;" in result


def test_create_html_template_branding_when_enabled():
    """Test that branding is rendered in sidebar when show_branding is True."""
    from docs_server.templates import create_html_template

    navigation = [{"type": "link", "title": "Home", "link": "index.html"}]
    result = create_html_template("<p>Content</p>", navigation=navigation, show_branding=True)

    assert "Powered by servemd" in result
    assert "github.com/jberends/servemd" in result
    assert "servemd-branding" in result


def test_create_html_template_no_branding_when_disabled():
    """Test that branding footer is absent when show_branding is False."""
    from docs_server.templates import create_html_template

    result = create_html_template("<p>Content</p>", show_branding=False)

    assert "Powered by servemd" not in result
    assert "<footer class='servemd-branding'>" not in result


def test_create_html_template_branding_link_attributes():
    """Test that branding link has correct external link attributes."""
    from docs_server.templates import create_html_template

    navigation = [{"type": "link", "title": "Home", "link": "index.html"}]
    result = create_html_template("<p>Content</p>", navigation=navigation, show_branding=True)

    assert 'target="_blank"' in result
    assert 'rel="noopener noreferrer"' in result


def test_create_html_template_search_custom_svg(tmp_path, monkeypatch):
    """Test that custom SVG from DOCS_ROOT is used when path is safe."""
    from docs_server import config
    from docs_server.templates import create_html_template

    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()
    (assets_dir / "search.svg").write_text("<svg></svg>")

    monkeypatch.setattr(config.settings, "DOCS_ROOT", tmp_path)

    content = "<p>Content</p>"
    topbar_sections = {
        "left": [],
        "middle": [],
        "right": [{"type": "search", "params": {"icon": "assets/search.svg"}}],
    }
    result = create_html_template(content, topbar_sections=topbar_sections, show_search=True)

    assert "/assets/search.svg" in result


def test_create_html_template_page_actions_on_doc_page():
    """Test that Copy page dropdown is present when page_actions provided and not search page."""
    from docs_server.templates import create_html_template

    content = "<h1>MCP</h1><p>Model Context Protocol.</p>"
    page_actions = {
        "raw_md_url": "https://docs.example.com/features/mcp.md",
        "page_url": "https://docs.example.com/features/mcp.html",
        "page_title": "MCP",
        "chatgpt_url": "https://chatgpt.com/?prompt=Read+https%3A%2F%2Fdocs.example.com%2Ffeatures%2Fmcp.md+so+I+can+ask+questions+about+it.",
        "claude_url": "https://claude.ai/new?q=Read%20https%3A%2F%2Fdocs.example.com%2Ffeatures%2Fmcp.md%20so%20I%20can%20ask%20questions%20about%20it.",
        "mistral_url": "https://chat.mistral.ai/chat?q=Read+https%3A%2F%2Fdocs.example.com%2Ffeatures%2Fmcp.md+so+I+can+ask+questions+about+it.",
    }
    result = create_html_template(content, page_actions=page_actions, is_search_page=False)

    assert "page-actions" in result
    assert "Copy page" in result
    assert "Copy Markdown link" in result
    assert "View as Markdown" in result
    assert "Open in Mistral Le Chat" in result
    assert "Open in ChatGPT" in result
    assert "Open in Claude" in result
    assert "content-header" in result
    assert "prompt=Read+" in result
    assert "claude.ai/new?q=Read%20" in result
    assert "https://docs.example.com/features/mcp.md" in result


def test_create_html_template_page_actions_absent_on_search_page():
    """Test that Copy page dropdown is absent when is_search_page=True."""
    from docs_server.templates import create_html_template

    content = "<div class='search-page'>Search results</div>"
    page_actions = {
        "raw_md_url": "https://docs.example.com/search.md",
        "page_url": "https://docs.example.com/search.html",
        "page_title": "Search",
        "chatgpt_url": "https://chatgpt.com/?prompt=...",
        "claude_url": "https://claude.ai/new?q=...",
        "mistral_url": "https://chat.mistral.ai/chat?q=...",
    }
    result = create_html_template(content, page_actions=page_actions, is_search_page=True)

    # Dropdown not rendered on search page - menu item text only in dropdown HTML
    assert "Copy Markdown link" not in result


def test_create_html_template_page_actions_without_h1():
    """Test page_actions when content has no h1 - actions prepended."""
    from docs_server.templates import create_html_template

    content = "<p>No heading here.</p>"
    page_actions = {
        "raw_md_url": "https://docs.example.com/index.md",
        "page_url": "https://docs.example.com/index.html",
        "page_title": "Index",
        "chatgpt_url": "https://chatgpt.com/?prompt=...",
        "claude_url": "https://claude.ai/new?q=...",
        "mistral_url": "https://chat.mistral.ai/chat?q=...",
    }
    result = create_html_template(content, page_actions=page_actions, is_search_page=False)

    assert "page-actions" in result
    assert "content-header-actions" in result
    assert "<p>No heading here.</p>" in result


def test_create_html_template_mobile_menu_hamburger_present():
    """Hamburger button and mobile-menu div are present when topbar is rendered."""
    from docs_server.templates import create_html_template

    topbar_sections = {
        "left": [{"type": "logo_link", "title": "Docs", "link": "/"}],
        "middle": [],
        "right": [{"type": "link", "title": "GitHub", "link": "https://github.com"}],
    }
    result = create_html_template("<p>Content</p>", topbar_sections=topbar_sections)

    assert "mobile-menu-toggle" in result
    assert "id='mobile-menu'" in result
    assert "hamburger-bar" in result
    assert "aria-controls='mobile-menu'" in result


def test_create_html_template_mobile_menu_contains_topbar_links():
    """Topbar links appear inside the mobile-menu div."""
    from docs_server.templates import create_html_template

    topbar_sections = {
        "left": [{"type": "logo_link", "title": "MyDocs", "link": "/"}],
        "middle": [],
        "right": [
            {"type": "link", "title": "API Reference", "link": "/api"},
            {"type": "link", "title": "GitHub", "link": "https://github.com"},
        ],
    }
    result = create_html_template("<p>Content</p>", topbar_sections=topbar_sections)

    # Extract content after the mobile-menu opening tag
    mobile_section = result.split("id='mobile-menu'")[1].split("</div>")[0]
    assert "API Reference" in mobile_section
    assert "GitHub" in mobile_section


def test_create_html_template_mobile_menu_logo_excluded():
    """Logo items are excluded from the mobile menu (already visible in topbar)."""
    from docs_server.templates import create_html_template

    topbar_sections = {
        "left": [{"type": "logo_link", "title": "MyDocs", "link": "/"}],
        "middle": [],
        "right": [{"type": "link", "title": "Contact", "link": "/contact"}],
    }
    result = create_html_template("<p>Content</p>", topbar_sections=topbar_sections)

    mobile_section = result.split("id='mobile-menu'")[1].split("</div>")[0]
    # Logo should NOT appear again in the mobile menu
    assert "topbar-logo-link" not in mobile_section
    assert "topbar-logo-container" not in mobile_section


def test_create_html_template_mobile_menu_search_present():
    """Search bar is rendered inside the mobile menu when show_search=True."""
    from docs_server.templates import create_html_template

    topbar_sections = {
        "left": [{"type": "logo_link", "title": "Docs", "link": "/"}],
        "middle": [],
        "right": [{"type": "link", "title": "Help", "link": "/help"}],
    }
    result = create_html_template("<p>Content</p>", topbar_sections=topbar_sections, show_search=True)

    # Mobile menu has its own search form with mobile- prefix IDs
    assert "id='mobile-search-form'" in result
    assert 'id="mobile-search-input"' in result

    mobile_section = result.split("id='mobile-menu'")[1]
    mobile_form_pos = mobile_section.find("mobile-search-form")
    assert mobile_form_pos != -1, "mobile search form must be inside mobile-menu"


def test_create_html_template_mobile_menu_absent_when_no_topbar_and_no_nav():
    """No hamburger or mobile menu when topbar is empty, search off, and no navigation."""
    from docs_server.templates import create_html_template

    topbar_sections = {"left": [], "middle": [], "right": []}
    result = create_html_template(
        "<p>Content</p>", topbar_sections=topbar_sections, show_search=False, navigation=[]
    )

    # The CSS rule name appears in the stylesheet, but the HTML element must not be rendered
    assert "class='mobile-menu-toggle'" not in result
    assert "id='mobile-menu'" not in result


def test_create_html_template_mobile_menu_present_with_navigation_only():
    """Hamburger and mobile menu are rendered even when topbar is empty but navigation exists."""
    from docs_server.templates import create_html_template

    navigation = [{"type": "link", "title": "Home", "link": "/"}]
    result = create_html_template(
        "<p>Content</p>",
        topbar_sections={"left": [], "middle": [], "right": []},
        show_search=False,
        navigation=navigation,
    )

    assert "class='mobile-menu-toggle'" in result
    assert "id='mobile-menu'" in result


def test_create_html_template_mobile_menu_contains_sidebar_nav():
    """Sidebar navigation items are rendered inside the mobile menu."""
    from docs_server.templates import create_html_template

    navigation = [
        {"type": "link", "title": "Home", "link": "/"},
        {
            "type": "group_with_children",
            "title": "Features",
            "link": "/features/",
            "children": [
                {"title": "Search", "link": "/features/search.html"},
                {"title": "MCP", "link": "/features/mcp.html"},
            ],
        },
    ]
    result = create_html_template("<p>Content</p>", navigation=navigation)

    mobile_section = result.split("id='mobile-menu'")[1]
    assert "Home" in mobile_section
    assert "Features" in mobile_section
    assert "Search" in mobile_section
    assert "MCP" in mobile_section


def test_create_html_template_mobile_menu_nav_before_topbar_links():
    """Sidebar nav appears before topbar links in the mobile menu."""
    from docs_server.templates import create_html_template

    navigation = [{"type": "link", "title": "Home", "link": "/"}]
    topbar_sections = {
        "left": [],
        "middle": [],
        "right": [{"type": "link", "title": "GitHub", "link": "https://github.com"}],
    }
    result = create_html_template("<p>Content</p>", navigation=navigation, topbar_sections=topbar_sections)

    mobile_section = result.split("id='mobile-menu'")[1]
    nav_pos = mobile_section.find("mobile-menu-nav")
    topbar_pos = mobile_section.find("mobile-menu-topbar-links")
    assert nav_pos != -1
    assert topbar_pos != -1
    assert nav_pos < topbar_pos, "sidebar nav must appear before topbar links"


def test_create_html_template_mobile_menu_script_present():
    """Mobile menu JS is present when topbar is rendered."""
    from docs_server.templates import create_html_template

    topbar_sections = {
        "left": [{"type": "logo_link", "title": "Docs", "link": "/"}],
        "middle": [],
        "right": [{"type": "link", "title": "Help", "link": "/help"}],
    }
    result = create_html_template("<p>Content</p>", topbar_sections=topbar_sections)

    assert "mobile-menu-toggle" in result
    assert "setMenuOpen" in result
    assert "is-active" in result


def test_create_html_template_mobile_css_included():
    """Mobile hamburger and mobile-menu CSS rules are present."""
    from docs_server.templates import create_html_template

    result = create_html_template("<p>Content</p>")

    assert ".mobile-menu-toggle" in result
    assert ".hamburger-bar" in result
    assert ".mobile-menu" in result


