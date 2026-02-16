# TODO: Copy Page Dropdown with AI Links (Nuxt UI-style)

**Project:** ServeMD
**Feature:** Copy page dropdown with AI assistant links (ChatGPT, Claude)
**Reference:** Nuxt UI docs pattern
**Status:** Implemented
**Last Updated:** 2026-02-16

---

## Task Analysis

**Summary:** Add a "Copy page" dropdown button positioned to the **right of the page title** (in the main content area), matching the Nuxt UI documentation pattern. The dropdown provides: Copy Markdown link, View as Markdown, Open in ChatGPT, and Open in Claude.

**Acceptance criteria:**
- Dropdown button visible to the right of the page title (h1) on doc pages
- **Copy Markdown link** – copies a markdown-formatted link to the current page
- **View as Markdown** – opens raw `.md` URL in new tab (external link icon)
- **Open in ChatGPT** – opens ChatGPT with pre-filled prompt: "Read [raw_md_url] so I can ask questions about it."
- **Open in Claude** – opens Claude with pre-filled prompt: "Read [raw_md_url] so I can ask questions about it."
- Not shown on search page or non-doc pages (e.g. index/home if different layout)

**URL formats (from Nuxt UI):**
- **ChatGPT:** `https://chatgpt.com/?prompt=Read+{urlencoded_raw_md_url}+so+I+can+ask+questions+about+it.`
- **Claude:** `https://claude.ai/new?q=Read%20{urlencoded_raw_md_url}%20so%20I%20can%20ask%20questions%20about%20it.`

**Raw markdown URL:** ServeMD serves raw markdown at `/{path}.md` (e.g. `/features/mcp.md`). The full URL is `{BASE_URL}/{path}.md`.

**Placement:** Right of the title, horizontally aligned (see Nuxt UI Badge page: GitHub button + Copy page dropdown next to "Badge" h1).

**Dependencies:** `BASE_URL` or equivalent for absolute URLs; raw markdown route already exists.

---

## Overview

Inject a "Copy page" dropdown in the content area, immediately to the right of the page title. Reuse existing raw markdown serving (`GET /{path}.md`). Build absolute URLs from `BASE_URL` (or request base). Dropdown options mirror Nuxt UI: copy link, view raw, open in ChatGPT, open in Claude.

---

## Phased Implementation Checklist

### Phase 1: Template & Layout

- [x] Add a content header wrapper: title (h1) + action buttons row, flex layout
- [x] Position "Copy page" dropdown button to the right of the title
- [x] Style dropdown to match existing UI (buttons, borders, hover)
- [x] Only render on doc pages (exclude search page, optionally home/index if layout differs)
- [x] Pass `current_doc_path` (e.g. `features/mcp`) and `raw_md_url` (absolute) to template

### Phase 2: Dropdown Options

- [x] **Copy Markdown link** – `[Page Title]({page_url})` copied to clipboard (JS)
- [x] **View as Markdown** – link to `{BASE_URL}/{path}.md` with `target="_blank"` and external link icon
- [x] **Open in ChatGPT** – link: `https://chatgpt.com/?prompt=Read+{urlencode(raw_md_url)}+so+I+can+ask+questions+about+it.`
- [x] **Open in Claude** – link: `https://claude.ai/new?q=Read%20{urlencode(raw_md_url)}%20so%20I%20can%20ask%20questions%20about%20it.`
- [x] Use Lucide or similar icons: link (chain), file-down (M+), ChatGPT logo, Claude logo (or text labels)

### Phase 3: URL & Base URL Handling

- [x] Resolve `BASE_URL` from config (or `request.base_url`) for absolute raw markdown URL
- [x] Raw path: `{path}.md` where path is e.g. `features/mcp` (from `.html` request)
- [x] Ensure URL encoding: `urllib.parse.quote(raw_md_url, safe='')` for prompt/query params
- [x] Handle missing BASE_URL (e.g. relative fallback or omit AI links when unknown)

### Phase 4: Content Structure Changes

- [x] Modify `create_html_template()` to accept `page_actions_html` or `raw_md_url` + `current_doc_path`
- [x] Modify markdown→HTML pipeline or template so the first h1 is wrapped with the actions row
- [x] Option A: Inject actions HTML before/after first h1 via regex or DOM
- [x] Option B: Add a dedicated "content header" block in template, pass title + actions
- [x] Ensure TOC and permalinks still work (IDs on headings)

### Phase 5: Tests & Polish

- [x] Unit test: dropdown present on doc page, absent on search page
- [x] Unit test: ChatGPT link contains correct `prompt=Read+...` with raw md URL
- [x] Unit test: Claude link contains correct `q=Read%20...` with raw md URL
- [x] Unit test: View as Markdown links to `/{path}.md` with correct base
- [x] Run `uv run ruff check src/ tests/` and `uv run ruff format src/ tests/`
- [x] Run `uv run pytest tests/ -v` – all tests pass

### Phase 6: Documentation

- [x] Document in `docs/features/navigation.md` or new `docs/features/copy-page.md`
- [x] Mention BASE_URL requirement for AI links when self-hosting
- [x] Add to configuration if any new env vars (e.g. `COPY_PAGE_ENABLED`)

---

## Success Criteria

- [x] "Copy page" dropdown visible to the right of the page title on doc pages
- [x] Copy Markdown link copies `[Title](url)` to clipboard
- [x] View as Markdown opens raw `.md` in new tab
- [x] Open in ChatGPT uses: `https://chatgpt.com/?prompt=Read+{url}+so+I+can+ask+questions+about+it.`
- [x] Open in Claude uses: `https://claude.ai/new?q=Read%20{url}%20so%20I%20can%20ask%20questions%20about%20it.`
- [x] Raw markdown URL is absolute (BASE_URL + path + .md)
- [x] Dropdown not shown on search page

---

## Impact Analysis

| Area | Impact |
|------|--------|
| **Templates** | New content header block (title + actions); dropdown HTML + CSS |
| **Main** | Pass `raw_md_url`, `current_doc_path`, `page_title` to template |
| **Config** | Use existing `BASE_URL` for absolute URLs |
| **Helpers** | Optional: `build_raw_md_url(path)`, `build_chatgpt_url(raw_url)`, `build_claude_url(raw_url)` |
| **Tests** | New tests for dropdown presence and URL formats |

---

## Key Files to Modify

| File | Changes |
|------|---------|
| `src/docs_server/templates.py` | Content header with title + dropdown; dropdown HTML/CSS |
| `src/docs_server/main.py` | Compute `raw_md_url`, pass to `create_html_template()` |
| `src/docs_server/helpers.py` | Optional URL builders |
| `docs/features/*.md` | Document copy page feature |
| `tests/test_*.py` | New tests |

---

## Appendix: URL Examples

**Current page:** `/features/mcp.html`  
**Raw markdown path:** `features/mcp.md`  
**BASE_URL:** `https://docs.example.com`

- **Raw MD URL:** `https://docs.example.com/features/mcp.md`
- **ChatGPT:** `https://chatgpt.com/?prompt=Read+https%3A%2F%2Fdocs.example.com%2Ffeatures%2Fmcp.md+so+I+can+ask+questions+about+it.`
- **Claude:** `https://claude.ai/new?q=Read%20https%3A%2F%2Fdocs.example.com%2Ffeatures%2Fmcp.md%20so%20I%20can%20ask%20questions%20about%20it.`
