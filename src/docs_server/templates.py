"""
HTML template generation for ServeMD Documentation Server.
Contains the main HTML template with embedded CSS.
"""

import html
import re
from typing import Any

from .config import settings
from .helpers import is_safe_path

# Iconify CDN base URL (Nuxt UI / icones.js.org compatible: i-lucide-star, i-lucide-search, etc.)
ICONIFY_CDN = "https://api.iconify.design"

# Lucide icons (inline SVG) for search bar - used when offline or as fallback
LUCIDE_SEARCH_SVG = (
    "<svg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' "
    "fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>"
    "<circle cx='11' cy='11' r='8'/><path d='m21 21-4.35-4.35'/></svg>"
)
LUCIDE_X_SVG = (
    "<svg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' "
    "fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>"
    "<path d='M18 6 6 18'/><path d='m6 6 12 12'/></svg>"
)
LUCIDE_STAR_SVG = (
    "<svg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' "
    "fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>"
    "<polygon points='12 2 15 9 22 9 17 14 19 21 12 17 5 21 7 14 2 9 9 9'/></svg>"
)


def _iconify_img(prefix: str, icon: str, width: int = 18, height: int = 18, css_class: str = "search-icon-img") -> str:
    """Build Iconify CDN img tag for i-{prefix}-{icon} (e.g. i-lucide-star)."""
    if not re.match(r"^[a-z0-9-]+$", icon):
        return LUCIDE_SEARCH_SVG
    url = f"{ICONIFY_CDN}/{prefix}/{icon}.svg?width={width}&height={height}"
    return f"<img src='{url}' alt='' class='{html.escape(css_class)}' width='{width}' height='{height}'>"


def _render_page_actions_dropdown(
    raw_md_url: str,
    page_url: str,
    page_title: str,
    chatgpt_url: str,
    claude_url: str,
    mistral_url: str,
) -> str:
    """Build the Copy page dropdown HTML (Nuxt UI-style)."""
    raw_safe = html.escape(raw_md_url, quote=True)
    chatgpt_safe = html.escape(chatgpt_url, quote=True)
    claude_safe = html.escape(claude_url, quote=True)
    mistral_safe = html.escape(mistral_url, quote=True)
    markdown_link = f"[{page_title}]({page_url})"
    markdown_link_safe = html.escape(markdown_link, quote=True)

    # Lucide-style icons: link, external-link, file-down (inline SVG)
    link_svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' "
        "fill='none' stroke='currentColor' stroke-width='2'><path d='M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71'/>"
        "<path d='M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71'/></svg>"
    )
    external_svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' "
        "fill='none' stroke='currentColor' stroke-width='2'><path d='M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6'/>"
        "<polyline points='15 3 21 3 21 9'/><line x1='10' y1='14' x2='21' y2='3'/></svg>"
    )
    copy_svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' "
        "fill='none' stroke='currentColor' stroke-width='2'><rect x='9' y='9' width='13' height='13' rx='2' ry='2'/>"
        "<path d='M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1'/></svg>"
    )
    openai_icon = _iconify_img("simple-icons", "openai", 16, 16, "page-actions-item-icon")
    anthropic_icon = _iconify_img("simple-icons", "anthropic", 16, 16, "page-actions-item-icon")
    mistral_icon = _iconify_img("simple-icons", "mistralai", 16, 16, "page-actions-item-icon")

    return f"""<div class="page-actions" data-markdown-link="{markdown_link_safe}">
<details class="page-actions-dropdown">
<summary class="page-actions-trigger" aria-haspopup="listbox" aria-expanded="false">
<span class="page-actions-trigger-icon">{copy_svg}</span>
<span class="page-actions-trigger-text">Copy page</span>
<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' class="page-actions-chevron"><polyline points='6 9 12 15 18 9'/></svg>
</summary>
<div class="page-actions-menu">
<a href="#" class="page-actions-item" data-action="copy-link" role="button">
<span class="page-actions-item-icon">{link_svg}</span>Copy Markdown link</a>
<a href="{raw_safe}" target="_blank" rel="noopener noreferrer" class="page-actions-item">
<span class="page-actions-item-icon">{copy_svg}</span>View as Markdown<span class="page-actions-item-ext">{external_svg}</span></a>
<a href="{mistral_safe}" target="_blank" rel="noopener noreferrer" class="page-actions-item"><span class="page-actions-item-icon">{mistral_icon}</span>Open in Mistral Le Chat<span class="page-actions-item-ext">{external_svg}</span></a>
<a href="{chatgpt_safe}" target="_blank" rel="noopener noreferrer" class="page-actions-item"><span class="page-actions-item-icon">{openai_icon}</span>Open in ChatGPT<span class="page-actions-item-ext">{external_svg}</span></a>
<a href="{claude_safe}" target="_blank" rel="noopener noreferrer" class="page-actions-item"><span class="page-actions-item-icon">{anthropic_icon}</span>Open in Claude<span class="page-actions-item-ext">{external_svg}</span></a>
</div>
</details>
</div>"""


def create_html_template(
    content: str,
    title: str = "Documentation",
    current_path: str = "",
    navigation: list[dict[str, Any]] = None,
    topbar_sections: dict[str, list[dict[str, str]]] = None,
    toc_items: list[dict[str, str]] = None,
    show_search: bool = False,
    search_query: str = "",
    is_search_page: bool = False,
    show_branding: bool = True,
    page_actions: dict[str, str] | None = None,
    custom_css_url: str | None = None,
) -> str:
    """
    Create a complete HTML document with sidebar navigation and topbar.
    """
    if navigation is None:
        navigation = []
    if topbar_sections is None:
        topbar_sections = {"left": [], "middle": [], "right": []}
    if toc_items is None:
        toc_items = []

    def _render_search_bar(params: dict[str, str] | None, id_prefix: str = "topbar") -> str:
        """Build search bar HTML with optional icon/mode/placeholder params."""
        p = params or {}
        mode_raw = p.get("mode", "full")
        mode = mode_raw if mode_raw in ("full", "button", "input") else "full"
        placeholder = html.escape(p.get("placeholder", "Search..."), quote=True)
        icon_name = p.get("icon", "lucide-search")
        if icon_name.startswith("i-lucide-"):
            icon_svg = _iconify_img("lucide", icon_name[9:], 18, 18)
        elif icon_name.startswith("lucide-"):
            icon_svg = (
                LUCIDE_X_SVG
                if icon_name == "lucide-x"
                else LUCIDE_STAR_SVG
                if icon_name == "lucide-star"
                else LUCIDE_SEARCH_SVG
            )
        else:
            icon_path = icon_name.strip()
            if icon_path and is_safe_path(icon_path, settings.DOCS_ROOT):
                safe_path = html.escape(icon_path.lstrip("/"), quote=True)
                icon_svg = f"<img src='/{safe_path}' alt='' class='search-icon-img' width='18' height='18'>"
            else:
                icon_svg = LUCIDE_SEARCH_SVG
        search_value = html.escape(search_query, quote=True)
        # full = always show input + trailing icon (not expandable)
        # button = icon only, tap to expand
        # input = input only, no icon
        always_open = mode_raw in ("full", "input")
        show_toggle = mode_raw == "button"
        show_trailing_icon = mode_raw in ("full", "button")
        out = f"<div class='search-bar-wrapper' data-search-mode='{mode}'>"
        if show_toggle:
            out += "<button type='button' class='search-toggle' aria-label='Open search' title='Search (/)'>"
            out += icon_svg
            out += "</button>"
        open_class = " is-open" if (search_query or always_open) else ""
        out += f"<form action='/search' method='GET' class='search-form{open_class}' id='{id_prefix}-search-form'>"
        out += "<span class='search-input-wrap'>"
        out += f'<input type="text" name="q" placeholder="{placeholder}" value="{search_value}" class="search-input" id="{id_prefix}-search-input" autocomplete="off" role="searchbox">'
        if show_trailing_icon:
            out += "<span class='search-input-trailing'>" + icon_svg + "</span>"
        out += "</span></form></div>"
        return out

    def _has_search_placeholder() -> bool:
        return any(item.get("type") == "search" for items in topbar_sections.values() for item in items)

    def _render_topbar_item(item: dict) -> str:
        """Render a single topbar item (link, text, search, logo)."""
        t = item.get("type", "")
        if t == "logo_link":
            return f"<a href='{item['link']}' class='topbar-logo-link'><img src='/assets/logo.svg' alt='Logo' class='topbar-logo'><span class='topbar-logo-text'>{item['title']}</span></a>"
        if t == "logo_text":
            return f"<div class='topbar-logo-container'><img src='/assets/logo.svg' alt='Logo' class='topbar-logo'><span class='topbar-logo-text'>{item['title']}</span></div>"
        if t == "logo_only":
            return (
                "<div class='topbar-logo-container'><img src='/assets/logo.svg' alt='Logo' class='topbar-logo'></div>"
            )
        if t == "text":
            return f"<span class='topbar-text'>{item['title']}</span>"
        if t == "link":
            link = item.get("link", "")
            active = " active" if current_path == link else ""
            ext = ' target="_blank" rel="noopener noreferrer"' if link.startswith("http") else ""
            return f"<a href='{link}' class='topbar-link{active}'{ext}>{item['title']}</a>"
        if t == "search" and show_search:
            return _render_search_bar(item.get("params"))
        return ""

    sidebar_html = ""
    if navigation:
        sidebar_html = "<nav class='sidebar'>"
        sidebar_html += "<div class='nav-content'>"

        for section in navigation:
            section_type = section.get("type", "section")

            if section_type == "link":
                # Standalone link (like "Snelle Uitleg")
                is_active = current_path == section["link"]
                active_class = " active" if is_active else ""
                sidebar_html += "<div class='nav-group'>"
                sidebar_html += (
                    f"<a href='{section['link']}' class='nav-standalone-link{active_class}'>{section['title']}</a>"
                )
                sidebar_html += "</div>"

            elif section_type == "group_with_children":
                # Clickable group header with children (like Nuxt UI "Layout", "Element")
                is_active = current_path == section["link"]
                active_class = " active" if is_active else ""

                sidebar_html += "<div class='nav-group'>"
                sidebar_html += (
                    f"<a href='{section['link']}' class='nav-group-header{active_class}'>{section['title']}</a>"
                )
                sidebar_html += "<ul class='nav-group-links'>"

                for child in section.get("children", []):
                    child_active = current_path == child["link"]
                    child_active_class = " active" if child_active else ""
                    sidebar_html += f"<li class='nav-group-item{child_active_class}'>"
                    sidebar_html += f"<a href='{child['link']}' class='nav-group-link'>{child['title']}</a>"
                    sidebar_html += "</li>"

                sidebar_html += "</ul>"
                sidebar_html += "</div>"

        sidebar_html += "</div>"
        if show_branding:
            sidebar_html += (
                "<div class='servemd-branding'>"
                '<a href="https://github.com/jberends/servemd" target="_blank" rel="noopener noreferrer">'
                "Powered by servemd</a></div>"
            )
        sidebar_html += "</nav>"

    topbar_html = ""
    if navigation or any(topbar_sections.values()) or show_search:
        topbar_html = "<div class='topbar'>"

        if topbar_sections["left"]:
            topbar_html += "<div class='topbar-left'>"
            for item in topbar_sections["left"]:
                topbar_html += _render_topbar_item(item)
            topbar_html += "</div>"
        if topbar_sections["middle"]:
            topbar_html += "<div class='topbar-middle'>"
            for item in topbar_sections["middle"]:
                topbar_html += _render_topbar_item(item)
            topbar_html += "</div>"
        if topbar_sections["right"] or show_search:
            topbar_html += "<div class='topbar-right'>"
            for item in topbar_sections["right"]:
                topbar_html += _render_topbar_item(item)
            if show_search and not _has_search_placeholder():
                topbar_html += _render_search_bar(None)
            topbar_html += "</div>"

        topbar_html += (
            "<button class='mobile-menu-toggle' aria-label='Open menu' "
            "aria-expanded='false' aria-controls='mobile-menu'>"
            "<span class='hamburger-bar'></span>"
            "<span class='hamburger-bar'></span>"
            "<span class='hamburger-bar'></span>"
            "</button>"
        )
        topbar_html += "</div>"

    mobile_menu_html = ""
    mobile_menu_script = ""
    if navigation or any(topbar_sections.values()) or show_search:
        mobile_menu_html = "<div id='mobile-menu' class='mobile-menu'>"

        # 1. Sidebar navigation section
        if navigation:
            mobile_menu_html += "<div class='mobile-menu-nav'>"
            for _section in navigation:
                _stype = _section.get("type", "section")
                if _stype == "link":
                    _active = " active" if current_path == _section["link"] else ""
                    mobile_menu_html += f"<div class='nav-group'><a href='{_section['link']}' class='nav-standalone-link{_active}'>{_section['title']}</a></div>"
                elif _stype == "group_with_children":
                    _active = " active" if current_path == _section["link"] else ""
                    mobile_menu_html += "<div class='nav-group'>"
                    mobile_menu_html += f"<a href='{_section['link']}' class='nav-group-header{_active}'>{_section['title']}</a>"
                    mobile_menu_html += "<ul class='nav-group-links'>"
                    for _child in _section.get("children", []):
                        _cactive = " active" if current_path == _child["link"] else ""
                        mobile_menu_html += f"<li class='nav-group-item{_cactive}'><a href='{_child['link']}' class='nav-group-link'>{_child['title']}</a></li>"
                    mobile_menu_html += "</ul></div>"
            mobile_menu_html += "</div>"

        # 2. Topbar links section (excluding logos and search placeholder)
        _skip_in_mobile = {"logo_link", "logo_text", "logo_only", "search"}
        _topbar_items = [
            _item
            for _item in (
                topbar_sections.get("left", []) + topbar_sections.get("middle", []) + topbar_sections.get("right", [])
            )
            if _item.get("type") not in _skip_in_mobile
        ]
        if _topbar_items:
            if navigation:
                mobile_menu_html += "<div class='mobile-menu-divider'></div>"
            mobile_menu_html += "<div class='mobile-menu-topbar-links'>"
            for _item in _topbar_items:
                mobile_menu_html += _render_topbar_item(_item)
            mobile_menu_html += "</div>"

        # 3. Search
        if show_search:
            _search_item_params = next(
                (
                    _i.get("params")
                    for _items in topbar_sections.values()
                    for _i in _items
                    if _i.get("type") == "search"
                ),
                None,
            )
            _mobile_search_params: dict[str, str] = dict(_search_item_params) if _search_item_params else {}
            _mobile_search_params["mode"] = "full"
            mobile_menu_html += _render_search_bar(_mobile_search_params, id_prefix="mobile")

        mobile_menu_html += "</div>"
        mobile_menu_script = """<script>
(function() {
    var btn = document.querySelector('.mobile-menu-toggle');
    var menu = document.getElementById('mobile-menu');
    if (!btn || !menu) return;

    function setMenuOpen(open) {
        if (open) {
            menu.classList.add('is-open');
            btn.setAttribute('aria-expanded', 'true');
            btn.classList.add('is-active');
        } else {
            menu.classList.remove('is-open');
            btn.setAttribute('aria-expanded', 'false');
            btn.classList.remove('is-active');
        }
    }

    btn.addEventListener('click', function() {
        setMenuOpen(!menu.classList.contains('is-open'));
    });

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && menu.classList.contains('is-open')) {
            setMenuOpen(false);
            btn.focus();
        }
    });

    document.addEventListener('click', function(e) {
        if (menu.classList.contains('is-open') && !menu.contains(e.target) && !btn.contains(e.target)) {
            setMenuOpen(false);
        }
    });

    menu.querySelectorAll('a').forEach(function(link) {
        link.addEventListener('click', function() { setMenuOpen(false); });
    });

    var mobileForm = document.getElementById('mobile-search-form');
    var mobileInput = document.getElementById('mobile-search-input');
    if (mobileForm && mobileInput) {
        mobileForm.addEventListener('submit', function(e) {
            var q = (mobileInput.value || '').trim();
            if (!q) { e.preventDefault(); return false; }
            mobileInput.value = q;
        });
    }
})();
</script>"""

    search_script = ""
    if show_search:
        search_script = """<script>
(function() {
    var form = document.getElementById('topbar-search-form');
    var input = document.getElementById('topbar-search-input');
    var toggle = document.querySelector('.search-toggle');
    if (!form || !input) return;

    if (form.classList.contains('is-open') && toggle) toggle.style.display = 'none';

    form.addEventListener('submit', function(e) {
        var q = (input.value || '').trim();
        if (!q) {
            e.preventDefault();
            return false;
        }
        input.value = q;
    });

    function setExpanded(open) {
        if (open) {
            form.classList.add('is-open');
            if (toggle) toggle.style.display = 'none';
            setTimeout(function() { input.focus(); }, 50);
        } else {
            form.classList.remove('is-open');
            if (toggle) toggle.style.display = '';
            input.blur();
        }
    }

    if (toggle) {
        toggle.addEventListener('click', function() { setExpanded(true); });
    }

    document.addEventListener('click', function(e) {
        var wrapper = document.querySelector('.search-bar-wrapper');
        var mode = wrapper && wrapper.getAttribute('data-search-mode');
        var alwaysOpen = mode === 'full' || mode === 'input';
        if (!alwaysOpen && form.classList.contains('is-open') && wrapper && !wrapper.contains(e.target)) {
            setExpanded(false);
        }
    });

    document.addEventListener('keydown', function(e) {
        var wrapper = document.querySelector('.search-bar-wrapper');
        var mode = wrapper && wrapper.getAttribute('data-search-mode');
        var alwaysOpen = mode === 'full' || mode === 'input';
        if (e.key === '/') {
            var tag = document.activeElement && document.activeElement.tagName.toLowerCase();
            if (tag === 'input' || tag === 'textarea') return;
            e.preventDefault();
            setExpanded(true);
        } else if (e.key === 'Escape') {
            if (alwaysOpen) {
                input.blur();
            } else if (document.activeElement === input || form.classList.contains('is-open')) {
                setExpanded(false);
            }
        }
    });
})();
</script>"""

    search_page_script = ""
    if is_search_page:
        search_page_script = """<script>
(function() {
    var form = document.getElementById('search-page-form');
    var input = document.getElementById('search-page-input');
    var resultsDiv = document.getElementById('search-page-results');
    if (!form || !input || !resultsDiv) return;

    var debounceTimer = null;
    var currentXHR = null;
    var MIN_CHARS = 3;
    var DEBOUNCE_MS = 300;

    function doSearch(query) {
        if (currentXHR) { currentXHR.abort(); currentXHR = null; }
        if (!query || query.length < MIN_CHARS) {
            if (!query) {
                resultsDiv.innerHTML = "<p class='search-no-results'>Enter a search term to find documentation.</p>";
            }
            return;
        }
        resultsDiv.innerHTML = "<p class='search-page-loading'>Searching&hellip;</p>";

        var xhr = new XMLHttpRequest();
        currentXHR = xhr;
        xhr.open('GET', '/search?q=' + encodeURIComponent(query) + '&format=json');
        xhr.setRequestHeader('Accept', 'application/json');
        xhr.onload = function() {
            currentXHR = null;
            if (xhr.status === 200) {
                try {
                    var data = JSON.parse(xhr.responseText);
                    resultsDiv.innerHTML = data.html || "<p class='search-no-results'>No results.</p>";
                } catch(e) {
                    resultsDiv.innerHTML = "<p class='search-no-results'>Error parsing results.</p>";
                }
            } else {
                resultsDiv.innerHTML = "<p class='search-no-results'>Search request failed.</p>";
            }
        };
        xhr.onerror = function() {
            currentXHR = null;
            resultsDiv.innerHTML = "<p class='search-no-results'>Network error.</p>";
        };
        xhr.send();
    }

    input.addEventListener('input', function() {
        var q = (input.value || '').trim();
        // Update URL without reload for bookmarkability
        var url = q ? '/search?q=' + encodeURIComponent(q) : '/search';
        if (history.replaceState) history.replaceState(null, '', url);
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(function() { doSearch(q); }, DEBOUNCE_MS);
    });

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        var q = (input.value || '').trim();
        if (!q) return;
        clearTimeout(debounceTimer);
        // Update URL
        var url = '/search?q=' + encodeURIComponent(q);
        if (history.replaceState) history.replaceState(null, '', url);
        doSearch(q);
    });
})();
</script>"""

    toc_html = ""
    if toc_items:
        toc_html = "<aside class='toc-sidebar'>"
        toc_html += "<div class='toc-header'>On this page</div>"
        toc_html += "<nav class='toc-nav'>"

        for item in toc_items:
            level_class = f"level-{item['level']}" if item["level"] > 1 else ""
            toc_html += f"<div class='toc-item {level_class}'>"
            toc_html += f"<a href='#{item['id']}' class='toc-link'>{item['title']}</a>"
            toc_html += "</div>"

        toc_html += "</nav>"
        toc_html += "</aside>"

    # Inject page actions (Copy page dropdown) after first h1 on doc pages
    final_content = content
    if page_actions and not is_search_page:
        actions_html = _render_page_actions_dropdown(
            raw_md_url=page_actions["raw_md_url"],
            page_url=page_actions["page_url"],
            page_title=page_actions["page_title"],
            chatgpt_url=page_actions["chatgpt_url"],
            claude_url=page_actions["claude_url"],
            mistral_url=page_actions["mistral_url"],
        )
        # Wrap first h1 + actions in content-header for flex layout
        # Use string search instead of regex to avoid ReDoS on user-controlled content
        h1_found = False
        h1_start = content.find("<h1")
        if h1_start != -1:
            open_end = content.find(">", h1_start)
            if open_end != -1:
                close_start = content.find("</h1>", open_end + 1)
                if close_start != -1:
                    close_end = close_start + 6
                    h1_block = content[h1_start:close_end]
                    wrapped = f'<div class="content-header">{h1_block}{actions_html}</div>'
                    final_content = content[:h1_start] + wrapped + content[close_end:]
                    h1_found = True
        if not h1_found:
            # No h1 found, prepend actions at start
            final_content = f'<div class="content-header-actions">{actions_html}</div>{content}'

    safe_title = html.escape(title or "", quote=True)
    custom_css_link = (
        f'<link rel="stylesheet" href="{html.escape(custom_css_url, quote=True)}">' if custom_css_url else ""
    )

    return f"""<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{safe_title}</title>
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' stroke-width='2' stroke='%23f26a28' fill='none' stroke-linecap='round' stroke-linejoin='round'><path stroke='none' d='M0 0h24v24H0z' fill='none'/><path d='M3 19a9 9 0 0 1 9 0a9 9 0 0 1 9 0'/><path d='M3 6a9 9 0 0 1 9 0a9 9 0 0 1 9 0'/><line x1='3' y1='6' x2='3' y2='19'/><line x1='12' y1='6' x2='12' y2='19'/><line x1='21' y1='6' x2='21' y2='19'/></svg>">
    <meta name="description" content="Documentation Server">
    <style>
        :root {{
            /* Accent Colors */
            --accent-primary: #f26a28;
            --accent-black: #000000;

            /* UI Colors */
            --color-primary: #3b82f6;        /* Blue for UI elements */
            --color-primary-50: #eff6ff;
            --color-primary-100: #dbeafe;
            --color-primary-300: #93c5fd;
            --color-primary-600: #2563eb;

            /* Neutral colors */
            --color-neutral-50: #f9fafb;
            --color-gray-50: #f9fafb;
            --color-gray-100: #f3f4f6;
            --color-gray-200: #e5e7eb;
            --color-gray-300: #d1d5db;
            --color-gray-400: #9ca3af;
            --color-gray-500: #6b7280;
            --color-gray-600: #4b5563;
            --color-gray-700: #374151;
            --color-gray-800: #1f2937;
            --color-gray-900: #111827;

            /* Surface backgrounds (override for theming/dark mode) */
            --color-bg-sidebar: #ffffff;
            --color-bg-topbar: #ffffff;
            --color-bg-content: #ffffff;
            --color-bg-toc: transparent;
            --color-bg-branding: #ffffff;

            /* Button and highlight */
            --color-btn-text: #ffffff;
            --color-search-highlight: #fefce8;

            /* Code blocks */
            --color-code-bg: #f9fafb;
            --color-code-border: #e5e7eb;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: ui-sans-serif, system-ui, sans-serif, Apple Color Emoji, Segoe UI Emoji, Segoe UI Symbol, Noto Color Emoji;
            line-height: 1.6;
            color: var(--color-gray-900);
            background-color: var(--color-neutral-50);
            display: flex;
            flex-direction: column;
            min-height: 100vh;
        }}

        /* Sidebar Styles */
        .sidebar {{
            width: 280px;
            background: var(--color-bg-sidebar);
            border-right: 1px solid var(--color-gray-200);
            padding: 0.75rem;
            position: fixed;
            height: calc(100vh - 60px);
            left: 0;
            top: 60px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            z-index: 99;
        }}

        .nav-content {{
            padding: 0;
            flex: 1;
            overflow-y: auto;
            min-height: 0;
        }}

        .nav-group {{
            margin-bottom: 0.5rem;
        }}

        .nav-group:last-child {{
            margin-bottom: 0;
        }}

        .nav-group-header {{
            display: block;
            padding: 0.375rem 0.5rem;
            color: var(--color-gray-700);
            text-decoration: none;
            border-radius: 0.5rem;
            font-weight: 600;
            font-size: 0.875rem;
            transition: all 0.2s;
            margin-bottom: 0.125rem;
        }}

        .nav-group-header:hover {{
            background-color: var(--color-gray-50);
            color: var(--color-gray-900);
        }}

        .nav-group-header.active {{
            background-color: var(--color-primary-100);
            color: var(--color-primary-600);
            border-left: 3px solid var(--accent-primary);
        }}

        .nav-standalone-link {{
            display: block;
            padding: 0.375rem 0.5rem;
            color: var(--color-gray-700);
            text-decoration: none;
            border-radius: 0.5rem;
            font-weight: 500;
            transition: all 0.2s;
            margin-bottom: 0.125rem;
        }}

        .nav-standalone-link:hover {{
            background-color: var(--color-gray-50);
            color: var(--color-gray-900);
        }}

        .nav-standalone-link.active {{
            background-color: var(--color-primary-100);
            color: var(--color-primary-600);
            border-left: 3px solid var(--accent-primary);
        }}

        .nav-group-links {{
            list-style: none;
            padding: 0;
            margin: 0;
            margin-left: 0.75rem;
            border-left: 1px solid var(--color-gray-200);
            padding-left: 0.75rem;
        }}

        .nav-group-item {{
            margin-bottom: 0.125rem;
        }}

        .nav-group-link {{
            display: block;
            padding: 0.25rem 0.5rem;
            color: var(--color-gray-600);
            text-decoration: none;
            border-radius: 0.375rem;
            font-size: 0.875rem;
            font-weight: 400;
            transition: all 0.2s;
            position: relative;
        }}

        .nav-group-link:hover {{
            background-color: var(--color-gray-50);
            color: var(--color-gray-800);
        }}

        .nav-group-item.active .nav-group-link {{
            background-color: var(--color-primary-100);
            color: var(--color-primary-600);
            font-weight: 500;
        }}

        .nav-group-item.active .nav-group-link::before {{
            content: '';
            position: absolute;
            left: -0.75rem;
            top: 50%;
            transform: translateY(-50%);
            width: 1px;
            height: 100%;
            background-color: var(--accent-primary);
        }}

        /* Topbar Styles */
        .topbar {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 60px;
            background: var(--color-bg-topbar);
            border-bottom: 1px solid var(--color-gray-200);
            z-index: 100;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 2rem;
        }}

        .topbar-left {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}

        .topbar-middle {{
            display: flex;
            align-items: center;
            gap: 1rem;
            flex: 1;
            justify-content: center;
        }}

        .topbar-right {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}

        .topbar-logo {{
            height: 32px;
            width: auto;
            border: none;
            margin: 0;
        }}

        .topbar-logo-link {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            text-decoration: none;
            color: var(--color-gray-900);
            font-weight: 600;
            font-size: 1.125rem;
            padding: 0;
            transition: all 0.2s;
        }}

        .topbar-logo-link:hover {{
            opacity: 0.8;
        }}

        .topbar-logo-link.active {{
            background-color: var(--color-primary-100);
            color: var(--color-primary-600);
        }}

        .topbar-logo-container {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}

        .topbar-logo-text {{
            font-weight: 600;
            font-size: 1.125rem;
            color: var(--color-gray-900);
        }}

        .topbar-text {{
            color: var(--color-gray-600);
            font-size: 0.875rem;
            font-weight: 500;
        }}

        .topbar-link {{
            color: var(--color-gray-600);
            text-decoration: none;
            font-size: 0.875rem;
            font-weight: 500;
            padding: 0.5rem 1rem;
            border-radius: 0.375rem;
            transition: all 0.2s;
        }}

        .topbar-link:hover {{
            background-color: var(--color-gray-50);
            color: var(--color-gray-900);
        }}

        .topbar-link.active {{
            background-color: var(--color-primary-100);
            color: var(--color-primary-600);
        }}

        .main-content {{
            flex: 1;
            margin-left: 280px;
            margin-top: 60px;
            padding: 1.25rem;
            display: flex;
            gap: 1.25rem;
            max-width: calc(100vw - 280px);
        }}

        .content {{
            flex: 1;
            max-width: none;
            background: var(--color-bg-content);
            border-radius: 0.75rem;
            padding: 1.25rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            border: 1px solid var(--color-gray-200);
        }}

        .toc-sidebar {{
            width: 240px;
            flex-shrink: 0;
            background: var(--color-bg-toc);
            position: sticky;
            top: calc(60px + 1.25rem);
            height: fit-content;
            max-height: calc(100vh - 60px - 4rem);
            overflow-y: auto;
        }}

        .toc-header {{
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--color-gray-900);
            margin-bottom: 0.5rem;
            padding-bottom: 0.25rem;
            border-bottom: 1px solid var(--color-gray-200);
        }}

        .toc-nav {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}

        .toc-item {{
            margin-bottom: 0.25rem;
        }}

        .toc-link {{
            display: block;
            padding: 0.25rem 0;
            color: var(--color-gray-600);
            text-decoration: none;
            font-size: 0.875rem;
            line-height: 1.4;
            border-left: 2px solid transparent;
            padding-left: 0.75rem;
            transition: all 0.2s;
        }}

        .toc-link:hover {{
            color: var(--color-gray-900);
            border-left-color: var(--color-gray-300);
        }}

        .toc-link.active {{
            color: var(--accent-primary);
            border-left-color: var(--accent-primary);
            font-weight: 500;
        }}

        .toc-item.level-2 .toc-link {{
            padding-left: 1.5rem;
            font-size: 0.8125rem;
        }}

        .toc-item.level-3 .toc-link {{
            padding-left: 2.25rem;
            font-size: 0.8125rem;
        }}

        /* Typography */
        h1, h2, h3, h4, h5, h6 {{
            color: var(--accent-black);
            margin-bottom: 0.75rem;
            font-weight: 600;
            position: relative;
        }}

        h1 .headerlink, h2 .headerlink, h3 .headerlink, h4 .headerlink, h5 .headerlink, h6 .headerlink {{
            opacity: 0;
            margin-left: 0.5rem;
            color: var(--color-gray-400);
            text-decoration: none;
            font-size: 0.8em;
            transition: opacity 0.2s;
            display: inline-flex;
            align-items: center;
        }}

        h1:hover .headerlink, h2:hover .headerlink, h3:hover .headerlink, h4:hover .headerlink, h5:hover .headerlink, h6:hover .headerlink {{
            opacity: 1;
        }}

        .headerlink:hover {{
            color: var(--accent-primary);
        }}

        .headerlink {{
            font-size: 0.875em;
        }}

        h1 {{
            font-size: 2.5rem;
            border-bottom: 2px solid var(--accent-primary);
            padding-bottom: 0.25rem;
            margin-bottom: 1.25rem;
        }}
        h2 {{ font-size: 2rem; margin-top: 1.25rem; }}
        h3 {{ font-size: 1.5rem; margin-top: 1rem; }}

        p {{ margin-bottom: 0.75rem; }}

        /* Code blocks – Nuxt-like smooth appearance, no per-line borders */
        .highlight {{
            position: relative;
            margin: 0.75rem 0;
            border-radius: 0.5rem;
            overflow: hidden;
            background: var(--color-code-bg);
            border: 1px solid var(--color-code-border);
        }}

        .highlight pre {{
            margin: 0;
            padding: 1rem 1.25rem;
            overflow-x: auto;
            font-size: 0.875rem;
            line-height: 1.6;
            font-family: ui-monospace, SFMono-Regular, Monaco, Consolas, monospace;
            background: transparent;
            border: none;
        }}

        .highlight pre code {{
            background: transparent;
            border: none;
            padding: 0;
            font-size: inherit;
        }}

        /* Inline code (not in blocks) */
        :not(pre) > code {{
            background: var(--color-gray-100);
            border: 1px solid var(--color-code-border);
            border-radius: 0.375rem;
            padding: 0.125rem 0.375rem;
            font-size: 0.875em;
            font-family: ui-monospace, SFMono-Regular, Monaco, Consolas, monospace;
        }}

        /* Plain pre/code without .highlight (fallback) */
        pre:not(.highlight pre) {{
            margin: 0.75rem 0;
            padding: 1rem 1.25rem;
            overflow-x: auto;
            font-size: 0.875rem;
            background: var(--color-code-bg);
            border: 1px solid var(--color-code-border);
            border-radius: 0.5rem;
        }}

        pre:not(.highlight pre) code {{
            background: transparent;
            border: none;
            padding: 0;
        }}

        /* Copy button for code blocks */
        .code-copy-btn {{
            position: absolute;
            top: 0.5rem;
            right: 0.5rem;
            padding: 0.375rem 0.5rem;
            font-size: 0.75rem;
            font-weight: 500;
            color: var(--color-gray-500);
            background: var(--color-gray-100);
            border: 1px solid var(--color-code-border);
            border-radius: 0.375rem;
            cursor: pointer;
            opacity: 0.8;
            transition: opacity 0.15s, color 0.15s;
        }}

        .code-copy-btn:hover {{
            opacity: 1;
            color: var(--color-gray-700);
        }}

        .code-copy-btn.copied {{
            color: var(--color-primary-600);
        }}

        /* Tables */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 0.75rem 0;
            border-radius: 0.5rem;
            overflow: hidden;
            border: 1px solid var(--color-gray-200);
        }}

        th, td {{
            padding: 0.5rem 0.75rem;
            text-align: left;
            border-bottom: 1px solid var(--color-gray-200);
        }}

        th {{
            background-color: var(--color-gray-100);
            font-weight: 600;
            color: var(--color-gray-700);
        }}

        tr:hover {{
            background-color: var(--color-gray-50);
        }}

        /* Links */
        a {{
            color: var(--color-primary-600);
            text-decoration: none;
        }}

        a:hover {{
            text-decoration: underline;
            color: var(--accent-primary);
        }}

        /* Lists */
        ul, ol {{
            margin: 0.75rem 0;
            padding-left: 2rem;
        }}

        li {{
            margin-bottom: 0.375rem;
        }}

        /* Blockquotes */
        blockquote {{
            border-left: 4px solid var(--accent-primary);
            padding-left: 0.75rem;
            margin: 0.75rem 0;
            font-style: italic;
            color: var(--color-gray-600);
            background-color: var(--color-gray-50);
            padding: 0.75rem;
            border-radius: 0.5rem;
        }}

        /* Task lists */
        .task-list-item {{
            list-style: none;
            margin-left: -2rem;
            padding-left: 2rem;
        }}

        .task-list-item input[type="checkbox"] {{
            margin-right: 0.5rem;
            accent-color: var(--accent-primary);
        }}

        /* Images */
        img {{
            max-width: 100%;
            height: auto;
            border-radius: 0.5rem;
            margin: 0.75rem 0;
            border: 1px solid var(--color-gray-200);
        }}

        @media (max-width: 1200px) {{
            .toc-sidebar {{
                display: none;
            }}
        }}

        @media (max-width: 1024px) {{
            .sidebar {{
                transform: translateX(-100%);
                transition: transform 0.3s;
            }}

            .main-content {{
                margin-left: 0;
                max-width: 100%;
                padding: 0.75rem;
                flex-direction: column;
            }}

            .content {{
                padding: 1rem;
            }}

        }}

        .search-bar-wrapper {{
            display: flex;
            align-items: center;
            flex-shrink: 0;
        }}

        .search-toggle {{
            display: flex;
            align-items: center;
            justify-content: center;
            background: none;
            border: none;
            padding: 0.5rem;
            cursor: pointer;
            color: var(--color-gray-600);
            border-radius: 0.375rem;
            transition: color 0.15s, background 0.15s;
        }}

        .search-toggle:hover {{
            background: var(--color-gray-100);
            color: var(--color-gray-900);
        }}

        .search-form {{
            display: flex;
            align-items: center;
            width: 0;
            min-width: 0;
            max-width: 0;
            overflow: hidden;
            opacity: 0;
            flex: 0 0 0;
            pointer-events: none;
            transition: max-width 0.2s ease-out, opacity 0.15s ease-out;
        }}

        .search-form.is-open {{
            width: 260px;
            min-width: 260px;
            max-width: 260px;
            flex: 0 0 260px;
            opacity: 1;
            pointer-events: auto;
        }}

        .search-input-wrap {{
            display: flex;
            align-items: center;
            width: 100%;
            background: var(--color-gray-50);
            border: 1px solid var(--color-gray-200);
            border-radius: 0.5rem;
            transition: border-color 0.15s;
        }}

        .search-form.is-open .search-input-wrap {{
            border-color: var(--color-gray-300);
        }}

        .search-form.is-open .search-input-wrap:focus-within {{
            border-color: var(--color-primary-300);
            box-shadow: 0 0 0 2px var(--color-primary-50);
        }}

        .search-input {{
            flex: 1;
            min-width: 0;
            padding: 0.5rem 0.75rem 0.5rem 1rem;
            border: none;
            background: transparent;
            font-size: 0.875rem;
            outline: none;
            -webkit-appearance: none;
            appearance: none;
        }}

        .search-input::-webkit-search-decoration,
        .search-input::-webkit-search-cancel-button,
        .search-input::-webkit-search-results-button,
        .search-input::-webkit-search-results-decoration {{
            display: none;
        }}

        .search-input::placeholder {{
            color: var(--color-gray-400);
        }}

        .search-input-trailing {{
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 0 0.75rem;
            color: var(--color-gray-500);
            flex-shrink: 0;
        }}

        .search-icon-img {{
            object-fit: contain;
        }}

        .search-highlight {{
            background-color: var(--color-search-highlight);
            padding: 0 0.1em;
            border-radius: 2px;
        }}

        .search-page-form {{
            display: flex;
            gap: 0.75rem;
            align-items: stretch;
            margin-bottom: 1.5rem;
        }}

        .search-page-form .search-input-wrap {{
            flex: 1;
        }}

        .search-page-form .search-input-wrap:focus-within {{
            border-color: var(--color-primary-300);
            box-shadow: 0 0 0 2px var(--color-primary-50);
        }}

        .search-page-btn {{
            padding: 0.5rem 1rem;
            font-size: 0.875rem;
            font-weight: 500;
            color: var(--color-btn-text);
            background: var(--color-primary-600);
            border: none;
            border-radius: 0.375rem;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .search-page-btn:hover {{
            background: var(--color-primary);
        }}

        .search-result-count {{
            font-size: 0.875rem;
            color: var(--color-gray-500);
            margin-bottom: 1rem;
        }}

        .search-no-results {{
            color: var(--color-gray-500);
            font-style: italic;
            padding: 2rem 0;
        }}

        .search-result-card {{
            padding: 1rem 0;
            border-bottom: 1px solid var(--color-gray-200);
        }}

        .search-result-card:last-child {{
            border-bottom: none;
        }}

        .search-result-title {{
            font-weight: 600;
        }}

        .search-result-category {{
            display: inline-block;
            margin-left: 0.5rem;
            padding: 0.125rem 0.5rem;
            font-size: 0.75rem;
            font-weight: 500;
            color: var(--color-gray-600);
            background: var(--color-gray-100);
            border-radius: 999px;
            vertical-align: middle;
        }}

        .search-result-path {{
            display: block;
            font-size: 0.8125rem;
            color: var(--color-gray-400);
            font-family: ui-monospace, SFMono-Regular, Monaco, Consolas, monospace;
            margin-top: 0.25rem;
        }}

        .search-result-snippet {{
            margin-top: 0.375rem;
        }}

        .search-page-loading {{
            color: var(--color-gray-400);
            font-size: 0.875rem;
            padding: 1rem 0;
        }}

        @media (max-width: 640px) {{
            .search-page-form {{
                flex-direction: column;
            }}
        }}

        .search-bar-wrapper:has(.search-form.is-open) .search-toggle {{
            display: none;
        }}

        /* Hamburger button – hidden on desktop, shown on mobile */
        .mobile-menu-toggle {{
            display: none;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 5px;
            width: 44px;
            height: 44px;
            padding: 0;
            background: none;
            border: none;
            cursor: pointer;
            color: var(--color-gray-700);
            border-radius: 0.375rem;
            transition: background 0.15s;
            flex-shrink: 0;
        }}

        .mobile-menu-toggle:hover {{
            background: var(--color-gray-100);
        }}

        .hamburger-bar {{
            display: block;
            width: 20px;
            height: 2px;
            background: currentColor;
            border-radius: 2px;
            transition: transform 0.2s, opacity 0.2s;
        }}

        .mobile-menu-toggle.is-active .hamburger-bar:nth-child(1) {{
            transform: translateY(7px) rotate(45deg);
        }}

        .mobile-menu-toggle.is-active .hamburger-bar:nth-child(2) {{
            opacity: 0;
            transform: scaleX(0);
        }}

        .mobile-menu-toggle.is-active .hamburger-bar:nth-child(3) {{
            transform: translateY(-7px) rotate(-45deg);
        }}

        /* Mobile menu panel – hidden by default, only activated on mobile */
        .mobile-menu {{
            display: none;
            position: fixed;
            top: 60px;
            left: 0;
            right: 0;
            background: var(--color-bg-topbar);
            border-bottom: 1px solid var(--color-gray-200);
            z-index: 98;
            overflow: hidden;
        }}

        @media (max-width: 1024px) {{
            /* Show hamburger, hide desktop nav sections from topbar */
            .mobile-menu-toggle {{
                display: flex;
            }}

            .topbar-middle,
            .topbar-right {{
                display: none;
            }}

            /* Hide all topbar-left links/text — topbar shows hamburger only */
            .topbar-left .topbar-link,
            .topbar-left .topbar-text {{
                display: none;
            }}

            /* Mobile menu animation */
            .mobile-menu {{
                display: block;
                max-height: 0;
                opacity: 0;
                padding: 0 1.5rem;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
                transition: max-height 0.25s ease-out, opacity 0.2s ease-out, padding 0.25s ease-out;
            }}

            .mobile-menu.is-open {{
                max-height: 90vh;
                opacity: 1;
                padding: 0.75rem 1.5rem 1rem;
                overflow-y: auto;
            }}

            .mobile-menu .topbar-link {{
                display: block;
                padding: 0.625rem 0.75rem;
                font-size: 0.9375rem;
                border-radius: 0.375rem;
            }}

            .mobile-menu .topbar-logo-link,
            .mobile-menu .topbar-logo-container {{
                display: none;
            }}

            /* Sidebar nav section inside mobile menu */
            .mobile-menu-nav {{
                padding-bottom: 0.5rem;
            }}

            /* Divider between nav and topbar links */
            .mobile-menu-divider {{
                height: 1px;
                background: var(--color-gray-200);
                margin: 0.5rem 0;
            }}

            /* Topbar links section inside mobile menu */
            .mobile-menu-topbar-links {{
                padding: 0.25rem 0;
            }}

            /* Search bar inside mobile menu: always fully visible */
            .mobile-menu .search-bar-wrapper {{
                display: flex;
                margin-top: 0.5rem;
                padding-top: 0.5rem;
                border-top: 1px solid var(--color-gray-200);
            }}

            .mobile-menu .search-form,
            .mobile-menu .search-form.is-open {{
                position: static;
                width: 100%;
                min-width: 0;
                max-width: 100%;
                flex: 1;
                opacity: 1;
                visibility: visible;
                transform: none;
                box-shadow: none;
            }}
        }}

        .servemd-branding {{
            flex-shrink: 0;
            font-size: 0.8125rem;
            color: var(--color-gray-500);
            padding: 0.5rem 0 0;
            margin-top: auto;
            border-top: 1px solid var(--color-gray-200);
            background: var(--color-bg-branding);
        }}

        .servemd-branding a {{
            color: var(--color-gray-500);
            text-decoration: none;
        }}

        .servemd-branding a:hover {{
            color: var(--color-gray-700);
            text-decoration: underline;
        }}

        /* Content header: title + Copy page dropdown (Nuxt UI-style) */
        .content-header {{
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 1rem;
            margin-bottom: 1.25rem;
            flex-wrap: wrap;
        }}

        .content-header h1 {{
            margin-bottom: 0;
            flex: 1;
            min-width: 0;
        }}

        .content-header-actions {{
            margin-bottom: 1rem;
        }}

        .page-actions {{
            flex-shrink: 0;
        }}

        .page-actions-dropdown {{
            position: relative;
            display: inline-block;
        }}

        .page-actions-trigger {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.375rem 0.75rem;
            font-size: 0.875rem;
            font-weight: 500;
            color: var(--color-gray-600);
            background: var(--color-gray-50);
            border: 1px solid var(--color-gray-200);
            border-radius: 0.375rem;
            cursor: pointer;
            list-style: none;
            transition: all 0.15s;
        }}

        .page-actions-trigger::-webkit-details-marker {{
            display: none;
        }}

        .page-actions-trigger:hover {{
            background: var(--color-gray-100);
            color: var(--color-gray-900);
            border-color: var(--color-gray-300);
        }}

        .page-actions-trigger-icon {{
            display: flex;
            align-items: center;
        }}

        .page-actions-chevron {{
            flex-shrink: 0;
            opacity: 0.7;
            transition: transform 0.2s;
        }}

        .page-actions-dropdown[open] .page-actions-chevron {{
            transform: rotate(180deg);
        }}

        .page-actions-menu {{
            position: absolute;
            top: 100%;
            right: 0;
            margin-top: 0.25rem;
            min-width: 260px;
            background: var(--color-bg-content);
            border: 1px solid var(--color-gray-200);
            border-radius: 0.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
            z-index: 50;
            padding: 0.25rem;
        }}

        .page-actions-item {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            min-height: 2.25rem;
            padding: 0.5rem 0.75rem;
            font-size: 0.875rem;
            color: var(--color-gray-700);
            text-decoration: none;
            border-radius: 0.375rem;
            transition: background 0.15s;
            white-space: nowrap;
        }}

        .page-actions-item:hover {{
            background: var(--color-gray-50);
            color: var(--color-gray-900);
        }}

        .page-actions-item[data-action="copy-link"] {{
            cursor: pointer;
        }}

        .page-actions-item-icon {{
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            width: 16px;
            height: 16px;
        }}

        .page-actions-item-icon img {{
            display: block;
            object-fit: contain;
        }}

        .page-actions-item-ext {{
            margin-left: auto;
            opacity: 0.6;
        }}
    </style>
    {custom_css_link}
</head>
<body>
    {sidebar_html}
    {topbar_html}
    {mobile_menu_html}
    <div class="main-content">
        <div class="content">
            {final_content}
        </div>
        {toc_html}
    </div>
    {search_script}
    {search_page_script}
    {mobile_menu_script}
    <script>
    (function() {{
        var copyLinkBtn = document.querySelector('.page-actions-item[data-action="copy-link"]');
        if (copyLinkBtn) {{
            copyLinkBtn.addEventListener('click', function(e) {{
                e.preventDefault();
                var wrap = document.querySelector('.page-actions[data-markdown-link]');
                if (!wrap) return;
                var text = wrap.getAttribute('data-markdown-link');
                if (!text) return;
                navigator.clipboard.writeText(text).then(function() {{
                    var orig = copyLinkBtn.innerHTML;
                    copyLinkBtn.innerHTML = '<span class="page-actions-item-icon">✓</span>Copied!';
                    setTimeout(function() {{ copyLinkBtn.innerHTML = orig; }}, 1500);
                }});
            }});
        }}

        document.querySelectorAll('.highlight').forEach(function(block) {{
            var pre = block.querySelector('pre');
            if (!pre) return;
            var btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'code-copy-btn';
            btn.textContent = 'Copy';
            btn.setAttribute('aria-label', 'Copy code');
            btn.onclick = function() {{
                var code = pre.querySelector('code') || pre;
                var text = (code.innerText || code.textContent || '').trim();
                navigator.clipboard.writeText(text).then(function() {{
                    btn.textContent = 'Copied!';
                    btn.classList.add('copied');
                    setTimeout(function() {{
                        btn.textContent = 'Copy';
                        btn.classList.remove('copied');
                    }}, 2000);
                }});
            }};
            block.appendChild(btn);
        }});
    }})();
    </script>
</body>
</html>"""
