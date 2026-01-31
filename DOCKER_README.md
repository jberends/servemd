# Docker Usage Guide for ServeM

## Understanding DOCS_ROOT

**DOCS_ROOT** is the directory where servemd reads your markdown documentation files.

- **Default location**: `/app/__docs__`
- **Set via**: `ENV DOCS_ROOT=/app/__docs__` in Dockerfile
- **Can be changed**: Set `DOCS_ROOT` environment variable at runtime

---

## Three Ways to Use the Docker Image

### 1️⃣ **Quick Start - Mount Your Docs at Runtime** (Recommended for Development)

Use the published image and mount your documentation directory:

```bash
# From Docker Hub
docker run -p 8080:8080 \
  -v $(pwd)/docs:/app/__docs__:ro \
  jberends/servemd:latest

# Or from GHCR
docker run -p 8080:8080 \
  -v $(pwd)/docs:/app/__docs__:ro \
  ghcr.io/jberends/servemd:latest
```

**How it works:**
- ✅ Your local `./docs` folder is mounted to `/app/__docs__` (DOCS_ROOT)
- ✅ Changes to local files are immediately visible (with DEBUG=true)
- ✅ No rebuild needed

---

### 2️⃣ **Build Your Docs Into the Image** (Recommended for Production)

Create a custom Dockerfile that bundles YOUR documentation:

```dockerfile
# Dockerfile
FROM jberends/servemd:latest

# Copy YOUR documentation into DOCS_ROOT
COPY ./my-docs/ /app/__docs__/
```

Build and run:

```bash
docker build -t my-docs-server .
docker run -p 8080:8080 my-docs-server
```

**How it works:**
- ✅ Your docs are baked into the image
- ✅ Self-contained image - no external volumes needed
- ✅ Perfect for deployment to production

See [`examples/Dockerfile.custom-docs`](examples/Dockerfile.custom-docs) for a complete example.

---

### 3️⃣ **Use a Different DOCS_ROOT Location**

Override the DOCS_ROOT at runtime:

```bash
docker run -p 8080:8080 \
  -v /path/to/my/docs:/data/documentation \
  -e DOCS_ROOT=/data/documentation \
  jberends/servemd:latest
```

**How it works:**
- ✅ Mount your docs to ANY path
- ✅ Set `DOCS_ROOT` to that path
- ✅ Useful for existing filesystem layouts

---

## Dockerfile Structure Explained

The Dockerfile uses **multi-stage builds** for optimal image size:

### Stage 1: Base Image (Build Stage)
```dockerfile
FROM python:3.13-trixie AS base
# Install system dependencies
# Install Python dependencies
# Creates /app/.venv with all packages
```

### Stage 2: Application Image (Runtime Stage)
```dockerfile
FROM python:3.13-slim-trixie AS app
# Copy only the .venv (no build tools)
# Copy application source
# Set up DOCS_ROOT=/app/__docs__
# Copy docs/ into DOCS_ROOT
```

**Benefits:**
- 📦 Smaller final image (~180MB vs ~1.2GB)
- 🔒 No build tools in production image
- ⚡ Faster deployments

---

## DOCS_ROOT Requirements

Your documentation directory must contain these files:

```
docs/
├── index.md       # Homepage (required)
├── sidebar.md     # Left navigation (required)
├── topbar.md      # Top bar with links (required)
├── llms.txt       # AI index (optional, auto-generated)
└── *.md           # Your other markdown pages
```

**Example structure:**
```
my-docs/
├── index.md
├── sidebar.md
├── topbar.md
├── getting-started.md
├── api/
│   ├── authentication.md
│   └── endpoints.md
└── guides/
    └── deployment.md
```

---

## Complete Examples

### Development Setup

```bash
# 1. Create your docs
mkdir -p ./my-docs
echo "# Welcome" > ./my-docs/index.md
echo "# Sidebar\n- [Home](index.md)" > ./my-docs/sidebar.md
echo "# My Docs" > ./my-docs/topbar.md

# 2. Run with live reload
docker run -p 8080:8080 \
  -v $(pwd)/my-docs:/app/__docs__ \
  -e DEBUG=true \
  jberends/servemd:latest

# 3. Open browser
open http://localhost:8080
```

### Production Deployment

```dockerfile
# Dockerfile.production
FROM jberends/servemd:latest

# Remove example docs
RUN rm -rf /app/__docs__/*

# Copy production docs
COPY ./production-docs/ /app/__docs__/

# Set production config
ENV DEBUG=false
ENV BASE_URL=https://docs.mycompany.com
```

Build and deploy:
```bash
docker build -f Dockerfile.production -t my-company-docs:1.0 .
docker run -d -p 8080:8080 --name docs-server my-company-docs:1.0
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DOCS_ROOT` | `/app/__docs__` | **Where markdown files are read from** |
| `CACHE_ROOT` | `/app/__cache__` | Cache directory for rendered HTML |
| `PORT` | `8080` | HTTP server port |
| `DEBUG` | `false` | Enable debug mode (auto-reload) |
| `BASE_URL` | (auto) | Base URL for llms.txt absolute links |
| `MCP_ENABLED` | `true` | Enable/disable MCP endpoint |

---

## Advanced: Custom Cache Location

```bash
docker run -p 8080:8080 \
  -v $(pwd)/docs:/app/__docs__:ro \
  -v $(pwd)/cache:/app/__cache__ \
  -e CACHE_ROOT=/app/__cache__ \
  jberends/servemd:latest
```

**Benefits:**
- Persistent cache across container restarts
- Faster startup after first run

---

## Troubleshooting

### "Required file not found: index.md"

**Problem:** DOCS_ROOT doesn't contain required files.

**Solution:** Ensure your docs directory has `index.md`, `sidebar.md`, and `topbar.md`:
```bash
ls -la ./docs/
# Should show: index.md, sidebar.md, topbar.md
```

### Docs not updating in container

**Problem:** Changes to local files not visible.

**Solution 1:** Enable debug mode:
```bash
docker run -p 8080:8080 -v $(pwd)/docs:/app/__docs__ -e DEBUG=true servemd:latest
```

**Solution 2:** Clear cache:
```bash
docker exec <container-id> rm -rf /app/__cache__/*
```

### Permission errors

**Problem:** Container can't read mounted docs.

**Solution:** Ensure files are readable:
```bash
chmod -R a+r ./docs
```

---

## Image Sizes

| Stage | Size | Contents |
|-------|------|----------|
| `base` | ~1.2GB | Python + build tools + dependencies |
| `app` (final) | ~180MB | Python slim + runtime only |

The final image only contains what's needed to run, not build.

---

## Quick Reference

```bash
# Pull image
docker pull jberends/servemd:latest

# Run with local docs
docker run -p 8080:8080 -v $(pwd)/docs:/app/__docs__ jberends/servemd:latest

# Build custom image
docker build -t my-docs .

# Check DOCS_ROOT location
docker run jberends/servemd:latest env | grep DOCS_ROOT

# Inspect image
docker inspect jberends/servemd:latest

# Shell into running container
docker exec -it <container-id> bash
```

---

## Related Documentation

- **Main README**: [README.md](README.md)
- **Docker Publishing**: [DOCKER_PUBLISHING.md](DOCKER_PUBLISHING.md)
- **Custom Dockerfile Example**: [examples/Dockerfile.custom-docs](examples/Dockerfile.custom-docs)
- **Deployment Guides**: [docs/deployment/](docs/deployment/)
