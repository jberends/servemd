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

    def _render_search_bar(params: dict[str, str] | None) -> str:
        """Build search bar HTML with optional icon/mode/placeholder params."""
        p = params or {}
        mode = p.get("mode", "full")
        placeholder = p.get("placeholder", "Search...")
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
                icon_svg = f"<img src='/{icon_path.lstrip('/')}' alt='' class='search-icon-img' width='18' height='18'>"
            else:
                icon_svg = LUCIDE_SEARCH_SVG
        search_value = html.escape(search_query, quote=True)
        # full = always show input + trailing icon (not expandable)
        # button = icon only, tap to expand
        # input = input only, no icon
        always_open = mode in ("full", "input")
        show_toggle = mode == "button"
        show_trailing_icon = mode in ("full", "button")
        out = f"<div class='search-bar-wrapper' data-search-mode='{mode}'>"
        if show_toggle:
            out += "<button type='button' class='search-toggle' aria-label='Open search' title='Search (/)'>"
            out += icon_svg
            out += "</button>"
        open_class = " is-open" if (search_query or always_open) else ""
        out += f"<form action='/search' method='GET' class='search-form{open_class}' id='topbar-search-form'>"
        out += "<span class='search-input-wrap'>"
        out += f'<input type="text" name="q" placeholder="{html.escape(placeholder)}" value="{search_value}" class="search-input" id="topbar-search-input" autocomplete="off" role="searchbox">'
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

        sidebar_html += "</div></nav>"

    topbar_html = ""
    if any(topbar_sections.values()) or show_search:  # If any section has items or search bar
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

        topbar_html += "</div>"

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

    return f"""<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
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
            min-height: 100vh;
        }}

        /* Sidebar Styles */
        .sidebar {{
            width: 280px;
            background: white;
            border-right: 1px solid var(--color-gray-200);
            padding: 1rem;
            overflow-y: auto;
            position: fixed;
            height: calc(100vh - 60px);
            left: 0;
            top: 60px;
        }}

        .nav-content {{ padding: 0; }}

        .nav-group {{
            margin-bottom: 1rem;
        }}

        .nav-group:last-child {{
            margin-bottom: 0;
        }}

        .nav-group-header {{
            display: block;
            padding: 0.5rem 0.75rem;
            color: var(--color-gray-700);
            text-decoration: none;
            border-radius: 0.5rem;
            font-weight: 600;
            font-size: 0.875rem;
            transition: all 0.2s;
            margin-bottom: 0.25rem;
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
            padding: 0.5rem 0.75rem;
            color: var(--color-gray-700);
            text-decoration: none;
            border-radius: 0.5rem;
            font-weight: 500;
            transition: all 0.2s;
            margin-bottom: 0.25rem;
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
            padding: 0.375rem 0.75rem;
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
            background: white;
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
            padding: 2rem;
            display: flex;
            gap: 2rem;
            max-width: calc(100vw - 280px);
        }}

        .content {{
            flex: 1;
            max-width: none;
            background: white;
            border-radius: 0.75rem;
            padding: 2rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            border: 1px solid var(--color-gray-200);
        }}

        .toc-sidebar {{
            width: 240px;
            flex-shrink: 0;
            position: sticky;
            top: calc(60px + 2rem);
            height: fit-content;
            max-height: calc(100vh - 60px - 4rem);
            overflow-y: auto;
        }}

        .toc-header {{
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--color-gray-900);
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
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
            margin-bottom: 1rem;
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
            padding-bottom: 0.5rem;
            margin-bottom: 2rem;
        }}
        h2 {{ font-size: 2rem; margin-top: 2rem; }}
        h3 {{ font-size: 1.5rem; margin-top: 1.5rem; }}

        p {{ margin-bottom: 1rem; }}

        /* Code blocks */
        .highlight, pre, code {{
            background: var(--color-gray-100);
            border: 1px solid var(--color-gray-200);
            border-radius: 0.5rem;
            font-family: ui-monospace, SFMono-Regular, Monaco, Consolas, monospace;
        }}

        .highlight, pre {{
            padding: 1rem;
            margin: 1rem 0;
            overflow-x: auto;
            font-size: 0.875rem;
        }}

        code {{
            padding: 0.125rem 0.25rem;
            font-size: 0.875rem;
        }}

        /* Tables */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
            border-radius: 0.5rem;
            overflow: hidden;
            border: 1px solid var(--color-gray-200);
        }}

        th, td {{
            padding: 0.75rem;
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
            margin: 1rem 0;
            padding-left: 2rem;
        }}

        li {{
            margin-bottom: 0.5rem;
        }}

        /* Blockquotes */
        blockquote {{
            border-left: 4px solid var(--accent-primary);
            padding-left: 1rem;
            margin: 1rem 0;
            font-style: italic;
            color: var(--color-gray-600);
            background-color: var(--color-gray-50);
            padding: 1rem;
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
            margin: 1rem 0;
            border: 1px solid var(--color-gray-200);
        }}

        @media (max-width: 1200px) {{
            .toc-sidebar {{
                display: none;
            }}
        }}

        @media (max-width: 768px) {{
            .sidebar {{
                transform: translateX(-100%);
                transition: transform 0.3s;
            }}

            .main-content {{
                margin-left: 0;
                padding: 1rem;
                flex-direction: column;
            }}

            .content {{
                padding: 1.5rem;
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
            background-color: #fefce8;
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
            color: white;
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

        @media (max-width: 768px) {{
            .search-form {{
                position: absolute;
                top: 100%;
                right: 0;
                margin-top: 0.5rem;
                width: 0;
                min-width: 0;
                max-width: 0;
                flex: 0 0 0;
                opacity: 0;
                visibility: hidden;
                transform: translateY(-0.25rem);
                transition: width 0.2s ease-out, opacity 0.15s ease-out, visibility 0.15s, transform 0.2s ease-out;
                z-index: 200;
            }}

            .search-form.is-open {{
                width: min(320px, calc(100vw - 2rem));
                min-width: min(320px, calc(100vw - 2rem));
                max-width: min(320px, calc(100vw - 2rem));
                flex: 0 0 auto;
                opacity: 1;
                visibility: visible;
                transform: translateY(0);
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
            }}

        }}
    </style>
</head>
<body>
    {sidebar_html}
    {topbar_html}
    <div class="main-content">
        <div class="content">
            {content}
        </div>
        {toc_html}
    </div>
    {search_script}
    {search_page_script}
</body>
</html>"""
