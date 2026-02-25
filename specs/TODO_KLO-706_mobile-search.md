# KLO-706 – Servemd search optimisation for mobile HTML

## Overview

On mobile viewports two things combine to break the layout (confirmed by screenshot `IMG_0757.png`):

1. **Topbar links wrap into two rows** — all `topbar-left`, `topbar-middle`, and `topbar-right` link items are visible in the topbar on mobile, causing them to wrap and take up extra vertical space.
2. **Search bar drops below the topbar** — the expanded search form (positioned `absolute; top: 100%`) overlaps the page content and pushes the `h1` title into a tiny left column barely 80 px wide.

**Decision:** On mobile (≤768 px):
- Hide **all** topbar links and the search bar from the topbar.
- Show only the logo/title area and a **hamburger icon** in the topbar.
- Tapping the hamburger opens a full-width dropdown panel containing all topbar links + the search bar.

---

## Phased Implementation Checklist

### Phase 1 – Foundation
- [x] Add a hamburger `<button>` element to the topbar HTML (visible only on mobile via CSS, hidden on desktop)
- [x] Add a mobile-menu overlay `<div id="mobile-menu">` just below the topbar (initially hidden)
- [x] Wire up basic open/close toggle in JavaScript

### Phase 2 – Content of the mobile menu
- [x] Render all topbar items (left, middle, right sections) inside the mobile menu in `_render_topbar_item()` / `create_html_template()`
- [x] Render the search bar inside the mobile menu (after the topbar link items)
- [x] Hide the existing search bar from the topbar on mobile (`.topbar-right { display: none }` on `@media max-width: 768px`)

### Phase 3 – CSS polish
- [x] Style the hamburger button (three-line icon, 44 px tap target)
- [x] Style the mobile menu panel: full-width, white background, border-bottom, proper padding
- [x] Animate the open/close transition (slide-down / fade via `max-height` + `opacity`)
- [x] Ensure z-index layers are correct (mobile menu z-index: 98, below topbar's 100)
- [x] Hide topbar-middle / topbar-right items on mobile when they are already shown in the mobile menu
- [ ] Test on narrow viewports (320 px, 375 px, 414 px) – manual browser test

### Phase 4 – Polish & testing
- [x] Close mobile menu when a navigation link is clicked (UX)
- [x] Close mobile menu when the user taps outside the menu
- [x] Close mobile menu on `Escape` key
- [x] Write / update tests in `tests/` for template output (presence of hamburger button, mobile-menu element, search inside menu)
- [x] Run `uv run pytest tests/ -v` – 266 tests passing
- [x] Run `uv run ruff check src/ tests/ --fix && uv run ruff format src/ tests/`
- [ ] Update `docs/` documentation if relevant

---

## Success Criteria

1. On a ≤768 px viewport the topbar shows only the logo/title area and a hamburger icon – no search bar or other links.
2. Tapping the hamburger opens a dropdown containing all topbar links AND the search bar.
3. On ≥769 px viewport the layout is completely unchanged (no regression).
4. The search bar functionality (form submit, keyboard shortcut `/`, `Escape`) works from the mobile menu.
5. All existing tests pass without modification.

---

## Impact Analysis

| Area | Impact |
|---|---|
| `src/docs_server/templates.py` | Primary file – HTML structure, CSS, JavaScript |
| `tests/test_templates.py` | New/updated tests for mobile menu elements |
| `docs/` | Minor update if configuration options change |

No new dependencies needed. Change is pure HTML/CSS/JS inside the single-file template.

---

## Key Files to Modify

- `src/docs_server/templates.py` – main template (HTML, CSS, JS all inline)
- `tests/test_templates.py` – template tests (add assertions for new elements)

---

## Appendix – Reference Code Patterns

### Current mobile search CSS (to be replaced)

```css
@media (max-width: 768px) {
    .search-form {
        position: absolute;
        top: 100%;
        right: 0;
        /* ... drops below topbar when expanded */
    }
}
```

### Hamburger button approach (proposed)

```html
<!-- In topbar HTML (mobile only) -->
<button class="mobile-menu-toggle" aria-label="Open menu" aria-expanded="false" aria-controls="mobile-menu">
  <span class="hamburger-bar"></span>
  <span class="hamburger-bar"></span>
  <span class="hamburger-bar"></span>
</button>

<!-- Mobile menu panel (placed after topbar in DOM) -->
<div id="mobile-menu" class="mobile-menu" hidden>
  <!-- topbar links rendered here -->
  <!-- search bar rendered here -->
</div>
```

### JS toggle snippet (proposed)

```javascript
(function() {
    var btn = document.querySelector('.mobile-menu-toggle');
    var menu = document.getElementById('mobile-menu');
    if (!btn || !menu) return;

    btn.addEventListener('click', function() {
        var open = menu.hidden === false;
        menu.hidden = open;
        btn.setAttribute('aria-expanded', String(!open));
    });

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && !menu.hidden) {
            menu.hidden = true;
            btn.setAttribute('aria-expanded', 'false');
            btn.focus();
        }
    });
})();
```
