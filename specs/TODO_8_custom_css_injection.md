# TODO: Custom CSS Injection for Look and Feel Customization

**Project:** ServeMD
**Feature:** Custom CSS injection
**Branch:** `8-custom-css-injection`
**Reference:** [GitHub Issue #8](https://github.com/jberends/servemd/issues/8)
**Status:** Planning
**Last Updated:** 2026-02-16

---

## Task Analysis

**Summary:** Allow users to inject custom CSS to customize the look and feel of their documentation site without modifying servemd's core templates. Supports branding, theming, and layout tweaks.

**Acceptance criteria (from Issue #8):**
- Custom CSS file in `DOCS_ROOT` is loaded on every page
- Custom CSS loads after default styles (correct cascade/override)
- Configurable filename via env var
- File is served with `Content-Type: text/css`
- Documented in configuration guide
- Example `custom.css` in examples/ or docs/

**Expanded scope (user feedback):**
- Ship multiple examples: basic `custom.css` + `night-mode.css` (dark theme)
- Extensive documentation: dedicated customization guide + CSS variables reference
- CSS cleanup: replace hardcoded colors (e.g. `white`) with variables so themes can override consistently

**Optional enhancements (out of scope):**
- Support multiple CSS files
- Support inline custom CSS via config
- Hot-reload of custom CSS in DEBUG mode

**Dependencies:** None. Standalone feature.

**Ambiguities:**
- Default filename: Issue suggests `custom.css` as default when present. We'll use `custom.css` as default, configurable via `CUSTOM_CSS`.
- URL path: Serve at `/custom.css` or a dedicated path like `/assets/custom.css`? Using `/custom.css` keeps it simple and matches the filename; path must be validated to prevent conflicts with doc routes.

---

## Overview

Add file-based custom CSS support: a `custom.css` (or configurable name) in `DOCS_ROOT` is automatically loaded on every page. The `<link>` is injected after the main embedded styles so custom rules override defaults. The file is served from a dedicated route with `Content-Type: text/css`. Path validation ensures the file stays within `DOCS_ROOT`.

---

## Phased Implementation Checklist

### Phase 0: CSS Cleanup (prerequisite for good theming)

- [x] Audit `templates.py` embedded CSS for hardcoded colors
- [x] Add surface/background variables: `--color-bg-sidebar`, `--color-bg-topbar`, `--color-bg-content`, `--color-bg-toc`, `--color-bg-branding`
- [x] Replace `background: white` with `var(--color-bg-*)` in sidebar, topbar, content, toc-sidebar, servemd-branding
- [x] Add `--color-text-heading` (or use existing `--accent-black`) for heading color
- [x] Add `--color-btn-text` for button text (e.g. search button `color: white`)
- [x] Add `--color-search-highlight` for search term highlight (`#fefce8` → variable)
- [x] Document all variables in a single `:root` block with clear comments; ensure no regressions

### Phase 1: Configuration

- [x] Add `CUSTOM_CSS` to `config.py` (default: `custom.css`)
- [x] Parse `os.getenv("CUSTOM_CSS", "custom.css")` – filename only, no path
- [x] Add helper to resolve custom CSS path: `settings.DOCS_ROOT / settings.CUSTOM_CSS`
- [x] Validate filename: must end with `.css` and not contain path separators (security)

### Phase 2: Endpoint & Serving

- [x] Add route `GET /custom.css` that serves the file from `DOCS_ROOT` (filename from `CUSTOM_CSS`)
- [x] Use `get_file_path()` or equivalent to resolve path with `is_safe_path()` validation
- [x] Return `FileResponse` with `media_type="text/css"`
- [x] Return 404 if file does not exist (no custom CSS – page still works)
- [x] Optional: add cache headers (e.g. `Cache-Control: max-age=3600`) or no-cache in DEBUG

### Phase 3: Template Integration

- [x] Add optional `<link rel="stylesheet" href="/custom.css">` in `create_html_template()`
- [x] Inject **after** the main `<style>` block so custom rules override defaults
- [x] Only include the link when the custom CSS file exists (check at render time or pass flag)
- [x] Fixed href `/custom.css` (env var only selects which file is served at that URL)

### Phase 4: Wiring & Logic

- [x] Add helper `get_custom_css_path() -> Path | None` that returns the resolved path if file exists and is safe
- [x] Pass `custom_css_url: str | None` (or similar) to `create_html_template()` – `None` when no custom CSS
- [x] Wire in both `serve_content` (doc pages) and `search_page` (search HTML response)
- [x] Ensure cached HTML is invalidated when custom CSS changes – custom CSS is in DOCS_ROOT, so docs hash may not include it; consider adding custom CSS mtime to cache key or excluding from HTML cache for simplicity (custom CSS is typically small; cache invalidation on doc change is acceptable)

### Phase 5: Tests & Polish

- [x] Unit test: custom CSS file exists → link present in HTML, href `/custom.css`
- [x] Unit test: custom CSS file missing → no link in HTML, page still renders
- [x] Unit test: `CUSTOM_CSS=theme.css` → serves `theme.css` from DOCS_ROOT at `/custom.css`
- [x] Unit test: `/custom.css` endpoint returns 200 with `Content-Type: text/css`
- [x] Unit test: path traversal attempt (e.g. `CUSTOM_CSS=../etc/passwd`) rejected
- [x] Run `uv run ruff check src/ tests/` and `uv run ruff format src/ tests/`
- [x] Run `uv run pytest tests/ -v` – all tests pass

### Phase 6: Documentation & Examples

**Configuration:**
- [x] Add `CUSTOM_CSS` to `docs/configuration.md` environment variables table
- [x] Brief "Custom CSS" section in configuration with file location, cascade order, `CUSTOM_CSS` usage

**Dedicated customization guide:**
- [x] Create `docs/features/customization.md` (or `docs/customization.md`)
- [x] Sections: Overview, Setup (CUSTOM_CSS, file placement), How it works (cascade, when loaded)
- [x] **CSS variables reference**: table of all `:root` variables with description and default value
- [x] Common customizations: accent color, font family, dark mode (link to night-mode example)
- [x] Add "Customization" under Features in `docs/sidebar.md` (link to `features/customization.html`)

**Examples to ship:**
- [x] `examples/custom.css` – basic overrides (accent color, font, maybe border radius)
- [x] `examples/night-mode.css` – full dark theme using `prefers-color-scheme: dark` or `:root` override
- [x] `examples/README.md` – brief note on copying examples to DOCS_ROOT and setting `CUSTOM_CSS`

---

## Success Criteria

- [x] Custom CSS file in `DOCS_ROOT` is loaded on every doc and search page
- [x] Custom CSS loads after default styles (correct cascade)
- [x] Configurable filename via `CUSTOM_CSS` env var
- [x] File served with `Content-Type: text/css`
- [x] CSS uses variables for surfaces/backgrounds (no hardcoded `white`) so themes override cleanly
- [x] Dedicated customization guide with CSS variables reference
- [x] Two examples shipped: `custom.css` (basic) and `night-mode.css` (dark theme)

---

## Impact Analysis

| Area | Impact |
|------|--------|
| **Config** | New `CUSTOM_CSS` env var (default: `custom.css`) |
| **Main** | New route for serving custom CSS; pass `custom_css_url` to template |
| **Templates** | CSS cleanup: new variables; `background: white` → `var(--color-bg-*)`; conditional `<link>` |
| **Helpers** | Optional: `get_custom_css_path()` or logic in main |
| **Tests** | New tests in `test_templates.py`, `test_main.py` (or `test_custom_css.py`) |
| **Docs** | `docs/configuration.md` + new `docs/features/customization.md` with variables reference |
| **Examples** | `examples/custom.css`, `examples/night-mode.css`, `examples/README.md` |
| **Caching** | No change; HTML cache fine; browser fetches CSS separately |

---

## Key Files to Modify

| File | Changes |
|------|---------|
| `src/docs_server/config.py` | Add `CUSTOM_CSS` setting |
| `src/docs_server/main.py` | Add `/custom.css` route; pass `custom_css_url` to template |
| `src/docs_server/templates.py` | CSS cleanup (new variables); conditional `<link>` for custom CSS |
| `src/docs_server/helpers.py` | Optional: `get_custom_css_path()` |
| `docs/configuration.md` | Document `CUSTOM_CSS`; brief custom CSS section |
| `docs/features/customization.md` | **New** – full customization guide + CSS variables reference |
| `docs/sidebar.md` | Add link to customization guide |
| `examples/custom.css` | Basic overrides (accent, font) |
| `examples/night-mode.css` | **New** – dark theme example |
| `examples/README.md` | **New** – how to use examples |
| `tests/test_*.py` | New tests |

