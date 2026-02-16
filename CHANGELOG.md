# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **"Powered by servemd" branding** - Configurable attribution in sidebar footer:
  - `SERVEMD_BRANDING_ENABLED` env var (default: `true`); set to `false` for white-label deployments
  - Sticky at bottom of sidebar with link to GitHub repo
  - Hidden on mobile when sidebar is collapsed
- **In-page search** - Human-readable search experience when MCP is enabled:
  - Search bar in topbar (configurable via `{{search}}` placeholder in `topbar.md`)
  - Search page at `/search?q=...` with live results as you type (debounced, min 3 characters)
  - Keyboard shortcut `/` to focus search bar; `Escape` to blur
  - Search terms highlighted in results (pale yellow marker)
  - Configurable icon, mode (`full`, `button`, `input`), and placeholder via `{{search:icon=...,mode=...,placeholder=...}}`
  - JSON endpoint (`/search?format=json`) for client-side live search
- **`--clear-cache` CLI flag** - Clear the cache directory on startup before serving
- **Hetzner bare server deployment** - Minimal deployment guide for Debian 13 VPS on Hetzner (`deployment/hetzner/`). Includes Docker Compose stack with servemd + Caddy reverse proxy, automatic HTTPS via Let's Encrypt, and hourly auto-updates via cron. See `deployment/hetzner/README.md`.

### Changed

- **Reduced padding/margins** - Tighter spacing throughout: sidebar, main content, typography (h1, h2, h3, p, lists, code blocks, tables, blockquotes), and "Powered by" area. Topbar unchanged.
- **Docker container security hardening** - Significant security improvements to the Docker image:
  - Switched base image from Debian Trixie (testing) to Debian Bookworm (stable), reducing CVEs by ~40–57%
  - Container now runs as non-root `servemd` user (UID 1000) instead of root
  - Applies security patches during build (`apt-get upgrade`)
  - Minimal dependencies with `--no-install-recommends`
  - Proper file ownership for all application files
  - See `DOCKER_SECURITY.md` and `SECURITY_CHANGES.md` for details

### Fixed

- **ReDoS in page actions template** - Replaced regex `(<h1[^>]*>)(.*?)(</h1>)` with string-based search to avoid polynomial backtracking on user-controlled content (CodeQL py/polynomial-redos).
- **Log injection in MCP search** - Sanitized user-provided search query and exception messages before logging to prevent log injection (CodeQL High).
- **Sidebar and topbar link resolution** - Links in `sidebar.md` and `topbar.md` are now normalized to root-relative paths (`/dir/page.html`) during parsing. Previously, relative links like `deployment/docker.html` were resolved by the browser relative to the current page URL, causing broken links (e.g. `/dir/dir/page.html`) when viewing pages in subdirectories. Content markdown links remain relative to the current file and work correctly.

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

[Unreleased]: https://github.com/jberends/servemd/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/jberends/servemd/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/jberends/servemd/releases/tag/v0.1.0
