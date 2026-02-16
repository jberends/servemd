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

- [ ] Add route `GET /custom.css` that serves the file from `DOCS_ROOT` (filename from `CUSTOM_CSS`)
- [ ] Use `get_file_path()` or equivalent to resolve path with `is_safe_path()` validation
- [ ] Return `FileResponse` with `media_type="text/css"`
- [ ] Return 404 if file does not exist (no custom CSS – page still works)
- [ ] Optional: add cache headers (e.g. `Cache-Control: max-age=3600`) or no-cache in DEBUG

### Phase 3: Template Integration

- [ ] Add optional `<link rel="stylesheet" href="/custom.css">` in `create_html_template()`
- [ ] Inject **after** the main `<style>` block so custom rules override defaults
- [ ] Only include the link when the custom CSS file exists (check at render time or pass flag)
- [ ] Fixed href `/custom.css` (env var only selects which file is served at that URL)

### Phase 4: Wiring & Logic

- [ ] Add helper `get_custom_css_path() -> Path | None` that returns the resolved path if file exists and is safe
- [ ] Pass `custom_css_url: str | None` (or similar) to `create_html_template()` – `None` when no custom CSS
- [ ] Wire in both `serve_content` (doc pages) and `search_page` (search HTML response)
- [ ] Ensure cached HTML is invalidated when custom CSS changes – custom CSS is in DOCS_ROOT, so docs hash may not include it; consider adding custom CSS mtime to cache key or excluding from HTML cache for simplicity (custom CSS is typically small; cache invalidation on doc change is acceptable)

### Phase 5: Tests & Polish

- [ ] Unit test: custom CSS file exists → link present in HTML, href `/custom.css`
- [ ] Unit test: custom CSS file missing → no link in HTML, page still renders
- [ ] Unit test: `CUSTOM_CSS=theme.css` → serves `theme.css` from DOCS_ROOT at `/custom.css`
- [ ] Unit test: `/custom.css` endpoint returns 200 with `Content-Type: text/css`
- [ ] Unit test: path traversal attempt (e.g. `CUSTOM_CSS=../etc/passwd`) rejected
- [ ] Run `uv run ruff check src/ tests/` and `uv run ruff format src/ tests/`
- [ ] Run `uv run pytest tests/ -v` – all tests pass

### Phase 6: Documentation & Examples

**Configuration:**
- [ ] Add `CUSTOM_CSS` to `docs/configuration.md` environment variables table
- [ ] Brief "Custom CSS" section in configuration with file location, cascade order, `CUSTOM_CSS` usage

**Dedicated customization guide:**
- [ ] Create `docs/features/customization.md` (or `docs/customization.md`)
- [ ] Sections: Overview, Setup (CUSTOM_CSS, file placement), How it works (cascade, when loaded)
- [ ] **CSS variables reference**: table of all `:root` variables with description and default value
- [ ] Common customizations: accent color, font family, dark mode (link to night-mode example)
- [ ] Add "Customization" under Features in `docs/sidebar.md` (link to `features/customization.html`)

**Examples to ship:**
- [ ] `examples/custom.css` – basic overrides (accent color, font, maybe border radius)
- [ ] `examples/night-mode.css` – full dark theme using `prefers-color-scheme: dark` or `:root` override
- [ ] `examples/README.md` – brief note on copying examples to DOCS_ROOT and setting `CUSTOM_CSS`

---

## Success Criteria

- [ ] Custom CSS file in `DOCS_ROOT` is loaded on every doc and search page
- [ ] Custom CSS loads after default styles (correct cascade)
- [ ] Configurable filename via `CUSTOM_CSS` env var
- [ ] File served with `Content-Type: text/css`
- [ ] CSS uses variables for surfaces/backgrounds (no hardcoded `white`) so themes override cleanly
- [ ] Dedicated customization guide with CSS variables reference
- [ ] Two examples shipped: `custom.css` (basic) and `night-mode.css` (dark theme)

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

---

## Appendix: Code Examples & References

### A. Config pattern (from `config.py`)

```python
# Branding (existing)
self.SERVEMD_BRANDING_ENABLED = os.getenv("SERVEMD_BRANDING_ENABLED", "true").lower() == "true"

# Custom CSS (new)
custom_css = os.getenv("CUSTOM_CSS", "custom.css").strip()
if custom_css and custom_css.endswith(".css") and "/" not in custom_css and "\\" not in custom_css:
    self.CUSTOM_CSS = custom_css
else:
    self.CUSTOM_CSS = "custom.css"
```

### B. Static file serving (from `main.py`)

```python
# Existing: assets mount
assets_path = settings.DOCS_ROOT / "assets"
if assets_path.exists():
    app.mount("/assets", StaticFiles(directory=str(assets_path)), name="assets")

# Existing: generic static assets via get_file_path
# media_types = { ".png": "image/png", ... }
# return FileResponse(path=str(file_path), media_type=media_type, filename=file_path.name)
```

### C. Template structure (from `templates.py`)

The main `<style>` block ends around line 866, followed by `</head>`. Custom CSS link should go between `</style>` and `</head>`:

```html
    </style>
    {custom_css_link}
</head>
```

Where `custom_css_link` is either empty or:
```html
<link rel="stylesheet" href="/custom.css">
```

### D. Path validation (from `helpers.py`)

```python
def is_safe_path(path: str, base_path: Path) -> bool:
    """Validate that the requested path is within the allowed directory boundaries."""
    try:
        abs_base = base_path.resolve()
        abs_path = (base_path / path).resolve()
        return os.path.commonpath([abs_base, abs_path]) == str(abs_base)
    except (ValueError, OSError):
        return False
```

### E. Cache consideration

The docs hash in `config.py` includes only `.md` files. Custom CSS (`.css`) changes do not invalidate the HTML cache. Options:
1. **Simple:** Document that users should run `--clear-cache` after changing custom CSS, or rely on DEBUG mode (which always invalidates).
2. **Extended:** Include `custom.css` (or `CUSTOM_CSS` filename) mtime in cache key for HTML. More complex.
3. **Pragmatic:** Custom CSS is loaded via `<link href="/custom.css">` – the browser fetches it separately. Cached HTML will include the link; the CSS file itself is not cached by our HTML cache. So when the user updates `custom.css`, the next request to `/custom.css` gets the new file. The HTML cache is fine as-is. No change needed.

### F. Route ordering

FastAPI matches routes in order. The catch-all `/{path:path}` would match `custom.css`. We need to register `GET /custom.css` (or a dynamic path) **before** the catch-all. Check `main.py` route order: `/health`, `/mcp`, `/llms.txt`, `/llms-full.txt`, `/`, `/search`, `/{path:path}`. Add `/custom.css` before `/{path:path}`. If we use a configurable path, we need a route like `GET /{css_filename}` that only matches when it equals `settings.CUSTOM_CSS` – or we keep it simple and always use `/custom.css` as the URL, and the env var only changes which file we serve from disk. That way the route is fixed: `GET /custom.css` serves `DOCS_ROOT / settings.CUSTOM_CSS`.

Actually, re-reading the issue: "CUSTOM_CSS=custom.css or custom.css as default when present". So the env var is the filename. The URL could be the same as the filename: `/custom.css` or `/theme.css`. So we need a dynamic route. Options:
- `@app.get("/{css_file:path}")` with a check for `css_file == settings.CUSTOM_CSS` – but that would conflict with the catch-all.
- Simpler: always serve custom CSS at a fixed URL like `/custom.css`. The env var `CUSTOM_CSS` only specifies which *file* in DOCS_ROOT to serve. So the URL is always `/custom.css` regardless of the actual filename. That's a bit odd – if user sets `CUSTOM_CSS=theme.css`, the file is `theme.css` but the URL is `/custom.css`. Alternatively, the URL could match the filename: `/custom.css` when `CUSTOM_CSS=custom.css`, and `/theme.css` when `CUSTOM_CSS=theme.css`. That requires a dynamic route. We can add `@app.get(f"/{settings.CUSTOM_CSS}")` – but settings are loaded at import time, so that should work. We need to be careful: if `CUSTOM_CSS` is `theme.css`, the route would be `@app.get("/theme.css")`. But `theme.css` could conflict with a doc at `theme.css` (raw file serving). Looking at the catch-all: `.md` and `.html` are handled specially; other files are served as static. So `theme.css` would currently be served as a static file from DOCS_ROOT if it exists. So we're good – we could either:
1. Add an explicit route for `/{CUSTOM_CSS}` that runs first and serves with `text/css`. If the file doesn't exist, we 404. The catch-all would not be reached for that path if we register our route first.
2. Or use a reserved path like `/custom.css` always, and the env var only picks the file. Simpler.

**Recommendation:** Use a **fixed URL** `/custom.css` for the custom stylesheet. The `CUSTOM_CSS` env var specifies which *file* in DOCS_ROOT to serve at that URL (e.g. `CUSTOM_CSS=theme.css` → serve `docs/theme.css` at `/custom.css`). This avoids route conflicts and keeps the template simple. Register the route before the catch-all `/{path:path}`.

### G. CSS Variables (after Phase 0 cleanup)

| Variable | Default | Purpose |
|----------|---------|---------|
| `--accent-primary` | `#f26a28` | Accent (links, active states, borders) |
| `--accent-black` | `#000000` | Heading color |
| `--color-primary` | `#3b82f6` | Primary UI (buttons, focus) |
| `--color-primary-50` … `--color-primary-600` | (blue scale) | Primary variants |
| `--color-neutral-50` | `#f9fafb` | Page background |
| `--color-gray-50` … `--color-gray-900` | (gray scale) | Text, borders, surfaces |
| `--color-bg-sidebar` | `white` (→ variable) | Sidebar background |
| `--color-bg-topbar` | `white` | Topbar background |
| `--color-bg-content` | `white` | Main content area |
| `--color-bg-toc` | (sticky, inherits) | TOC sidebar |
| `--color-bg-branding` | `white` | Branding footer |
| `--color-btn-text` | `white` | Button text (e.g. search) |
| `--color-search-highlight` | `#fefce8` | Search term highlight |

### H. Night-mode example sketch

```css
/* examples/night-mode.css – Dark theme for servemd */
@media (prefers-color-scheme: dark) {
  :root {
    --accent-primary: #f97316;
    --accent-black: #f9fafb;
    --color-primary: #60a5fa;
    --color-primary-50: #1e3a8a;
    --color-primary-100: #1e40af;
    /* ... invert gray scale ... */
    --color-neutral-50: #111827;
    --color-gray-50: #1f2937;
    --color-gray-900: #f9fafb;
    --color-bg-sidebar: #1f2937;
    --color-bg-topbar: #1f2937;
    --color-bg-content: #111827;
    --color-search-highlight: #422006;
  }
}
```

Or use `:root` override without media query for always-dark. Document both approaches in the guide.
