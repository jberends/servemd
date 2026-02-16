# Configuration

Configure the documentation server with environment variables and file structure.

## Environment Variables

### Core Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `DOCS_ROOT` | `./test_docs` or `/app/docs` | Root directory for markdown files |
| `CACHE_ROOT` | `./__cache__` or `/app/cache` | Cache directory for rendered HTML |
| `PORT` | `8080` | HTTP server port |
| `DEBUG` | `false` | Enable debug mode with auto-reload |
| `BASE_URL` | Auto-detected | Base URL for absolute links in llms.txt and Copy page AI links (ChatGPT, Claude) |
| `SERVEMD_BRANDING_ENABLED` | `true` | Show "Powered by servemd" footer. Set to `false` to disable for white-label or self-hosted deployments |
| `CUSTOM_CSS` | `custom.css` | Filename of custom CSS in DOCS_ROOT. Loaded on every page after default styles. See [Customization](features/customization.html) |

### MCP Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_ENABLED` | `true` | Enable/disable MCP endpoint |
| `MCP_RATE_LIMIT_REQUESTS` | `120` | Max requests per window per IP |
| `MCP_RATE_LIMIT_WINDOW` | `60` | Rate limit window in seconds |
| `MCP_MAX_SEARCH_RESULTS` | `10` | Default max search results |
| `MCP_SNIPPET_LENGTH` | `200` | Max characters for search snippets |

### Example Configurations

**Development:**
```bash
DOCS_ROOT=./docs \
DEBUG=true \
PORT=3000 \
uv run python -m docs_server
```

**Production:**
```bash
DOCS_ROOT=/var/www/docs \
CACHE_ROOT=/var/cache/docs \
BASE_URL=https://docs.example.com \
PORT=8080 \
uv run python -m docs_server
```

**Clear cache on startup:**
```bash
uv run python -m docs_server --clear-cache
```

**Docker:**
```bash
docker run \
  -e DOCS_ROOT=/app/docs \
  -e BASE_URL=https://docs.mysite.com \
  -e DEBUG=false \
  -p 8080:8080 \
  -v $(pwd)/docs:/app/docs \
  markdown-docs-server
```

**White-label (disable branding):**
```bash
SERVEMD_BRANDING_ENABLED=false uv run python -m docs_server
```
The "Powered by servemd" footer is shown by default. Disable it with `SERVEMD_BRANDING_ENABLED=false` for white-label or self-hosted deployments where you prefer no attribution.

### Custom CSS

Place a CSS file (e.g. `custom.css`) in `DOCS_ROOT`. It is served at `/custom.css` and loaded on every page **after** the default styles, so your rules override defaults. Use `CUSTOM_CSS=theme.css` to serve a different filename. See [Customization](features/customization.html) for CSS variables and examples.

---

## Required File Structure

Your `DOCS_ROOT` must contain three required files:

```
docs/
├── index.md       # Homepage (REQUIRED)
├── sidebar.md     # Sidebar navigation (REQUIRED)
└── topbar.md      # Top bar navigation (REQUIRED)
```

### index.md

Your documentation homepage:

```markdown
# Welcome to My Project

Quick introduction and getting started guide.

## Features
- Feature 1
- Feature 2

## Quick Start
[Get started here](quick-start.md)
```

### sidebar.md

Hierarchical navigation structure:

```markdown
# Navigation

* [Home](index.md)
* [Getting Started](getting-started.md)
* [User Guide](user-guide.md)
  * [Installation](user-guide/install.md)
  * [Configuration](user-guide/config.md)
* [API Reference](api.md)
  * [REST API](api/rest.md)
  * [GraphQL](api/graphql.md)
```

**Rules:**
- Top-level items: `* [Title](link.md)`
- Child items: `  * [Title](link.md)` (2 spaces indent)
- Sections automatically detected
- `.md` extensions converted to `.html` in rendered output

### topbar.md

Top bar with left/middle/right sections:

```markdown
# Top Bar Navigation

## left
* [📚 Docs](index.md)
* [🚀 Quick Start](quick-start.md)

## middle
* [v2.0.0](https://github.com/project/releases)

## right
* [GitHub](https://github.com/project)
* [Discord](https://discord.gg/project)
```

**Sections:**
- `## left` - Left side (logo, main links)
- `## middle` - Center (optional, breadcrumbs)
- `## right` - Right side (external links, social)

**Placeholders** (double braces so `{logo}` displays literally elsewhere):

| Tag | Syntax | Purpose |
|-----|--------|---------|
| `{{logo}}` | `* {{logo}} \| [Home](index.md)` | Logo + link in left section |
| `{{search}}` | `* {{search}}` or `* {{search:icon=...,mode=...,placeholder=...}}` | Search bar (MCP search when enabled) |

See [Navigation Features](features/navigation.md) for all `{{search}}` options: `icon` (lucide-search, lucide-x, custom SVG), `mode` (full, button, input), `placeholder`.

---

## Optional Files

### llms.txt

AI assistant index (see [LLMs.txt Guide](features/llms-txt.md)):

```markdown
# Project Documentation

[Homepage](index.md)
[Quick Start](quick-start.md)
[API Reference](api.md)
```

If not provided, auto-generated from `sidebar.md` + `index.md`.

### assets/

Place static assets in an `assets/` folder:

```
docs/
└── assets/
    ├── logo.svg
    ├── screenshot.png
    └── diagram.pdf
```

Reference in markdown:
```markdown
![Logo](assets/logo.svg)
[Download PDF](assets/diagram.pdf)
```

---

## Directory Structure

Organize content in subdirectories:

```
docs/
├── index.md
├── sidebar.md
├── topbar.md
├── getting-started.md
├── user-guide/
│   ├── installation.md
│   ├── configuration.md
│   └── troubleshooting.md
├── api/
│   ├── rest.md
│   ├── graphql.md
│   └── webhooks.md
├── deployment/
│   ├── docker.md
│   ├── kubernetes.md
│   └── cloud.md
└── assets/
    ├── logo.svg
    └── images/
        └── screenshot.png
```

**Best practices:**
- Group related content in folders
- Use clear, URL-friendly names
- Keep hierarchy shallow (2-3 levels max)
- Use descriptive filenames

---

## Markdown Configuration

The server uses these Markdown extensions:

### Enabled Extensions

| Extension | Purpose |
|-----------|---------|
| `codehilite` | Syntax highlighting for code blocks |
| `toc` | Automatic table of contents |
| `tables` | GitHub-style tables |
| `fenced_code` | ``` code blocks |
| `footnotes` | Footnote support[^1] |
| `attr_list` | HTML attributes in markdown |
| `def_list` | Definition lists |
| `abbr` | Abbreviations |
| `pymdownx.superfences` | Advanced code blocks |
| `pymdownx.tasklist` | - [ ] Task lists |
| `pymdownx.highlight` | Enhanced highlighting |
| `pymdownx.inlinehilite` | Inline code highlight |

[^1]: Like this footnote!

### Extension Configuration

Customize in `config.py`:

```python
markdown_extension_configs = {
    "codehilite": {
        "css_class": "highlight",
        "use_pygments": True,
    },
    "toc": {
        "permalink": True,
        "toc_depth": 3,
        "permalink_title": "🔗",
    },
    "pymdownx.tasklist": {
        "custom_checkbox": True,
    },
}
```

---

## Caching Strategy

### How It Works

1. **First request**: Markdown rendered to HTML, cached
2. **Subsequent requests**: Served from cache (instant)
3. **Server restart**: Cache cleared automatically

### Cache Location

```bash
# Default cache directory
CACHE_ROOT=./__cache__

# Custom cache directory
CACHE_ROOT=/tmp/docs-cache
```

### Cache Files

```
__cache__/
├── index.html               # Cached homepage
├── quick-start.html         # Cached page
├── user-guide/
│   └── installation.html
├── llms.txt                 # Cached llms.txt
└── llms-full.txt           # Cached full content
```

### Manual Cache Clear

```bash
# Remove cache directory
rm -rf __cache__

# Server will recreate on next request
```

---

## Security Settings

### Path Traversal Protection

Built-in security prevents directory traversal:

```python
# These are blocked:
/../../../../etc/passwd  ❌
/../secret.md            ❌
/../../config.yml        ❌

# These work:
/user-guide/install.md   ✅
/api/endpoints.md        ✅
```

### Safe Path Validation

All file paths are validated before serving:

```python
def is_safe_path(path: str, base_path: Path) -> bool:
    """Validate path is within allowed directory."""
    abs_base = base_path.resolve()
    abs_path = (base_path / path).resolve()
    return os.path.commonpath([abs_base, abs_path]) == str(abs_base)
```

---

## URL Routing

### HTML Mode

Serves rendered HTML:

```
http://localhost:8080/index.html          → Rendered
http://localhost:8080/api/endpoints.html  → Rendered
```

### Raw Markdown Mode

Serves original markdown:

```
http://localhost:8080/index.md            → Raw markdown
http://localhost:8080/api/endpoints.md    → Raw markdown
```

### Static Assets

Direct file serving:

```
http://localhost:8080/assets/logo.svg     → Static file
http://localhost:8080/assets/doc.pdf      → Static file
```

### Special Endpoints

```
http://localhost:8080/                    → Redirects to /index.html
http://localhost:8080/health              → Health check JSON
http://localhost:8080/llms.txt            → AI assistant index
http://localhost:8080/llms-full.txt       → Full documentation
```

---

## MCP Cache Considerations

### Kubernetes / k3s Deployments

When deploying to Kubernetes or k3s with MCP enabled:

**Cache Persistence:**
- MCP search index is stored in `CACHE_ROOT/mcp/`
- Each pod builds its own index on first startup (~200ms for typical docs)
- Cache persists across container restarts if volume is mounted
- Recommended: Use emptyDir volume for cache (ephemeral, fast)

```yaml
# Example volume mount for cache
volumes:
  - name: cache
    emptyDir: {}
volumeMounts:
  - name: cache
    mountPath: /app/cache
```

**Horizontal Scaling:**
- Each pod maintains its own independent search index
- Index rebuilds automatically when docs change (hash-based validation)
- No shared state required between pods
- Rate limiting is per-pod (each pod has 120 req/min limit)

**Startup Performance:**
- First startup: ~200ms to build index (100 docs)
- Subsequent startups: ~10ms to load from cache
- Health check passes immediately (MCP initialization is async)

**Environment Variables:**
```yaml
env:
  - name: MCP_ENABLED
    value: "true"
  - name: MCP_RATE_LIMIT_REQUESTS
    value: "120"
  - name: CACHE_ROOT
    value: "/app/cache"
```

## Production Checklist

Before deploying to production:

- [ ] Set `DEBUG=false`
- [ ] Configure `BASE_URL` for llms.txt
- [ ] Use proper `DOCS_ROOT` path
- [ ] Set up cache directory with write permissions
- [ ] Configure reverse proxy (nginx/caddy)
- [ ] Enable HTTPS
- [ ] Set proper PORT if needed
- [ ] Add health check monitoring
- [ ] Configure log aggregation
- [ ] Set up backup for docs
- [ ] For k8s/k3s: Configure emptyDir volume for cache
- [ ] For k8s/k3s: Consider per-pod rate limit scaling

---

## Troubleshooting

### Server won't start

Check port availability:
```bash
lsof -i :8080  # See what's using port 8080
```

### Files not found

Verify `DOCS_ROOT`:
```bash
echo $DOCS_ROOT
ls $DOCS_ROOT  # Should show index.md, sidebar.md, topbar.md
```

### Styling broken

Check for required files:
```bash
ls $DOCS_ROOT/sidebar.md
ls $DOCS_ROOT/topbar.md
```

### Cache issues

Clear and restart:
```bash
rm -rf __cache__
uv run python -m docs_server
```

---

## Advanced Configuration

### Custom Port

```bash
PORT=3000 uv run python -m docs_server
```

### Multiple Environments

```bash
# Development
cp .env.development .env
uv run python -m docs_server

# Production
cp .env.production .env
uv run python -m docs_server
```

### Environment File

Create `.env`:

```bash
DOCS_ROOT=./docs
CACHE_ROOT=./__cache__
PORT=8080
DEBUG=false
BASE_URL=https://docs.mysite.com
```

Load with:
```bash
source .env && uv run python -m docs_server
```

---

## Next Steps

- **[Deployment Guide](deployment/docker.md)** - Deploy to production
- **[API Reference](api/endpoints.md)** - HTTP endpoints
- **[Examples](examples/basic.md)** - Configuration examples
