# Markdown Documentation Server

A **lightweight, fast, and beautiful** documentation server that renders Markdown files as styled HTML with zero configuration.

## 🚀 What Makes This Special?

This isn't just another static site generator. It's a **live documentation server** with remarkable features:

### ✨ Zero Configuration
- Drop your `.md` files in a folder
- Start the server
- Beautiful docs instantly available

### 🎨 Beautiful Design
- Inspired by [Nuxt UI](https://ui.nuxt.com/) documentation
- Three-column layout (sidebar, content, table of contents)
- Responsive design for mobile/tablet/desktop
- Dark mode ready with customizable colors

### 🤖 AI-Friendly
- **llms.txt** support for AI assistants
- **llms-full.txt** for complete context
- Automatic link transformation
- Optimized for Claude, ChatGPT, and other LLMs

### ⚡ Performance
- Intelligent caching system
- Fast markdown rendering
- Minimal dependencies
- Production-ready Docker image

### 🎯 Developer Experience
- Hot reload in development
- Clear error messages
- Type hints everywhere
- Comprehensive test suite (71 tests, 100% passing)

---

## 📚 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/markdown-docs-server
cd markdown-docs-server

# Install dependencies with uv (recommended)
pip install uv
uv sync

# Or with pip
pip install -e .
```

### Run Locally

```bash
# Development mode (auto-reload)
uv run python -m docs_server

# Or with environment variables
DOCS_ROOT=./my-docs PORT=8080 uv run python -m docs_server
```

Visit `http://localhost:8080` and see your documentation come to life! 🎉

---

## 🐳 Docker Deployment

### Quick Start

```bash
# Build the image
docker build -t markdown-docs-server .

# Run with your docs
docker run -p 8080:8080 \
  -v $(pwd)/my-docs:/app/docs \
  markdown-docs-server
```

### Production Deployment

```bash
# With environment variables
docker run -d \
  -p 8080:8080 \
  -e BASE_URL=https://docs.example.com \
  -e DEBUG=false \
  -v $(pwd)/docs:/app/docs \
  --restart unless-stopped \
  --name docs-server \
  markdown-docs-server
```

---

## 📖 Documentation Structure

Your documentation needs just **3 required files** and 1 optional:

```
docs/
├── index.md       # Homepage (required)
├── sidebar.md     # Navigation structure (required)
├── topbar.md      # Top bar navigation (required)
└── llms.txt       # AI assistant index (optional)
```

All other `.md` files are your content pages!

---

## 🎯 Key Features

| Feature | Description |
|---------|-------------|
| **Markdown Extensions** | Tables, code highlighting, TOC, task lists, and more |
| **Navigation** | Sidebar with groups, topbar with sections |
| **Caching** | Smart caching for fast performance |
| **Security** | Path traversal protection |
| **Dual Mode** | Serve HTML or raw markdown |
| **Assets** | Images, PDFs, videos supported |
| **LLMs.txt** | Built-in AI assistant support |
| **Responsive** | Mobile-first design |

---

## 🌟 What You're Seeing Now

This documentation is **powered by the server itself**! Every feature you see here is built-in:

- ✅ The beautiful three-column layout
- ✅ Syntax-highlighted code blocks
- ✅ Responsive navigation
- ✅ Automatic table of contents
- ✅ Markdown tables
- ✅ Task lists
- ✅ And much more!

---

## 🔍 Learn More

Explore the documentation to see all features in action:

- [**Quick Setup Guide**](quick-setup.md) - Get started in 5 minutes
- [**Markdown Features**](features/markdown.md) - See what's possible
- [**Navigation Guide**](features/navigation.md) - Create beautiful menus
- [**LLMs.txt Guide**](features/llms-txt.md) - AI assistant integration
- [**Docker Deployment**](deployment/docker.md) - Production deployment
- [**API Reference**](api/endpoints.md) - HTTP endpoints
- [**Configuration**](configuration.md) - Environment variables

---

## 💡 Why This Server?

### For Documentation Teams
- **Zero learning curve** - just write Markdown
- **Beautiful by default** - no CSS needed
- **Fast deployment** - Docker ready

### For Open Source Projects
- **GitHub-friendly** - works with GitHub Pages
- **Self-hosted** - own your docs
- **Modern design** - professional appearance

### For AI/LLM Integration
- **llms.txt native** - built-in AI support
- **Context optimization** - smart link transformation
- **Full content export** - llms-full.txt endpoint

---

## 🎨 Customization

While the default theme is beautiful, you can customize:

- Colors (CSS variables)
- Logo (place in `assets/`)
- Navigation structure (sidebar.md, topbar.md)
- Content organization (any folder structure)

---

## 🧪 Quality

This is a **production-ready** server with:

- ✅ **71 unit tests** (100% passing)
- ✅ **Type hints** everywhere
- ✅ **Linting** with Ruff
- ✅ **CI/CD** ready
- ✅ **Docker** optimized
- ✅ **Security** focused

---

## 🤝 Contributing

Contributions welcome! This server is:

- 🐍 **Python 3.13+** with modern features
- ⚡ **FastAPI** for performance
- 📦 **uv** for fast dependency management
- 🧪 **pytest** for comprehensive testing

---

## 📜 License

MIT License - use it freely for any project!

---

## 🚀 Next Steps

1. **[Quick Setup](quick-setup.md)** - Get running in 5 minutes
2. **[Features Guide](features/markdown.md)** - Explore all capabilities
3. **[Deployment](deployment/docker.md)** - Go to production

---

<div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 1rem; margin: 2rem 0;">
  <h2 style="color: white; margin-bottom: 1rem;">Ready to Create Beautiful Docs?</h2>
  <p style="font-size: 1.2rem; margin-bottom: 1.5rem;">Get started now and see your documentation transform!</p>
  <code style="background: rgba(255,255,255,0.2); padding: 0.5rem 1rem; border-radius: 0.5rem; font-size: 1rem;">
    uv run python -m docs_server
  </code>
</div>
