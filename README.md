# servemd

**Serve docs to humans and AI.**

Beautiful markdown documentation with native llms.txt support. Zero configuration, production-ready.

[![PyPI](https://img.shields.io/pypi/v/servemd.svg)](https://pypi.org/project/servemd/)
[![Docker Hub](https://img.shields.io/docker/v/jberends/servemd?label=docker)](https://hub.docker.com/r/jberends/servemd)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.128+-green.svg)](https://fastapi.tiangolo.com/)
[![MCP](https://img.shields.io/badge/MCP-enabled-purple.svg)](docs/features/mcp.md)
[![Tests](https://img.shields.io/badge/tests-208%20passing-brightgreen.svg)](tests/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-yellow.svg)](LICENSE)
[![CodeQL](https://github.com/jberends/servemd/actions/workflows/security.yml/badge.svg)](https://github.com/jberends/servemd/actions/workflows/security.yml)

---

## Why servemd?

Unlike basic markdown servers, **servemd** is built for the AI era:

```
Markdown → Beautiful HTML    → Humans
         → llms.txt          → AI/LLMs
         → llms-full.txt     → Complete AI context
         → /mcp endpoint     → AI assistants (250x less context)
```

**For humans:** Nuxt UI-inspired design, three-column layout, zero configuration.
**For AI:** Native llms.txt support, structured context, ready for the Model Context Protocol era.

---

## ✨ Features

- 🎨 **Beautiful Design** — Nuxt UI-inspired three-column layout (sidebar, content, TOC)
- 🤖 **AI-Native** — Built-in llms.txt and llms-full.txt for Claude, ChatGPT, Cursor, etc.
- 🔌 **MCP Support** — Model Context Protocol endpoint for interactive AI queries (250x less context)
- ✨ **Zero Configuration** — Drop `.md` files and go
- ⚡ **Fast** — Smart disk caching, <5ms cached responses
- 🐳 **Docker Ready** — Production-optimized container
- 🧪 **Well Tested** — 208 tests, 100% passing
- 📱 **Responsive** — Mobile, tablet, and desktop support

---

## 🚀 Quick Start

### Install

```bash
pip install servemd
```

### Run

```bash
# Serve docs from current directory
servemd

# Or specify a directory
servemd ./my-docs
```

Visit **http://localhost:8080** — your documentation is live.

**Live demo:** [https://servemd.me.cloudns.cl](https://servemd.me.cloudns.cl)

### Alternative: Docker

```bash
# Quick start - mount your docs
docker run -p 8080:8080 -v $(pwd)/docs:/app/__docs__ jberends/servemd:latest

# Or build custom image with docs baked in
FROM jberends/servemd:latest
COPY ./my-docs/ /app/__docs__/
```

**See [DOCKER_README.md](DOCKER_README.md)** for complete Docker usage guide.

### Alternative: uvx (no install)

```bash
uvx servemd ./my-docs
```

📚 **[Complete Setup Guide →](docs/quick-start-user.md)**

### For Contributors

```bash
git clone https://github.com/servemd/servemd
cd servemd
uv sync
uv run python -m docs_server
```

---

## 🤖 AI-Native: llms.txt & MCP Support

servemd automatically serves your docs in AI-friendly formats:

| Endpoint | Purpose | Audience | Context Size |
|----------|---------|----------|--------------|
| `/{page}.html` | Rendered HTML with navigation | Humans | N/A |
| `/{page}.md` | Raw markdown | AI/LLMs | Per-page |
| `/llms.txt` | Documentation index | AI assistants | Small (~5KB) |
| `/llms-full.txt` | Complete context (all pages) | AI deep context | Large (~500KB+) |
| `/mcp` | **Interactive queries** | **AI (MCP clients)** | **Minimal (250x less)** |

### llms.txt - Static Index

**Example:** Give an AI assistant your docs:
```
"Read my documentation at https://docs.example.com/llms.txt"
```

The AI gets a structured index with absolute URLs to every page. For complete context, use `/llms-full.txt` which includes all page content inline.

### MCP - Interactive Queries (Recommended for AI)

**Model Context Protocol** provides on-demand documentation access with **250x less context**:

```json
POST /mcp
{
  "method": "tools/call",
  "params": {
    "name": "search_docs",
    "arguments": {
      "query": "authentication",
      "limit": 5
    }
  }
}
```

**Benefits:**
- 🎯 **Precise** — AI queries only what it needs
- ⚡ **Fast** — No sending entire documentation every time
- 💰 **Cost-effective** — 250x less tokens than llms-full.txt
- 🔍 **Smart** — Full-text search with Whoosh

**Available MCP Tools:**
- `search_docs` — Semantic search across documentation
- `get_doc_page` — Retrieve specific pages with section filtering
- `list_doc_pages` — List all available pages by category

**See [MCP Integration Guide](docs/features/mcp.md)** for details.

---

## ✨ Key Features

### For Humans
- 🎨 Nuxt UI-inspired three-column layout (sidebar, content, TOC)
- 🎨 Syntax highlighting with Pygments
- 🎨 Responsive design (mobile, tablet, desktop)
- 🎨 Dark mode ready
- ✅ Tables, task lists, footnotes, Mermaid diagrams

### For AI
- 🤖 **llms.txt** — Structured documentation index (5KB)
- 🤖 **llms-full.txt** — Complete context export (500KB+)
- 🔌 **MCP endpoint** — Interactive queries via Model Context Protocol
  - **250x less context** than llms-full.txt
  - Full-text search with Whoosh
  - On-demand page retrieval
  - Section filtering
- 🤖 Automatic link transformation to absolute URLs
- 🤖 Curated or auto-generated indexes

### For Developers
- ⚡ Fast — disk caching, <5ms cached responses
- 🔥 Hot reload in debug mode
- 🔧 Zero configuration required
- 🐍 Python 3.11-3.14, FastAPI, Pydantic
- 🧪 208 tests, 100% passing

---

## 📁 File Structure

Your documentation needs just 3 required files:

```
docs/
├── index.md       # Homepage (required)
├── sidebar.md     # Navigation (required)
├── topbar.md      # Top bar (required)
├── llms.txt       # AI index (optional)
└── your-content.md # Your pages
```

---

## ⚙️ Configuration

Configure via environment variables:

```bash
DOCS_ROOT=./docs                 # Documentation directory
CACHE_ROOT=./__cache__           # Cache directory
PORT=8080                        # Server port
DEBUG=true                       # Enable debug mode
BASE_URL=https://docs.site.com   # Base URL for llms.txt
MCP_ENABLED=true                 # Enable MCP endpoint (default: true)
MCP_RATE_LIMIT_REQUESTS=120      # MCP rate limit (requests per window)
MCP_RATE_LIMIT_WINDOW=60         # MCP rate limit window (seconds)
```

See [Configuration Guide](docs/configuration.md) for details.

---

## 🎯 Use Cases

**servemd** is perfect for:

- **SaaS Documentation** — Customer-facing support docs with AI assistant integration
- **Open Source Projects** — Self-hosted, beautiful docs
- **Internal Teams** — Company knowledge bases and wikis
- **API Documentation** — REST/GraphQL API docs
- **Technical Writing** — Blogs and tutorials

### 📘 Deployment

| Method | Best For |
|--------|----------|
| [Local Development](docs/deployment/local-development.md) | Development, previewing |
| [Docker](docs/deployment/docker.md) | Production, CI/CD |
| [Cloud Platforms](docs/deployment/cloud-platforms.md) | Heroku, Railway, Fly.io, DigitalOcean |
| [Kubernetes](docs/deployment/kubernetes.md) | k8s, k3s, Helm charts |

### 🛠️ Examples

Check **[examples/](examples/)** for ready-to-use templates:
- `Dockerfile.user-template` — Custom Docker image
- `docker-compose.user.yml` — Docker Compose setup
- `k8s-simple.yaml` — Kubernetes deployment

---

## 🏗️ Architecture

Clean, modular FastAPI application:

```
src/docs_server/
├── config.py           # Settings & environment
├── helpers.py          # Utilities & navigation
├── caching.py          # Smart caching
├── markdown_service.py # Markdown rendering
├── llms_service.py     # LLMs.txt generation
├── templates.py        # HTML templates
├── main.py             # FastAPI routes
└── mcp/                # Model Context Protocol
    ├── server.py       # MCP JSON-RPC handler
    ├── tools.py        # MCP tools (search, get, list)
    ├── search.py       # Full-text search with Whoosh
    └── indexer.py      # Documentation indexing
```

---

## 🧪 Testing

```bash
uv run pytest tests/ -v

# 208 tests, 100% passing ✅
```

---

## 🔧 Development

```bash
git clone https://github.com/servemd/servemd
cd servemd
uv sync --group dev
uv run pytest tests/ -v
DEBUG=true uv run python -m docs_server
```

---

## 📊 Performance

| Endpoint | First Request | Cached |
|----------|---------------|--------|
| Rendered HTML | 50-100ms | <5ms |
| Raw Markdown | <10ms | <10ms |
| LLMs.txt | 100-200ms | <5ms |

---

## 📖 Documentation

- **[Quick Setup](docs/quick-setup.md)** — Get running in 5 minutes
- **[Markdown Features](docs/features/markdown.md)** — Tables, code blocks, diagrams
- **[LLMs.txt Guide](docs/features/llms-txt.md)** — AI assistant integration
- **[MCP Integration](docs/features/mcp.md)** — Interactive queries for LLMs
- **[Navigation](docs/features/navigation.md)** — Sidebar and topbar configuration
- **[Configuration](docs/configuration.md)** — Environment variables
- **[API Reference](docs/api/endpoints.md)** — HTTP endpoints

---

## 🙋 Support

- 📖 **Documentation**: [docs.servemd.dev](https://docs.servemd.dev) or run locally
- 🚀 **Live demo**: [servemd.me.cloudns.cl](https://servemd.me.cloudns.cl)
- 🐛 **Issues**: [GitHub Issues](https://github.com/servemd/servemd/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/servemd/servemd/discussions)

---

## 📜 License

MIT License — use freely for any project.

---

## 🎉 Get Started Now

```bash
pip install servemd
servemd ./my-docs
```

Visit **http://localhost:8080** — beautiful docs for humans, structured context for AI.

---

<div align="center">

**servemd** — Serve docs to humans and AI

Built with Python, FastAPI, and Markdown

[Documentation](https://docs.servemd.dev) · [Live Demo](https://servemd.me.cloudns.cl) · [PyPI](https://pypi.org/project/servemd/) · [GitHub](https://github.com/servemd/servemd)

</div>
