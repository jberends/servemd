# TODO: "Powered by servemd" Branding Option

**Project:** ServeMD
**Feature:** Configurable branding attribution
**Branch:** `7-powered-by-servemd-branding`
**Reference:** [GitHub Issue #7](https://github.com/jberends/servemd/issues/7)
**Status:** Implemented
**Last Updated:** 2026-02-16

---

## Task Analysis

**Summary:** Add a configurable way to show that the documentation site is served with servemd. This gives servemd visibility and credit while allowing site owners to control placement and visibility for self-hosted/white-label deployments.

**Acceptance criteria (from Issue #7):**
- Branding visible by default (or configurable default)
- Can be disabled via `SERVEMD_BRANDING=false` (or equivalent)
- Link to servemd repo or docs
- Does not dominate the layout
- Documented in configuration guide

**Dependencies:** None. Standalone feature.

**Ambiguities:**
- Placement: Issue suggests footer or corner badge. Footer is simpler and more conventional for attribution.
- Link target: GitHub repo (https://github.com/jberends/servemd) or docs? Repo is canonical; docs may be served by servemd itself.

---

## Overview

Add a subtle "Powered by servemd" attribution that appears by default in the footer of every page. Site owners can disable it via `SERVEMD_BRANDING=false` for white-label deployments. The branding uses minimal styling consistent with the existing Nuxt UI-inspired design.

---

## Phased Implementation Checklist

### Phase 1: Configuration

- [x] Add `SERVEMD_BRANDING` to `config.py` (default: `true`)
- [x] Parse `os.getenv("SERVEMD_BRANDING", "true").lower() == "true"`
- [x] Expose via `settings.SERVEMD_BRANDING` for use in templates

### Phase 2: Template Integration

- [x] Add `show_branding: bool` parameter to `create_html_template()`
- [x] When `show_branding=True`: render footer HTML with "Powered by servemd" link
- [x] Footer placement: inside `main-content` or as sibling after it; spans full width of content area
- [x] Link target: `https://github.com/jberends/servemd` (repo is canonical)
- [x] Use `target="_blank" rel="noopener noreferrer"` for external link

### Phase 3: Styling

- [x] Add `.servemd-branding` (or `.branding-footer`) CSS class
- [x] Minimal styling: small font (0.75rem–0.875rem), muted color (gray-500), no background
- [x] Center or right-align; padding consistent with content area
- [x] Ensure it does not dominate layout; subtle and unobtrusive

### Phase 4: Wiring & Tests

- [x] Pass `show_branding=settings.SERVEMD_BRANDING` in both `create_html_template` call sites (`main.py`: doc pages and search page)
- [x] Unit test: `SERVEMD_BRANDING=true` → footer present in HTML
- [x] Unit test: `SERVEMD_BRANDING=false` → footer absent
- [x] Test: footer contains link to servemd repo
- [x] Run `uv run ruff check src/ tests/` and `uv run ruff format src/ tests/`
- [x] Run `uv run pytest tests/ -v` – all tests pass

### Phase 5: Documentation

- [x] Add `SERVEMD_BRANDING` to `docs/configuration.md` environment variables table
- [x] Document opt-out use case (white-label, self-hosted)
- [ ] Optional: mention in README or deployment docs

---

## Success Criteria

- [x] Branding visible by default on all doc and search pages
- [x] `SERVEMD_BRANDING=false` hides branding completely
- [x] "Powered by servemd" links to https://github.com/jberends/servemd
- [x] Styling is minimal and non-intrusive
- [x] Documented in configuration guide

---

## Impact Analysis

| Area | Impact |
|------|--------|
| **Config** | New `SERVEMD_BRANDING` env var (default: true) |
| **Templates** | New footer block in `create_html_template`; new `show_branding` param; new CSS |
| **Main** | Pass `show_branding=settings.SERVEMD_BRANDING` to both template calls |
| **Tests** | New tests in `test_templates.py` for branding presence/absence |
| **Docs** | Update `docs/configuration.md` |

---

## Key Files to Modify

| File | Changes |
|------|---------|
| `src/docs_server/config.py` | Add `SERVEMD_BRANDING` setting |
| `src/docs_server/templates.py` | Add `show_branding` param; render footer block; add CSS |
| `src/docs_server/main.py` | Pass `show_branding=settings.SERVEMD_BRANDING` to `create_html_template` |
| `docs/configuration.md` | Document `SERVEMD_BRANDING` |
| `tests/test_templates.py` | Tests for branding on/off |

---

## Appendix: Code Examples

### Config pattern (from config.py)

```python
# MCP Configuration
self.MCP_ENABLED = os.getenv("MCP_ENABLED", "true").lower() == "true"
# ...
# Branding
self.SERVEMD_BRANDING = os.getenv("SERVEMD_BRANDING", "true").lower() == "true"
```

### Template call pattern (from main.py)

```python
full_html = create_html_template(
    html_content,
    title,
    current_path,
    navigation,
    topbar_sections,
    toc_items,
    show_search=settings.MCP_ENABLED,
    show_branding=settings.SERVEMD_BRANDING,  # NEW
)
```

### Footer HTML (conceptual)

```html
<footer class="servemd-branding">
  <a href="https://github.com/jberends/servemd" target="_blank" rel="noopener noreferrer">
    Powered by servemd
  </a>
</footer>
```

### CSS (minimal)

```css
.servemd-branding {
  font-size: 0.8125rem;
  color: var(--color-gray-500);
  text-align: center;
  padding: 1rem 0;
  margin-top: 2rem;
  border-top: 1px solid var(--color-gray-200);
}
.servemd-branding a {
  color: var(--color-gray-500);
  text-decoration: none;
}
.servemd-branding a:hover {
  color: var(--color-gray-700);
  text-decoration: underline;
}
```

### Test pattern (from test_templates.py)

```python
def test_create_html_template_branding_when_enabled():
    from docs_server.templates import create_html_template
    result = create_html_template("<p>Content</p>", show_branding=True)
    assert "Powered by servemd" in result
    assert "github.com/jberends/servemd" in result

def test_create_html_template_no_branding_when_disabled():
    from docs_server.templates import create_html_template
    result = create_html_template("<p>Content</p>", show_branding=False)
    assert "Powered by servemd" not in result
```
