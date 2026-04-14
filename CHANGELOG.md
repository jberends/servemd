# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## v1.2.0 (2026-04-14)

### Added

- :electric_plug: **MCP Installation UX** — New `/about_servemd` about page with per-client connection instructions and version info:
  - `GET /about_servemd` renders in the full three-column layout (sidebar + content + TOC); excluded from the Whoosh search index automatically (not under `DOCS_ROOT`).
  - **Claude (claude.ai)** — step-by-step guide for the native Connectors flow (Customize → Connectors → +); covers Free, Pro, Max, Team & Enterprise plans including the Owner-first Team/Enterprise flow.
  - **ChatGPT** — instructions for Developer Mode connector (Plus/Team/Enterprise/Edu); URL shown with required trailing slash; per-chat activation note included.
  - **Mistral Le Chat** — custom MCP connector guide (Intelligence → Connectors → Custom MCP Connector); Admin-role requirement noted.
  - **Add to Cursor** deep link via `cursor://` scheme: uses `mcp-remote` as a stdio bridge (required workaround for broken HTTP transport in Cursor v3.0.9+).
  - **Add to VS Code** deep link via `vscode://` scheme: uses VS Code's native HTTP MCP transport.
  - All URLs derived from the deployment's actual base URL (`BASE_URL` env var or request origin) — zero hardcoded placeholders; ChatGPT URL automatically gets trailing slash.
  - Shared public-internet reachability note with ngrok suggestion for local development.
  - "Powered by servemd" sidebar footer now links to `/about_servemd`; GitHub link moved to the about page only.
  - New `docs/features/mcp-setup.md` step-by-step guide for AI clients, Cursor, VS Code, and manual JSON fallback.
  - Updated `docs/features/mcp.md` integration examples with Cursor mcp-remote config and link to `/about_servemd`.
- :page_facing_up: **HTML file embedding** - Raw `.html` files in `DOCS_ROOT` are now served inside the standard doc layout (sidebar, topbar) via a same-origin iframe:
  - `GET /foo.html` falls back to `foo.html` when no `foo.md` exists — markdown always wins when both are present
  - New `GET /raw/{path}` endpoint serves any file from `DOCS_ROOT` as-is (no template wrapping), used as the iframe `src` to avoid recursive rendering
  - Iframe fills the content pane (`min-height: 80vh`); scripts and styles in the HTML file run in full isolation
  - Path traversal protection inherited from existing `get_file_path()` validation; iframe attributes HTML-escaped and URL-encoded
- :bookmark_tabs: **Favicon** - Inline SVG favicon using the Tabler `book` icon in accent orange (`#f26a28`); embedded as a data URI so it works offline with no external requests.

### Changed

- Improved search for identifiers in headings: The search index tokenizer uses now a single general rule: any heading token whose segments (split by `-`, `_`, `+`, `/`, `.`) contain at least one letter **and** at least one digit is extracted as an identifier. Covers `UC2-002`, `KECMAP2-1234`, `G002`, `G-02`, `#2.02`, `23/24`, `2.0.2`, `2.0.2.1`, lower-case variants, digit-first forms (`3gpp-spec`), and any future naming convention without needing per-pattern branches. Ensures better search results for identifiers in headings.
- :mag: **MCP search: structured identifier lookup** - Searching for identifiers like `UC-2-002`, `AUTH-01`, or `G-02` now reliably returns the defining document as the first result. Three root causes were addressed:
  - `extract_headings()` now captures h2–h4 (was h2-only), so UC entry headings at h3 level land in the boosted `headings` field.
  - New `identifiers` field (field\_boost=5.0) extracts structured IDs from heading lines verbatim using a whitespace-only tokenizer, preserving `UC-2-002` as a single exact token.
  - Custom prose analyzer replaces the bare `StemmingAnalyzer`: extended tokenizer emits hyphenated tokens as single units, and `StopFilter(minsize=1)` keeps single-digit tokens so `UC-3-002` and `UC-4-002` remain distinguishable.
  - New `path_text` field tokenises the file path on word boundaries, enabling filename-fragment searches (e.g. `AUTH_01` finds `screens/AUTH_01_login_screen.md`).
  - `MultifieldParser` now includes `identifiers` and `path_text` with per-field boosts (`identifiers: 5.0`, `title: 2.0`, `headings: 1.5`).

### v1.1.0 (2026-02-25)

### Changed

- :sparkles: **Mobile menu** - Hamburger menu for mobile navigation:
  - `<button id="mobile-menu-toggle">☰</button>` in topbar
  - `#mobile-menu` overlay panel with full-width, white background, border-bottom, proper padding
  - Animate open/close transition (slide-down / fade via `max-height` + `opacity`)
  - Close mobile menu when a navigation link is clicked (UX)
  - Close mobile menu when the user taps outside the menu
  - Close mobile menu on `Escape` key

## v1.0.0 (2026-02-16)

### Added

- :sparkles: **Custom CSS injection** - Override styles without forking templates:
  - `CUSTOM_CSS` env var (default: `custom.css`); file served from DOCS_ROOT
  - `GET /custom.css` endpoint with cache headers (no-cache in DEBUG, max-age=3600 otherwise)
  - Link injected after built-in styles when file exists
  - Examples: `examples/custom.css`, `examples/night-mode.css`
- :sparkles: **Copy page dropdown** - Page actions next to document title (doc pages only):
  - Copy Markdown link `[Title](url)` to clipboard
  - View as Markdown (raw .md URL)
  - Open in Mistral Le Chat, ChatGPT, Claude (pre-filled prompt to read the page)
  - Nuxt UI-style dropdown with icons
- :sparkles: **Code block copy button** - "Copy" button on syntax-highlighted code blocks; shows "Copied!" feedback
- :sparkles: **"Powered by servemd" branding** - Configurable attribution in sidebar footer:
  - `SERVEMD_BRANDING_ENABLED` env var (default: `true`); set to `false` for white-label deployments
  - Sticky at bottom of sidebar with link to GitHub repo
  - Hidden on mobile when sidebar is collapsed
- :sparkles: **In-page search** - Human-readable search experience when MCP is enabled:
  - Search bar in topbar (configurable via `{{search}}` placeholder in `topbar.md`)
  - Search page at `/search?q=...` with live results as you type (debounced, min 3 characters)
  - Keyboard shortcut `/` to focus search bar; `Escape` to blur
  - Search terms highlighted in results (pale yellow marker)
  - Configurable icon, mode (`full`, `button`, `input`), and placeholder via `{{search:icon=...,mode=...,placeholder=...}}`
  - JSON endpoint (`/search?format=json`) for client-side live search
- :wrench: **`--clear-cache` CLI flag** - Clear the cache directory on startup before serving
- :rocket: **Hetzner bare server deployment** - Minimal deployment guide for Debian 13 VPS on Hetzner (`deployment/hetzner/`). Includes Docker Compose stack with servemd + Caddy reverse proxy, automatic HTTPS via Let's Encrypt, and hourly auto-updates via cron. See `deployment/hetzner/README.md`.

### Changed

- :art: **CSS variables for theming** - New variables for easier customization: `--color-bg-sidebar`, `--color-bg-topbar`, `--color-bg-content`, `--color-bg-toc`, `--color-bg-branding`, `--color-btn-text`, `--color-search-highlight`, `--color-code-bg`, `--color-code-border`. Replaced hardcoded `white` and `#fefce8` with variables.
- :lipstick: **Code block styling** - Nuxt-like appearance: no per-line borders, smoother padding, distinct inline vs block code styles.
- :art: **Reduced padding/margins** - Tighter spacing throughout: sidebar, main content, typography (h1, h2, h3, p, lists, code blocks, tables, blockquotes), and "Powered by" area. Topbar unchanged.
- :lock: **Docker container security hardening** - Significant security improvements to the Docker image:
  - Switched base image from Debian Trixie (testing) to Debian Bookworm (stable), reducing CVEs by ~40–57%
  - Container now runs as non-root `servemd` user (UID 1000) instead of root
  - Applies security patches during build (`apt-get upgrade`)
  - Minimal dependencies with `--no-install-recommends`
  - Proper file ownership for all application files
  - See `DOCKER_SECURITY.md` and `SECURITY_CHANGES.md` for details

### Fixed

- :lock: **ReDoS in page actions template** - Replaced regex `(<h1[^>]*>)(.*?)(</h1>)` with string-based search to avoid polynomial backtracking on user-controlled content (CodeQL py/polynomial-redos).
- :lock: **Log injection in MCP search** - Sanitized user-provided search query and exception messages before logging to prevent log injection (CodeQL High).
- :bug: **Sidebar and topbar link resolution** - Links in `sidebar.md` and `topbar.md` are now normalized to root-relative paths (`/dir/page.html`) during parsing. Previously, relative links like `deployment/docker.html` were resolved by the browser relative to the current page URL, causing broken links (e.g. `/dir/dir/page.html`) when viewing pages in subdirectories. Content markdown links remain relative to the current file and work correctly.

## v0.2.0 (2026-02-02)

### Added

#### Docker & CI/CD
- **Docker Hub & GHCR Publishing** - Automated Docker image publishing workflow
  - Publishes to both Docker Hub and GitHub Container Registry on release
  - Multi-platform build support (linux/amd64, linux/arm64)
  - Automatic Docker Hub description updates from README
  - Container images available as `jberends/servemd:latest` and `ghcr.io/jberends/servemd:latest`
- Comprehensive Docker documentation (`DOCKER_README.md`)
- Docker build and push scripts (`docker-build-push.sh`)
- Custom Dockerfile examples for user documentation
- Enhanced Dockerfile with build optimizations

#### Documentation & Examples
- **Search alternatives guide** - Documentation on different search implementation options
- **Release workflow documentation** - Complete guide for maintainers
- Dependabot configuration for automated dependency updates
- Updated deployment examples with MCP support
- Enhanced Docker Compose examples
- Improved Kubernetes deployment examples
- Custom Dockerfile examples for users

### Changed

#### Dependencies
- **Migrated to Whoosh-Reloaded** - Updated from unmaintained Whoosh to Whoosh-Reloaded
  - Active maintenance and Python 3.13+ compatibility
  - Added `cached-property` dependency for compatibility
- Updated various GitHub Actions dependencies

#### CI/CD Improvements
- Enhanced CI workflow with better test coverage display
- **Fixed dependency check workflow permissions** - Added write permissions for automated PR creation
- Updated Docker image publishing workflow with multi-platform support
- Improved GitHub Actions workflow configurations

#### Documentation Structure
- Consolidated MCP planning documents into single `TODO.md`
- Removed outdated specification files to streamline project structure
- Cleaned up 4,300+ lines of obsolete planning documentation

#### Code Quality
- Improved logging formatting in `main.py` and MCP server
- Better error messages and debug output
- Enhanced Docker build scripts with better error handling

### Fixed

- **Python 3.13 Compatibility** - Suppressed SyntaxWarnings from Whoosh library
  - Proper handling of invalid escape sequences in regex patterns
  - Ensures clean operation on Python 3.13+
- GitHub Actions permissions for automated dependency updates
- Docker build process improvements

### Technical Details

- MCP endpoint now production-ready with all features from v0.1.0
- Container images optimized for size and build speed
- Automated publishing pipeline with version tagging
- Multi-platform container support (amd64, arm64)

## v0.1.0 (2026-01-31)

### Added

#### Core Features
- Beautiful Nuxt UI-inspired three-column layout (sidebar, content, TOC)
- Zero-configuration markdown documentation server
- FastAPI-based web server with async support
- Smart disk caching system (<5ms cached responses)
- Hot reload in debug mode
- Support for Python 3.11, 3.12, 3.13, 3.14

#### Markdown Support
- Full markdown rendering with syntax highlighting (Pygments)
- Tables support
- Task lists (checkboxes)
- Footnotes
- Table of contents (TOC) auto-generation
- Code blocks with syntax highlighting
- Mermaid diagram support
- Special character handling

#### AI-Native Features
- **llms.txt** endpoint - Documentation index for AI assistants
- **llms-full.txt** endpoint - Complete context export with all pages
- **MCP (Model Context Protocol)** endpoint - Interactive queries for LLMs
  - `search_docs` tool - Semantic search across documentation
  - `get_doc_page` tool - Retrieve specific pages with section filtering
  - `list_doc_pages` tool - List all available pages by category
- Whoosh-based full-text search indexing
- Rate limiting for MCP endpoint (120 req/60s per IP)
- Automatic link transformation to absolute URLs for AI consumption

#### Navigation & UI
- Sidebar navigation from `sidebar.md`
- Top bar configuration from `topbar.md`
- Active link highlighting
- External link indicators
- Responsive design (mobile, tablet, desktop)
- Dark mode ready CSS

#### Deployment
- Docker support with optimized Dockerfile
- Docker Compose examples
- Kubernetes deployment examples
- Cloud platform deployment guides (Heroku, Railway, Fly.io, DigitalOcean)
- Health check endpoint (`/health`)

#### Developer Experience
- CLI command: `servemd` (main entry point)
- CLI command: `docs-server` (alias)
- CLI command: `servemd-mcp` (MCP server CLI)
- Environment variable configuration
- Asset serving (images, PDFs, videos, audio)
- Static file mounting for assets directory
- Comprehensive test suite (208 tests, 100% passing)

#### Configuration
- `DOCS_ROOT` - Documentation directory path
- `CACHE_ROOT` - Cache directory path
- `PORT` - Server port (default: 8080)
- `DEBUG` - Enable debug/hot-reload mode
- `BASE_URL` - Base URL for absolute links
- `MCP_ENABLED` - Enable/disable MCP endpoint
- `MCP_RATE_LIMIT_REQUESTS` - MCP rate limit
- `MCP_RATE_LIMIT_WINDOW` - MCP rate limit window

#### Security
- Path traversal protection
- Safe file path validation
- Input sanitization
- Rate limiting for API endpoints
- No code execution from user content

#### Documentation
- Comprehensive user documentation in `docs/`
- Deployment guides for various platforms
- API endpoint documentation
- Configuration guide
- Quick start guides
- MCP integration guide
- Publishing guide with GitHub Actions workflow

### Technical Details
- Built with FastAPI 0.128+
- Uses uvicorn as ASGI server
- Markdown rendering with pymdown-extensions
- Full-text search with Whoosh
- Async/await for I/O operations
- Type hints throughout codebase
- Ruff for linting and formatting
- pytest with asyncio support

### Package
- Published to PyPI as `servemd`
- Dynamic versioning from `__version__` in `__init__.py`
- Apache 2.0 License
- Includes examples and templates
- GitHub Actions workflow for automated publishing
- PyPI Trusted Publishing support

---

[Unreleased]: https://github.com/jberends/servemd/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/jberends/servemd/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/jberends/servemd/compare/v0.2.0...v1.0.0
[0.2.0]: https://github.com/jberends/servemd/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/jberends/servemd/releases/tag/v0.1.0
