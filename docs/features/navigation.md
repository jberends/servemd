# Navigation Features

Create beautiful, hierarchical navigation with sidebar and topbar support.

## Sidebar Navigation

The sidebar provides the main documentation structure with collapsible groups.

### Structure Format

Create `sidebar.md` with this format:

```markdown
# Navigation

* [Home](index.md)
* [Getting Started](getting-started.md)
* [User Guide](user-guide.md)
  * [Installation](user-guide/install.md)
  * [Configuration](user-guide/config.md)
  * [Troubleshooting](user-guide/troubleshoot.md)
* [API Reference](api.md)
  * [REST API](api/rest.md)
  * [GraphQL](api/graphql.md)
```

### Rules

- **Top-level items**: `* [Title](link.md)` (no indentation)
- **Child items**: `  * [Title](link.md)` (2 spaces)
- **No nesting beyond 2 levels** (keep it simple)
- **Links auto-convert**: `.md` → `.html` in rendered output

### Types

The sidebar automatically detects two types:

1. **Standalone Links** - No children, clickable
2. **Groups** - Has children, header + children both clickable

---

## Topbar Navigation

The topbar provides quick access to key pages and external links.

### Structure Format

Create `topbar.md` with sections:

```markdown
# Top Bar

## left
* [📚 Docs](index.md)
* [🚀 Quick Start](quick-start.md)

## middle
* Version 2.0

## right
* [GitHub](https://github.com/project)
* [Discord](https://discord.gg/project)
```

### Sections

**Left Section** - Main navigation
```markdown
## left
* [Home](index.md)
* [Docs](docs.md)
```

**Middle Section** - Breadcrumbs, version info (optional)
```markdown
## middle
* v2.0.0
* [Changelog](changelog.md)
```

**Right Section** - External links, social
```markdown
## right
* [GitHub](https://github.com/project)
* [Twitter](https://twitter.com/project)
```

---

## Active State Highlighting

Both sidebar and topbar automatically highlight the current page.

**In sidebar:**
- Active page gets blue background
- Orange left border accent
- Bold text

**In topbar:**
- Active link gets blue background
- Subtle color change

---

## Logo Support

Add a logo to the topbar left section:

```markdown
## left
* {logo} | [Home](index.md)
* [Docs](docs.md)
```

Place your logo at `docs/assets/logo.svg`

---

## Examples

### Minimal Sidebar

```markdown
# Navigation

* [Home](index.md)
* [About](about.md)
* [Contact](contact.md)
```

### Complex Sidebar

```markdown
# Documentation

* [Home](index.md)
* [Quick Start](quick-start.md)
* [Features](features.md)
  * [Markdown Support](features/markdown.md)
  * [Navigation](features/navigation.md)
  * [LLMs.txt](features/llms-txt.md)
  * [Caching](features/caching.md)
* [Deployment](deployment.md)
  * [Docker](deployment/docker.md)
  * [Kubernetes](deployment/k8s.md)
  * [Cloud](deployment/cloud.md)
* [API Reference](api.md)
  * [Endpoints](api/endpoints.md)
  * [Authentication](api/auth.md)
  * [Rate Limiting](api/rate-limit.md)
* [Contributing](contributing.md)
  * [Code of Conduct](contributing/coc.md)
  * [Development Setup](contributing/setup.md)
  * [Pull Request Process](contributing/pr-process.md)
```

### Simple Topbar

```markdown
# Top Bar

## left
* [Docs](index.md)

## right
* [GitHub](https://github.com/project)
```

### Full Topbar

```markdown
# Top Navigation

## left
* {logo} | [Docs Home](index.md)
* [Quick Start](quick-start.md)
* [API](api.md)

## middle
* v2.1.0
* [Release Notes](changelog.md)

## right
* [GitHub](https://github.com/project)
* [Issues](https://github.com/project/issues)
* [Discord](https://discord.gg/project)
* [Twitter](https://twitter.com/project)
```

---

## Best Practices

### Sidebar

✅ **DO:**
- Keep hierarchy shallow (max 2 levels)
- Use clear, descriptive titles
- Group related content
- Order by user journey
- Limit to 10-15 top-level items

❌ **DON'T:**
- Over-nest (3+ levels)
- Use generic titles ("Misc", "Other")
- List every single page
- Alphabetize blindly
- Create huge lists

### Topbar

✅ **DO:**
- Keep it minimal (3-5 items per section)
- Put important links in left
- Use icons/emojis for visual interest
- Link to external resources in right
- Version info in middle

❌ **DON'T:**
- Overload with links
- Duplicate sidebar content
- Use only text (boring!)
- Hide important pages
- Ignore mobile users

---

## Responsive Behavior

### Desktop (>768px)
- Sidebar: Fixed left, always visible
- Topbar: Full width with all sections
- TOC: Fixed right (if content has headings)

### Tablet (768px-1200px)
- Sidebar: Fixed left, collapsible
- Topbar: Full width
- TOC: Hidden

### Mobile (<768px)
- Sidebar: Hidden by default, slide-in menu
- Topbar: Compact, hamburger menu
- TOC: Hidden

---

## Styling

### Colors

Navigation uses the theme colors:

```css
--accent-primary: #f26a28;  /* Accent color */
--color-primary: #3b82f6;   /* Active links */
--color-gray-700: #374151;  /* Normal text */
--color-gray-50: #f9fafb;   /* Hover background */
```

### Customization

To customize, modify `templates.py`:

```python
# Change accent color
.nav-group-header.active {
    border-left: 3px solid #your-color;
}

# Change hover color
.nav-group-link:hover {
    background-color: #your-color;
}
```

---

## Next Steps

- **[Markdown Features](markdown.md)** - Content capabilities
- **[LLMs.txt Support](llms-txt.md)** - AI integration
- **[Examples](../examples/basic.md)** - Real-world examples
