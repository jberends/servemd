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

- [ ] Add `GET /search` route in `main.py` **before** the catch-all `/{path:path}`
- [ ] Accept query parameter `q`; empty or whitespace-only → redirect to home or do nothing
- [ ] Call `mcp.search.search_docs(q)` when index is initialized
- [ ] When index unavailable: render page with graceful message "Search will be available once the index is built"
- [ ] When no results: show "No results found for 'xyz'"
- [ ] Convert `SearchResult.path` (e.g. `features/mcp.md`) to doc URL (e.g. `/features/mcp.html`) for links
- [ ] Render results using `format_search_results` output → convert to HTML (untouched format, iterate on display later)
- [ ] Use `create_html_template()` with same layout (sidebar, topbar, main content); results in main content area
- [ ] Pass `current_path="/search"` for active state when on search page

### Phase 2: Frontend – Search Bar in Topbar

- [ ] Add new topbar item type `search` or inject search form in topbar right section
- [ ] Search bar visible when MCP enabled; show graceful fallback message when index unavailable
- [ ] `<form action="/search" method="GET">` with `<input name="q" placeholder="Search...">`
- [ ] Add minimal JS: trim `q` on submit, block empty submit (preventDefault when trimmed empty)
- [ ] Pre-fill search input when on `/search?q=...` (read from URL)
- [ ] Ensure search bar appears in topbar right (before or after existing links)

### Phase 3: Responsive & Keyboard Shortcuts

- [ ] Mobile: collapse search bar to search icon; tap opens full-width search input (overlay or expanded)
- [ ] Keyboard: `/` focuses search bar globally (ignore when focus in input/textarea)
- [ ] Keyboard: `Escape` blurs search input
- [ ] Add CSS for search bar styling (desktop and mobile states)

### Phase 4: Tests & Documentation

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

---

## Impact Analysis

| Area | Impact |
|------|--------|
| **Routes** | New `/search` route; must be defined before `/{path:path}` |
| **Templates** | `create_html_template` needs `show_search` or search bar injection; new content type for search results |
| **Helpers** | Possibly `path_to_doc_url(path: str) -> str` for converting `features/mcp.md` → `/features/mcp.html` |
| **MCP** | No changes to `search_docs`, `SearchResult`, or indexer; reuse as-is |
| **Config** | No new env vars; use `MCP_ENABLED` and index manager `is_initialized` |
| **Tests** | New `test_search_route.py` or extend existing MCP tests |

---

## Key Files to Modify

| File | Changes |
|------|---------|
| `src/docs_server/main.py` | Add `GET /search` route; import `search_docs`, `get_index_manager` |
| `src/docs_server/templates.py` | Add search bar to topbar; add search results content block; new CSS for search |
| `src/docs_server/helpers.py` | Optional: `path_to_doc_url()` helper |
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

### G. initialized_index fixture (tests/test_mcp_tools.py)

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

### H. format_search_results output (mcp/search.py)

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
