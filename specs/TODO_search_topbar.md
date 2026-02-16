# TODO: In-Page Search with MCP-Powered Search Bar

**Project:** ServeMD
**Feature:** In-page search with search bar in topbar
**Branch:** `feature-search-topbar`
**Reference:** [GitHub Issue #6](https://github.com/jberends/servemd/issues/6)
**Status:** Planning
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

- [ ] Add `GET /search` page layout: topbar | sidebar | content (searchbar div + searchresults div)
- [ ] **Searchbar div/component:** search input (pre-filled with current `q` from URL) + search button; responsive
- [ ] **Searchresults div:** displays MCP search results converted from markdown to HTML; reuse `search_docs` + `format_search_results` pipeline
- [ ] Searchbar updates searchresults div when user types: debounced 300ms, minimum 3 characters before search
- [ ] Add API endpoint for client-side fetch (e.g. `GET /search.json?q=...` or `GET /search?q=...&format=json`) so the searchresults div can update without full page reload
- [ ] Optimise search results markdown format for human readability (iterate interactively on `format_search_results` output or add `format_search_results_human()`)
- [ ] Ensure MCP and human share the same underlying search; human page just presents results in a friendlier layout

### Phase 4: Responsive & Keyboard Shortcuts

- [ ] Mobile: collapse search bar to search icon; tap opens full-width search input (overlay or expanded)
- [x] Keyboard: `/` focuses search bar globally (ignore when focus in input/textarea)
- [x] Keyboard: `Escape` blurs search input
- [x] Add CSS for search bar styling (desktop and mobile states)

### Phase 5: Search Result Highlighting

- [ ] When on `/search?q=mcp`, highlight all words containing the search term (e.g. "mcp", "MCP") in the results
- [ ] Use a pale yellow highlight marker (`<mark>` or equivalent with custom CSS)
- [ ] Match case-insensitively (e.g. `q=mcp` highlights both "MCP" and "mcp")
- [ ] Apply to titles, snippets, and path text in the rendered search results
- [ ] Add CSS class for highlight styling (e.g. `background: #fefce8` or similar pale yellow)

### Phase 6: Configurable Search Placement in topbar.md

Place the search bar exactly where specified in `topbar.md` using a `{search}` placeholder. Support optional parameters for customization.

- [ ] Parse `* {search}` or `* {search:params}` in topbar.md sections (left, middle, right)
- [ ] When `{search}` present: render search bar at that position; when absent: default to far right of right section
- [ ] **Parameters** (simple `key=value` after colon, e.g. `{search:icon=lucide-search}`):
  - `icon` – `lucide-<name>` (e.g. `lucide-search`) for Lucide icon, or path relative to DOCS_ROOT for custom SVG (e.g. `assets/search.svg`)
  - `mode` – `full` (input + icon, default), `button` (icon/button only, tap opens input), `input` (input only, no icon)
  - `placeholder` – override placeholder text (default: "Search...")
- [ ] Lucide icons: embed inline SVG from known set (search, x, etc.) or document CDN approach; keep it simple
- [ ] Custom SVG from DOCS_ROOT: validate path, prevent traversal; serve via `/assets/` or inline if small
- [ ] Document in `docs/navigation.md` or topbar section

**Example topbar.md:**
```markdown
## right
* [GitHub](https://github.com/...)
* [Docker](https://hub.docker.com/...)
* {search}
```

Or with params: `* {search:icon=lucide-search,mode=button}`

### Phase 7: Tests & Documentation

- [ ] Unit tests: mock `search_docs`, assert `/search` returns HTML with results, empty query handling
- [ ] Integration tests: use `initialized_index` fixture, hit `/search?q=health`, assert results in HTML
- [ ] Test: index unavailable → graceful message
- [ ] Test: empty results → "No results found"
- [ ] Update `docs/features/mcp.md` or add `docs/features/search.md` with search usage
- [ ] Update `docs/api/endpoints.md` with `/search` route
- [ ] Document keyboard shortcut `/` in docs
- [ ] Run `uv run ruff check src/ tests/` and `uv run ruff format src/ tests/`
- [ ] Run `uv run pytest tests/ -v` – all tests pass

---

## Success Criteria

- [ ] Search bar visible in topbar (right section) when MCP enabled
- [ ] Search results displayed in main content area
- [ ] Sidebar and topbar remain visible during search
- [ ] Results link to actual documentation pages
- [ ] Reuses existing MCP search infrastructure (no new index)
- [ ] Responsive on mobile/tablet/desktop (collapse to icon on mobile)
- [ ] Keyboard shortcut `/` focuses search; `Escape` blurs
- [ ] Empty query does nothing; empty results show clear message
- [ ] Graceful fallback when index unavailable
- [ ] Search terms highlighted in results (pale yellow marker)
- [ ] Search page has in-page searchbar + searchresults layout; debounced live search (min 3 chars)
- [ ] Search bar placement configurable via `{search}` in topbar.md (Phase 6)

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

---

## Appendix: Code Examples & References

### A. Route definition order (main.py)

Routes are matched in definition order. The catch-all `/{path:path}` must come last:

```python
# main.py - Route order matters
@app.get("/")
async def root(): ...

@app.get("/health")
async def health_check(): ...

@app.get("/search")  # ADD BEFORE catch-all
async def search_page(q: str = ""): ...

@app.get("/{path:path}")  # Catch-all last
async def serve_content(path: str, request: Request): ...
```

### B. MCP search usage (mcp/search.py, mcp/tools.py)

```python
from docs_server.mcp import search_docs, SearchResult

# search_docs returns list[SearchResult]
results = search_docs(query="authentication", limit=10)

# SearchResult fields: path, title, snippet, score, category
# format_search_results for text output (MCP format)
from docs_server.mcp.search import format_search_results
formatted = format_search_results(results)
```

### C. Index availability check (mcp/indexer.py)

```python
from docs_server.mcp import get_index_manager

manager = get_index_manager()
if manager.is_initialized:
    # Safe to call search_docs
    results = search_docs(q)
else:
    # Show graceful fallback
    pass
```

### D. Topbar right section injection (templates.py)

Current topbar right renders items from `topbar_sections["right"]`. Each item has `type` and `title`/`link`. Add a new type `search`:

```python
# In topbar right section loop, before or after existing items:
elif item["type"] == "search":
    # Render search form
    topbar_html += '<form action="/search" method="GET" class="search-form">'
    topbar_html += '<input type="search" name="q" placeholder="Search..." value="">'
    topbar_html += '</form>'
```

Alternatively, inject search form directly in template when `show_search=True`, without extending topbar.md parsing.

### E. Path to doc URL conversion

```python
def path_to_doc_url(path: str) -> str:
    """Convert SearchResult.path (e.g. features/mcp.md) to doc URL (/features/mcp.html)."""
    if path.endswith(".md"):
        path = path[:-3] + ".html"
    return "/" + path.lstrip("/")
```

### F. create_html_template signature (templates.py)

```python
def create_html_template(
    content: str,
    title: str = "Documentation",
    current_path: str = "",
    navigation: list[dict[str, Any]] = None,
    topbar_sections: dict[str, list[dict[str, str]]] = None,
    toc_items: list[dict[str, str]] = None,
) -> str:
```

For search page: pass `content` = rendered search results HTML, `title` = "Search results", `current_path` = "/search", `toc_items` = [] (no TOC on search page).

### G. Search page layout (Phase 3)

```
┌─────────────────────────────────────────────────────────┐
│ topbar (logo, links)                                    │
├──────────────┬──────────────────────────────────────────┤
│ sidebar      │ content                                  │
│ (nav links)  │ ┌──────────────────────────────────────┐ │
│              │ │ searchbar div                        │ │
│              │ │ [search input........] [Search]      │ │
│              │ └──────────────────────────────────────┘ │
│              │ ┌──────────────────────────────────────┐ │
│              │ │ searchresults div                    │ │
│              │ │ (MCP results, markdown → HTML)       │ │
│              │ └──────────────────────────────────────┘ │
└──────────────┴──────────────────────────────────────────┘
```

- Searchbar: debounce 300ms, min 3 chars; fetches `/search.json?q=...` (or similar) and injects HTML into searchresults div
- Searchresults: receives HTML fragment or full results; reuses `format_search_results` → markdown → HTML pipeline

### H. initialized_index fixture (tests/test_mcp_tools.py)

```python
@pytest.fixture
async def initialized_index(temp_docs_root, temp_cache_root):
    """Create an initialized search index with test documents."""
    with patch("docs_server.mcp.indexer.settings") as mock_settings:
        mock_settings.DOCS_ROOT = temp_docs_root
        mock_settings.CACHE_ROOT = temp_cache_root
        ...
        await manager.initialize(force_rebuild=True)
        yield manager
```

Reuse this fixture in search route tests with `@pytest.mark.asyncio` and `async def test_search_returns_results(initialized_index):`.

### I. format_search_results output (mcp/search.py)

```
Found 3 result(s):

1. **MCP Support** (`features/mcp.md`)
   Category: features
   Score: 2.45
   MCP enables LLM integration. Available tools: search_docs...

2. **API Endpoints** (`api/endpoints.md`)
   ...
```

Convert this markdown-style text to HTML (e.g. `markdown.markdown()` or simple regex for `**bold**` and links). For "untouched" iteration: use `format_search_results` output → convert to HTML with minimal processing (e.g. newlines to `<br>`, `**x**` to `<strong>x</strong>`).

### J. Search term highlighting (Phase 5)

When rendering search results, wrap matched terms in `<mark class="search-highlight">`:

```python
# After converting format_search_results to HTML, wrap search terms:
import re
def highlight_search_terms(html: str, query: str) -> str:
    if not query or not query.strip():
        return html
    pattern = re.compile(re.escape(query.strip()), re.IGNORECASE)
    return pattern.sub(lambda m: f'<mark class="search-highlight">{m.group(0)}</mark>', html)
```

CSS for pale yellow highlight:

```css
.search-highlight {
    background-color: #fefce8;  /* pale yellow */
    padding: 0 0.1em;
    border-radius: 2px;
}
```

Note: Match whole words or substrings? User said "words containing" – so `q=mcp` highlights "mcp", "MCP", "mcp-support" etc. Use `re.escape()` for safety with special regex chars.

### K. Configurable search placement (Phase 6)

**Syntax in topbar.md:**
```
* {search}                    # Default: full input + icon at this position
* {search:icon=lucide-search} # Lucide icon by name
* {search:icon=assets/search.svg}  # Custom SVG from DOCS_ROOT
* {search:mode=button}        # Icon/button only, tap opens input
* {search:mode=input}         # Input only, no icon
* {search:placeholder=Zoeken...}  # Custom placeholder
* {search:icon=lucide-search,mode=button}  # Combined params
```

**Parser logic:** In `parse_topbar_links()`, when `item_text` matches `{search}` or `{search:...}`, append `{"type": "search", "params": {...}}` to current section. Params parsed from `key=value` pairs after `:`.

**Template logic:** When iterating topbar items, `elif item["type"] == "search"` renders the search bar with `item.get("params", {})` for icon/mode/placeholder overrides.
