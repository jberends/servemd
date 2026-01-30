# Quick Setup Guide

Get your documentation server running in **5 minutes** or less!

## Prerequisites

- Python 3.13+ (or Python 3.11+ with minor adjustments)
- `uv` package manager (recommended) or `pip`

## Step 1: Install

### Option A: With uv (Recommended)

```bash
# Install uv if you haven't already
pip install uv

# Clone and setup
git clone https://github.com/yourusername/markdown-docs-server
cd markdown-docs-server
uv sync
```

### Option B: With pip

```bash
# Clone and setup
git clone https://github.com/yourusername/markdown-docs-server
cd markdown-docs-server
pip install -e .
```

## Step 2: Prepare Your Docs

Create a `docs` folder with required files:

```bash
mkdir -p docs
cd docs
```

### Required Files

**1. Create `index.md`** (your homepage):

```markdown
# Welcome to My Documentation

This is the homepage of my documentation.

## Quick Links

- [Getting Started](getting-started.md)
- [API Reference](api.md)
```

**2. Create `sidebar.md`** (navigation structure):

```markdown
# Navigation

* [Home](index.md)
* [Getting Started](getting-started.md)
* [API Reference](api.md)
  * [Authentication](api/auth.md)
  * [Endpoints](api/endpoints.md)
```

**3. Create `topbar.md`** (top navigation):

```markdown
# Top Bar

## left
* [Docs](index.md)

## right
* [GitHub](https://github.com/yourproject)
```

## Step 3: Run the Server

```bash
# From the project root
DOCS_ROOT=./docs uv run python -m docs_server
```

Or for development with auto-reload:

```bash
DOCS_ROOT=./docs DEBUG=true uv run python -m docs_server
```

## Step 4: View Your Docs

Open your browser to:

- **Homepage**: http://localhost:8080
- **Any page**: http://localhost:8080/getting-started.html
- **Raw markdown**: http://localhost:8080/getting-started.md
- **Health check**: http://localhost:8080/health
- **LLMs.txt**: http://localhost:8080/llms.txt

🎉 **That's it!** Your documentation is live!

---

## Quick Docker Setup

Prefer Docker? Even faster:

```bash
# Build
docker build -t my-docs .

# Run
docker run -p 8080:8080 -v $(pwd)/docs:/app/docs my-docs
```

Visit http://localhost:8080

---

## Environment Variables

Customize behavior with environment variables:

```bash
# Documentation root (default: ./test_docs or /app/docs in Docker)
DOCS_ROOT=./my-docs

# Cache directory (default: ./__cache__ or /app/cache in Docker)
CACHE_ROOT=./my-cache

# Base URL for llms.txt absolute links (auto-detected if not set)
BASE_URL=https://docs.mysite.com

# Enable debug mode with auto-reload (default: false)
DEBUG=true

# Server port (default: 8080)
PORT=3000
```

---

## File Structure

Your docs directory should look like this:

```
docs/
├── index.md              # Required: Homepage
├── sidebar.md            # Required: Sidebar navigation
├── topbar.md             # Required: Top bar
├── llms.txt              # Optional: AI assistant index
├── getting-started.md    # Your content pages
├── api.md
├── api/
│   ├── auth.md
│   └── endpoints.md
└── assets/               # Optional: Images, etc.
    └── logo.svg
```

---

## Next Steps

Now that your server is running:

1. **[Explore Features](features/markdown.md)** - See what's possible with Markdown
2. **[Configure Navigation](features/navigation.md)** - Customize your sidebar and topbar
3. **[Deploy to Production](deployment/docker.md)** - Take it live!

---

## Troubleshooting

### Server won't start?

Check that Python 3.13+ is installed:

```bash
python --version
# Should show 3.13.0 or higher
```

### Can't find docs?

Make sure `DOCS_ROOT` points to the correct directory:

```bash
ls $DOCS_ROOT
# Should show: index.md sidebar.md topbar.md
```

### Port already in use?

Change the port:

```bash
PORT=3000 uv run python -m docs_server
```

### Need help?

- Check the [Configuration Guide](configuration.md)
- Review [Examples](examples/basic.md)
- Open an issue on GitHub

---

## What's Next?

Your documentation is now live! Here's what you can do:

✅ Add more markdown pages  
✅ Customize navigation  
✅ Add images and assets  
✅ Enable llms.txt for AI  
✅ Deploy to production  

**Happy documenting!** 📚
