# Markdown Documentation Server

A lightweight, fast, and **beautiful** documentation server that renders Markdown files as styled HTML with zero configuration.

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/tests-71%20passing-brightgreen.svg)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🌟 What Makes This Special?

This isn't just another static site generator. It's a **live documentation server** with remarkable features:

- ✨ **Zero Configuration** - Drop `.md` files and go
- 🎨 **Beautiful Design** - Nuxt UI-inspired three-column layout
- 🤖 **AI-Friendly** - Built-in llms.txt support for Claude, ChatGPT, etc.
- ⚡ **Performance** - Smart caching, fast rendering
- 🐳 **Docker Ready** - Production-optimized container
- 🧪 **Well Tested** - 71 tests, 100% passing
- 📱 **Responsive** - Mobile/tablet/desktop support

---

## 🚀 Quick Start

### For End Users (Serve Your Own Docs)

**Option 1: Quick local serving with uvx** (no installation needed):
```bash
cd /path/to/your/docs
uvx --from servemd docs-server
```

**Option 2: Docker with volume mount**:
```bash
docker run -it --rm -p 8080:8080 -v $(pwd):/app/docs ghcr.io/yourusername/servemd:latest
```

**Option 3: Build custom Docker image**:
```bash
# Create Dockerfile in your docs directory (see examples/Dockerfile.user-template)
FROM ghcr.io/yourusername/servemd:latest
COPY . /app/docs/

# Build and run
docker build -t my-docs:latest .
docker run -p 8080:8080 my-docs:latest
```

Visit **http://localhost:8080** - Your documentation is live! 🎉

📚 **[Complete End-User Guide →](docs/quick-start-user.md)**

### For Contributors (Develop ServeMD)

```bash
# Install with uv (recommended)
pip install uv
uv sync

# Run the server
uv run python -m docs_server

# Or with custom docs directory
DOCS_ROOT=./my-docs uv run python -m docs_server
```

---

## 📖 Documentation

This project **documents itself**! The `/docs` folder contains comprehensive documentation powered by the server.

**Read the full documentation:** Run the server and visit http://localhost:8080

### Quick Links

- **[Quick Setup](docs/quick-setup.md)** - Get running in 5 minutes
- **[Markdown Features](docs/features/markdown.md)** - See what's possible
- **[LLMs.txt Guide](docs/features/llms-txt.md)** - AI assistant integration ⭐
- **[Configuration](docs/configuration.md)** - Environment variables
- **[Docker Deployment](docs/deployment/docker.md)** - Production deployment
- **[API Reference](docs/api/endpoints.md)** - HTTP endpoints

---

## ✨ Key Features

### Rich Markdown Support

- ✅ Tables, code blocks with syntax highlighting
- ✅ Task lists, footnotes, definition lists
- ✅ Automatic table of contents
- ✅ Math expressions (coming soon)
- ✅ Mermaid diagrams

### Beautiful UI

- 🎨 Three-column responsive layout (sidebar, content, TOC)
- 🎨 Syntax highlighting with Pygments
- 🎨 Active link highlighting
- 🎨 Mobile-first design
- 🎨 Dark mode ready

### AI Assistant Integration

- 🤖 **llms.txt** endpoint for AI indexing
- 🤖 **llms-full.txt** for complete context
- 🤖 Automatic link transformation
- 🤖 Curated or auto-generated indexes

### Developer Experience

- 🔥 Hot reload in debug mode
- 🔥 Clear error messages
- 🔥 Type hints everywhere
- 🔥 Comprehensive test suite
- 🔥 Fast dependency installation with `uv`

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
DOCS_ROOT=./docs              # Documentation directory
CACHE_ROOT=./__cache__        # Cache directory
PORT=8080                     # Server port
DEBUG=true                    # Enable debug mode
BASE_URL=https://docs.site.com  # Base URL for llms.txt
```

See [Configuration Guide](docs/configuration.md) for details.

---

## 🎯 Use Cases & Deployment Guides

Perfect for:

- **Open Source Projects** - Self-hosted, beautiful docs
- **Internal Teams** - Company documentation portals
- **API Documentation** - REST/GraphQL API docs
- **Technical Writing** - Blogs and tutorials
- **Knowledge Bases** - Internal wikis

### 📘 Deployment Guides

Choose your deployment method:

1. **[Quick Start for End Users](docs/quick-start-user.md)** - Overview of all options
2. **[Local Development](docs/deployment/local-development.md)** - uvx, pipx, Docker volumes
3. **[User Dockerfile Template](docs/deployment/user-dockerfile.md)** - Build custom images
4. **[Cloud Platforms](docs/deployment/cloud-platforms.md)** - Heroku, Railway, Fly.io, DigitalOcean, etc.
5. **[Kubernetes](docs/deployment/kubernetes.md)** - k8s, k3s, Helm charts, GitOps

### 🛠️ Ready-to-Use Examples

Check the **[examples/](examples/)** directory for:
- `serve-docs-local.sh` - Shell script for local serving
- `Dockerfile.user-template` - User Dockerfile template
- `docker-compose.user.yml` - Docker Compose setup
- `k8s-simple.yaml` - Simple Kubernetes deployment

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
└── main.py            # FastAPI routes
```

**Total: 1,502 lines across 9 focused modules**

---

## 🧪 Testing

Comprehensive test coverage with pytest:

```bash
# Run all tests
uv run pytest tests/ -v

# Results
71 tests, 100% passing ✅
- Unit tests: 57 tests
- Integration tests: 14 tests
- Execution time: <0.2s
```

---

## 🔧 Development

```bash
# Clone
git clone https://github.com/yourusername/markdown-docs-server
cd markdown-docs-server

# Install dependencies
uv sync --group dev

# Run tests
uv run pytest tests/ -v

# Linting
uv run ruff check src/
uv run ruff format src/

# Start dev server (auto-reload)
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

## 🤝 Contributing

Contributions welcome! This is a production-ready server with:

- ✅ Python 3.13+ with modern features
- ✅ FastAPI for performance
- ✅ uv for fast dependency management
- ✅ pytest for comprehensive testing
- ✅ Ruff for linting and formatting

---

## 📜 License

MIT License - use freely for any project!

---

## 🌐 Live Examples

See it in action:

1. **This Documentation** - Run the server and visit http://localhost:8080
2. **Your Project** - Point `DOCS_ROOT` to your markdown files
3. **Examples** - Check `/docs/examples/` for templates

---

## 🎓 Learn More

### Documentation Highlights

- **[Markdown Features](docs/features/markdown.md)** - Complete capabilities showcase with examples
- **[Navigation Guide](docs/features/navigation.md)** - Sidebar and topbar configuration
- **[LLMs.txt Support](docs/features/llms-txt.md)** - AI assistant integration (remarkable!)
- **[Docker Deployment](docs/deployment/docker.md)** - Production deployment guide
- **[API Reference](docs/api/endpoints.md)** - All HTTP endpoints

---

## 🙋 Support

- 📖 **Documentation**: http://localhost:8080 (after starting server)
- 🐛 **Issues**: [GitHub Issues](https://github.com/yourusername/markdown-docs-server/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/yourusername/markdown-docs-server/discussions)

---

## 🎉 Getting Started

Ready to create beautiful documentation?

```bash
# 1. Install
pip install uv && uv sync

# 2. Prepare your docs
mkdir -p docs
cp docs/index.md docs/index.md.example  # Use examples

# 3. Start server
uv run python -m docs_server

# 4. Open browser
open http://localhost:8080
```

**That's it!** Your documentation is live in 4 commands! 🚀

---

<div align="center">

**Built with ❤️ using Python, FastAPI, and Markdown**

[Documentation](http://localhost:8080) • [GitHub](https://github.com/yourusername/markdown-docs-server) • [Docker Hub](https://hub.docker.com/r/yourusername/markdown-docs-server)

</div>
