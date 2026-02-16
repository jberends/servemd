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

**Optional enhancements (out of scope for initial implementation):**
- Support multiple CSS files
- Support inline custom CSS via config (for simple overrides)
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

### Phase 1: Configuration

- [ ] Add `CUSTOM_CSS` to `config.py` (default: `custom.css`)
- [ ] Parse `os.getenv("CUSTOM_CSS", "custom.css")` – filename only, no path
- [ ] Add helper to resolve custom CSS path: `settings.DOCS_ROOT / settings.CUSTOM_CSS`
- [ ] Validate filename: must end with `.css` and not contain path separators (security)

### Phase 2: Endpoint & Serving

- [ ] Add route `GET /custom.css` (or dynamic path based on config) that serves the file from `DOCS_ROOT`
- [ ] Use `get_file_path()` or equivalent to resolve path with `is_safe_path()` validation
- [ ] Return `FileResponse` with `media_type="text/css"`
- [ ] Return 404 if file does not exist (no custom CSS – page still works)
- [ ] Optional: add cache headers (e.g. `Cache-Control: max-age=3600`) or no-cache in DEBUG

### Phase 3: Template Integration

- [ ] Add optional `<link rel="stylesheet" href="/custom.css">` in `create_html_template()`
- [ ] Inject **after** the main `<style>` block so custom rules override defaults
- [ ] Only include the link when the custom CSS file exists (check at render time or pass flag)
- [ ] Use configurable href (e.g. `/custom.css` or `/{CUSTOM_CSS}`) so it matches the served path

### Phase 4: Wiring & Logic

- [ ] Add helper `get_custom_css_path() -> Path | None` that returns the resolved path if file exists and is safe
- [ ] Pass `custom_css_url: str | None` (or similar) to `create_html_template()` – `None` when no custom CSS
- [ ] Wire in both `serve_content` (doc pages) and `search_page` (search HTML response)
- [ ] Ensure cached HTML is invalidated when custom CSS changes – custom CSS is in DOCS_ROOT, so docs hash may not include it; consider adding custom CSS mtime to cache key or excluding from HTML cache for simplicity (custom CSS is typically small; cache invalidation on doc change is acceptable)

### Phase 5: Tests & Polish

- [ ] Unit test: custom CSS file exists → link present in HTML, correct href
- [ ] Unit test: custom CSS file missing → no link in HTML, page still renders
- [ ] Unit test: `CUSTOM_CSS=theme.css` → link href is `/theme.css`
- [ ] Unit test: `/custom.css` endpoint returns 200 with `Content-Type: text/css`
- [ ] Unit test: path traversal attempt (e.g. `CUSTOM_CSS=../etc/passwd`) rejected
- [ ] Run `uv run ruff check src/ tests/` and `uv run ruff format src/ tests/`
- [ ] Run `uv run pytest tests/ -v` – all tests pass

### Phase 6: Documentation & Examples

- [ ] Add `CUSTOM_CSS` to `docs/configuration.md` environment variables table
- [ ] Document: file location, cascade order, use cases (branding, theming)
- [ ] Add example `custom.css` in `examples/custom.css` or `docs/custom.css` with sample overrides (e.g. accent color, font)

---

## Success Criteria

- [ ] Custom CSS file in `DOCS_ROOT` is loaded on every doc and search page
- [ ] Custom CSS loads after default styles (correct cascade)
- [ ] Configurable filename via `CUSTOM_CSS` env var
- [ ] File served with `Content-Type: text/css`
- [ ] Documented in configuration guide
- [ ] Example `custom.css` provided

---

## Impact Analysis

| Area | Impact |
|------|--------|
| **Config** | New `CUSTOM_CSS` env var (default: `custom.css`) |
| **Main** | New route for serving custom CSS; pass `custom_css_url` to template |
| **Templates** | Conditional `<link>` after main styles |
| **Helpers** | Optional: `get_custom_css_path()` or logic in main |
| **Tests** | New tests in `test_templates.py`, `test_main.py` (or `test_custom_css.py`) |
| **Docs** | Update `docs/configuration.md`; add `examples/custom.css` |
| **Caching** | Consider: custom CSS change should invalidate HTML cache; docs hash does not include `.css` – may need to extend hash or accept that custom CSS changes require cache clear |

---

## Key Files to Modify

| File | Changes |
|------|---------|
| `src/docs_server/config.py` | Add `CUSTOM_CSS` setting |
| `src/docs_server/main.py` | Add `/custom.css` route (or dynamic); pass `custom_css_url` to template |
| `src/docs_server/templates.py` | Add conditional `<link>` for custom CSS after main `<style>` |
| `src/docs_server/helpers.py` | Optional: `get_custom_css_path()` |
| `docs/configuration.md` | Document `CUSTOM_CSS` |
| `examples/custom.css` | Example file |
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
