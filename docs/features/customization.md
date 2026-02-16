# Customization

Customize the look and feel of your documentation site with custom CSS. Override colors, fonts, and layout without modifying servemd's core templates.

## Overview

Place a CSS file in your `DOCS_ROOT`. It is automatically loaded on every page **after** the default styles, so your rules override servemd's defaults. Use CSS variables for consistent theming.

## Setup

1. Create a CSS file in `DOCS_ROOT` (e.g. `custom.css`)
2. Optionally set `CUSTOM_CSS=theme.css` to use a different filename
3. Restart the server (or run with `DEBUG=true` for auto-reload)

The file is served at `/custom.css` regardless of the filename. The `CUSTOM_CSS` env var only selects which file in `DOCS_ROOT` is served.

## How It Works

- **Cascade**: Your CSS loads after the embedded default styles, so your rules take precedence
- **When loaded**: The `<link rel="stylesheet" href="/custom.css">` is injected in the `<head>` after the main `<style>` block
- **If missing**: If the file does not exist, no link is added and the page renders normally

## CSS Variables Reference

Override these `:root` variables in your custom CSS to theme the site:

| Variable | Default | Purpose |
|----------|---------|---------|
| `--accent-primary` | `#f26a28` | Accent color (links, active states, borders) |
| `--accent-black` | `#000000` | Heading color |
| `--color-primary` | `#3b82f6` | Primary UI (buttons, focus) |
| `--color-primary-50` | `#eff6ff` | Primary light background |
| `--color-primary-100` | `#dbeafe` | Primary hover/active background |
| `--color-primary-300` | `#93c5fd` | Primary border/focus |
| `--color-primary-600` | `#2563eb` | Primary text/buttons |
| `--color-neutral-50` | `#f9fafb` | Page background |
| `--color-gray-50` … `--color-gray-900` | Gray scale | Text, borders, surfaces |
| `--color-bg-sidebar` | `#ffffff` | Sidebar background |
| `--color-bg-topbar` | `#ffffff` | Topbar background |
| `--color-bg-content` | `#ffffff` | Main content area |
| `--color-bg-toc` | `transparent` | Table of contents sidebar |
| `--color-bg-branding` | `#ffffff` | Branding footer background |
| `--color-btn-text` | `#ffffff` | Button text (e.g. search) |
| `--color-search-highlight` | `#fefce8` | Search term highlight |
| `--color-code-bg` | `#f9fafb` | Code block background |
| `--color-code-border` | `#e5e7eb` | Code block border |

## Common Customizations

### Accent Color

```css
:root {
  --accent-primary: #10b981;
}
```

### Font Family

```css
body {
  font-family: "Inter", ui-sans-serif, system-ui, sans-serif;
}
```

### Dark Mode

Use the [night-mode.css](../examples/night-mode.css) example. It uses `prefers-color-scheme: dark` to switch automatically:

```css
@media (prefers-color-scheme: dark) {
  :root {
    --accent-primary: #f97316;
    --color-neutral-50: #111827;
    --color-bg-sidebar: #1f2937;
    --color-bg-topbar: #1f2937;
    --color-bg-content: #111827;
    /* ... more overrides */
  }
}
```

For always-dark (no system preference), override `:root` directly without the media query.

## Examples

Copy an example from the `examples/` directory to your `DOCS_ROOT` and set `CUSTOM_CSS` if needed:

- `examples/custom.css` – basic overrides (accent, font)
- `examples/night-mode.css` – dark theme

See `examples/README.md` in the repository for usage instructions.
