# TODO: In-Page Search with MCP-Powered Search Bar

**Project:** ServeMD
**Feature:** In-page search with search bar in topbar
**Branch:** `feature-search-topbar`
**Reference:** [GitHub Issue #6](https://github.com/jberends/servemd/issues/6)
**Status:** Implementation (Phase 4 mobile collapse optional)
**Last Updated:** 2026-02-16

---

## Task Analysis

**Summary:** Add an in-page search experience that reuses MCP's Whoosh-based `search_docs` and `SearchResult`. Place a search bar in the topbar right section; on Enter, navigate to `/search?q=...` and display results in the main content area. Sidebar and topbar stay visible.

**Acceptance criteria (from Issue #6):**
- Search bar visible and accessible (topbar)
- Search results displayed in main content area
- Sidebar and topbar remain visible during search
- Results link to actual documentation pages
- Reuses existing MCP search infrastructure
- Responsive on mobile/tablet/desktop

**Dependencies:** MCP must be enabled; Whoosh index must be initialized (happens at startup when `MCP_ENABLED=true`).

**Ambiguities resolved:** See decision summary from planning session (search trigger=Enter, route=/search, result format=untouched, mobile=collapse to icon, keyboard=/ focus + Escape blur).

---

## Overview

Harvest the existing MCP search capabilities to add an in-page search experience for human users. Reuse the MCP search components (Whoosh index, `search_docs`, `SearchResult`) and inject a search bar with search results into the main content area, while maintaining the existing sidebar and topbar layout.

---

## Phased Implementation Checklist

### Phase 1: Backend – Search Route

- [x] Add `GET /search` route in `main.py` **before** the catch-all `/{path:path}`
- [x] Accept query parameter `q`; empty or whitespace-only → redirect to home or do nothing
- [x] Call `mcp.search.search_docs(q)` when index is initialized
- [x] When index unavailable: render page with graceful message "Search will be available once the index is built"
- [x] When no results: show "No results found for 'xyz'"
- [x] Convert `SearchResult.path` (e.g. `features/mcp.md`) to doc URL (e.g. `/features/mcp.html`) for links
- [x] Render results using `format_search_results` output → convert to HTML (untouched format, iterate on display later)
- [x] Use `create_html_template()` with same layout (sidebar, topbar, main content); results in main content area
- [x] Pass `current_path="/search"` for active state when on search page

### Phase 2: Frontend – Search Bar in Topbar

- [x] Add new topbar item type `search` or inject search form in topbar right section
- [x] Search bar visible when MCP enabled; show graceful fallback message when index unavailable
- [x] `<form action="/search" method="GET">` with `<input name="q" placeholder="Search...">`
- [x] Add minimal JS: trim `q` on submit, block empty submit (preventDefault when trimmed empty)
- [x] Pre-fill search input when on `/search?q=...` (read from URL)
- [x] Ensure search bar appears in topbar right (before or after existing links)

### Phase 3: Search Page Redesign

Redesign the search results page for human readability. Layout: topbar + sidebar + content (searchbar + searchresults). The in-page searchbar drives the results div dynamically.

- [x] Add `GET /search` page layout: topbar | sidebar | content (searchbar div + searchresults div)
- [x] **Searchbar div/component:** search input (pre-filled with current `q` from URL) + search button; responsive
- [x] **Searchresults div:** displays MCP search results converted from markdown to HTML; reuse `search_docs` + `format_search_results` pipeline
- [x] Searchbar updates searchresults div when user types: debounced 300ms, minimum 3 characters before search
- [x] Add API endpoint for client-side fetch (e.g. `GET /search.json?q=...` or `GET /search?q=...&format=json`) so the searchresults div can update without full page reload
- [x] Optimise search results markdown format for human readability (iterate interactively on `format_search_results` output or add `format_search_results_human()`)
- [x] Ensure MCP and human share the same underlying search; human page just presents results in a friendlier layout

### Phase 4: Responsive & Keyboard Shortcuts

- [ ] Mobile: collapse search bar to search icon; tap opens full-width search input (overlay or expanded)
- [x] Keyboard: `/` focuses search bar globally (ignore when focus in input/textarea)
- [x] Keyboard: `Escape` blurs search input
- [x] Add CSS for search bar styling (desktop and mobile states)

### Phase 5: Search Result Highlighting

- [x] When on `/search?q=mcp`, highlight all words containing the search term (e.g. "mcp", "MCP") in the results
- [x] Use a pale yellow highlight marker (`<mark>` or equivalent with custom CSS)
- [x] Match case-insensitively (e.g. `q=mcp` highlights both "MCP" and "mcp")
- [x] Apply to titles, snippets, and path text in the rendered search results
- [x] Add CSS class for highlight styling (e.g. `background: #fefce8` or similar pale yellow)

### Phase 6: Configurable Search Placement in topbar.md

Place the search bar exactly where specified in `topbar.md` using a `{search}` placeholder. Support optional parameters for customization.

- [x] Parse `* {search}` or `* {search:params}` in topbar.md sections (left, middle, right)
- [x] When `{search}` present: render search bar at that position; when absent: default to far right of right section
- [x] **Parameters** (simple `key=value` after colon, e.g. `{search:icon=lucide-search}`):
  - `icon` – `lucide-<name>` (e.g. `lucide-search`) for Lucide icon, or path relative to DOCS_ROOT for custom SVG (e.g. `assets/search.svg`)
  - `mode` – `full` (input + icon, default), `button` (icon/button only, tap opens input), `input` (input only, no icon)
  - `placeholder` – override placeholder text (default: "Search...")
- [x] Lucide icons: embed inline SVG from known set (search, x, etc.) or document CDN approach; keep it simple
- [x] Custom SVG from DOCS_ROOT: validate path, prevent traversal; serve via `/assets/` or inline if small
- [x] Document in `docs/navigation.md` or topbar section

### Phase 7: Tests & Documentation

- [x] Unit tests: mock `search_docs`, assert `/search` returns HTML with results, empty query handling
- [x] Integration tests: use `initialized_index` fixture, hit `/search?q=health`, assert results in HTML
- [x] Test: index unavailable → graceful message
- [x] Test: empty results → "No results found"
- [x] Update `docs/features/mcp.md` or add `docs/features/search.md` with search usage
- [x] Update `docs/api/endpoints.md` with `/search` route
- [x] Document keyboard shortcut `/` in docs
- [x] Run `uv run ruff check src/ tests/` and `uv run ruff format src/ tests/`
- [x] Run `uv run pytest tests/ -v` – all tests pass

---

## Success Criteria

- [x] Search bar visible in topbar (right section) when MCP enabled
- [x] Search results displayed in main content area
- [x] Sidebar and topbar remain visible during search
- [x] Results link to actual documentation pages
- [x] Reuses existing MCP search infrastructure (no new index)
- [ ] Responsive on mobile/tablet/desktop (collapse to icon on mobile) — use `{{search:mode=button}}` to enable
- [x] Keyboard shortcut `/` focuses search; `Escape` blurs
- [x] Empty query does nothing; empty results show clear message
- [x] Graceful fallback when index unavailable
- [x] Search terms highlighted in results (pale yellow marker)
- [x] Search page has in-page searchbar + searchresults layout; debounced live search (min 3 chars)
- [x] Search bar placement configurable via `{{search}}` in topbar.md (Phase 6)

---

## Impact Analysis

| Area | Impact |
|------|--------|
| **Routes** | New `/search` route; must be defined before `/{path:path}`; Phase 3: `/search.json?q=...` or similar for client-side fetch |
| **Templates** | `create_html_template` needs `show_search` or search bar injection; new content type for search results; Phase 3 search page layout (searchbar + searchresults divs); highlight CSS for Phase 5; Phase 6: render search at `{search}` position with params |
| **Helpers** | `path_to_doc_url()` for `features/mcp.md` → `/features/mcp.html`; Phase 6: parse `{search}` and `{search:key=val}` in `parse_topbar_links()` |
| **MCP** | No changes to `search_docs`, `SearchResult`, or indexer; reuse as-is |
| **Config** | No new env vars; use `MCP_ENABLED` and index manager `is_initialized` |
| **Tests** | New `test_search_route.py` or extend existing MCP tests |

---

## Key Files to Modify

| File | Changes |
|------|---------|
| `src/docs_server/main.py` | Add `GET /search` route; import `search_docs`, `get_index_manager`; Phase 3: add `/search.json` or `format=json` for AJAX |
| `src/docs_server/templates.py` | Add search bar to topbar; add search results content block; new CSS for search |
| `src/docs_server/helpers.py` | Optional: `path_to_doc_url()` helper; Phase 6: parse `{search}` items in topbar |
| `docs/features/mcp.md` | Add section on human search via topbar |
| `docs/api/endpoints.md` | Document `/search` |
| `tests/test_search_route.py` | New test file (or `test_search.py`) |

