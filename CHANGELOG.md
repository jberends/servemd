# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-01-31

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

[Unreleased]: https://github.com/jberends/servemd/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/jberends/servemd/releases/tag/v0.1.0
