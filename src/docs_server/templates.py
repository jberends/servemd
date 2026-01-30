"""
HTML template generation for ServeMD Documentation Server.
Contains the main HTML template with embedded CSS.
"""

from typing import Any


def create_html_template(
    content: str,
    title: str = "Documentation",
    current_path: str = "",
    navigation: list[dict[str, Any]] = None,
    topbar_sections: dict[str, list[dict[str, str]]] = None,
    toc_items: list[dict[str, str]] = None,
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

    # Generate sidebar HTML with Nuxt UI-style grouping
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

    # Generate topbar HTML with structured sections
    topbar_html = ""
    if any(topbar_sections.values()):  # If any section has items
        topbar_html = "<div class='topbar'>"

        # Left section
        if topbar_sections["left"]:
            topbar_html += "<div class='topbar-left'>"
            for item in topbar_sections["left"]:
                if item["type"] == "logo_link":
                    # Don't show active state for logo - keep it clean
                    topbar_html += f"<a href='{item['link']}' class='topbar-logo-link'>"
                    topbar_html += "<img src='/assets/logo.svg' alt='Logo' class='topbar-logo'>"
                    topbar_html += f"<span class='topbar-logo-text'>{item['title']}</span>"
                    topbar_html += "</a>"
                elif item["type"] == "logo_text":
                    topbar_html += "<div class='topbar-logo-container'>"
                    topbar_html += "<img src='/assets/logo.svg' alt='Logo' class='topbar-logo'>"
                    topbar_html += f"<span class='topbar-logo-text'>{item['title']}</span>"
                    topbar_html += "</div>"
                elif item["type"] == "logo_only":
                    topbar_html += "<div class='topbar-logo-container'>"
                    topbar_html += "<img src='/assets/logo.svg' alt='Logo' class='topbar-logo'>"
                    topbar_html += "</div>"
                elif item["type"] == "text":
                    topbar_html += f"<span class='topbar-text'>{item['title']}</span>"
                elif item["type"] == "link":
                    is_active = current_path == item.get("link", "")
                    active_class = " active" if is_active else ""
                    is_external = item["link"].startswith("http")
                    target_attr = ' target="_blank" rel="noopener noreferrer"' if is_external else ""
                    topbar_html += (
                        f"<a href='{item['link']}' class='topbar-link{active_class}'{target_attr}>{item['title']}</a>"
                    )
            topbar_html += "</div>"

        # Middle section (for future breadcrumbs)
        if topbar_sections["middle"]:
            topbar_html += "<div class='topbar-middle'>"
            for item in topbar_sections["middle"]:
                if item["type"] == "text":
                    topbar_html += f"<span class='topbar-text'>{item['title']}</span>"
                elif item["type"] == "link":
                    is_active = current_path == item.get("link", "")
                    active_class = " active" if is_active else ""
                    is_external = item["link"].startswith("http")
                    target_attr = ' target="_blank" rel="noopener noreferrer"' if is_external else ""
                    topbar_html += (
                        f"<a href='{item['link']}' class='topbar-link{active_class}'{target_attr}>{item['title']}</a>"
                    )
            topbar_html += "</div>"

        # Right section
        if topbar_sections["right"]:
            topbar_html += "<div class='topbar-right'>"
            for item in topbar_sections["right"]:
                if item["type"] == "text":
                    topbar_html += f"<span class='topbar-text'>{item['title']}</span>"
                elif item["type"] == "link":
                    is_active = current_path == item.get("link", "")
                    active_class = " active" if is_active else ""
                    is_external = item["link"].startswith("http")
                    target_attr = ' target="_blank" rel="noopener noreferrer"' if is_external else ""
                    topbar_html += (
                        f"<a href='{item['link']}' class='topbar-link{active_class}'{target_attr}>{item['title']}</a>"
                    )
            topbar_html += "</div>"

        topbar_html += "</div>"

    # Generate TOC sidebar HTML
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


        /* Navigation Content */
        .nav-content {{
            padding: 0;
        }}

        /* Navigation Groups (Nuxt UI style) */
        .nav-group {{
            margin-bottom: 1rem;
        }}

        .nav-group:last-child {{
            margin-bottom: 0;
        }}

        /* Clickable Group Headers (like "Globaal", "Initiatief Overzicht") */
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

        /* Standalone Links (like "Snelle Uitleg") */
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

        /* Group Links Container */
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

        /* Group Links (children under sections) */
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

        /* Active indicator for child items */
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

        /* Main Content - Three Column Layout */
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

        /* Table of Contents Sidebar */
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

        /* Nested TOC items */
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

        /* Improved heading links with hover-only link icon */
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

        /* Link icon styling for TOC-generated headerlinks */
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

        /* Responsive */
        /* Responsive Design */
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
</body>
</html>"""
