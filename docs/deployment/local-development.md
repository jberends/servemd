# Local Development Guide

Quick ways to serve your documentation locally without Docker.

## Method 1: Using uvx (Recommended)

The fastest way to serve local documentation using `uvx` (run packages without installation).

### Prerequisites

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Quick Start

Create a shell script `serve-docs.sh` in your documentation directory:

```bash
#!/bin/bash
# serve-docs.sh - Serve documentation with servemd

set -e

# Configuration
DOCS_DIR="${1:-.}"  # Use first argument or current directory
PORT="${PORT:-8080}"
DEBUG="${DEBUG:-false}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}📖 Starting ServeMD Documentation Server...${NC}"
echo -e "${YELLOW}📁 Documentation directory: ${DOCS_DIR}${NC}"
echo -e "${YELLOW}🌐 Port: ${PORT}${NC}"

# Run with uvx (installs if needed, then runs)
DOCS_ROOT="$DOCS_DIR" \
PORT="$PORT" \
DEBUG="$DEBUG" \
uvx --from servemd docs-server

# Alternative: If you want to run the module directly
# uvx --from servemd python -m docs_server
```

Make it executable:

```bash
chmod +x serve-docs.sh
```

### Usage

```bash
# Serve current directory
./serve-docs.sh

# Serve specific directory
./serve-docs.sh ./my-docs

# With custom port
PORT=3000 ./serve-docs.sh

# With debug mode
DEBUG=true ./serve-docs.sh

# Visit http://localhost:8080
```

### One-liner

For quick testing without a script:

```bash
# Current directory
uvx --from servemd docs-server

# Custom directory
DOCS_ROOT=./my-docs uvx --from servemd docs-server

# Custom port and directory
DOCS_ROOT=./my-docs PORT=3000 uvx --from servemd docs-server
```

## Method 2: Install Globally with pipx

Install once, use everywhere:

```bash
# Install servemd globally
pipx install servemd

# Use it anywhere
cd /path/to/my-docs
docs-server

# Or with environment variables
DOCS_ROOT=./my-docs PORT=3000 docs-server
```

## Method 3: Development Installation

For contributors or advanced users:

```bash
# Clone the repository
git clone https://github.com/yourusername/servemd.git
cd servemd

# Install with uv
uv sync

# Run in development mode
DEBUG=true uv run python -m docs_server

# Or use the installed command
uv run docs-server
```

## Method 4: Docker with Volume Mount

Serve local directory without building a custom image:

```bash
# Pull the official image
docker pull ghcr.io/yourusername/servemd:latest

# Serve current directory
docker run -it --rm \
  -p 8080:8080 \
  -v $(pwd):/app/docs \
  ghcr.io/yourusername/servemd:latest

# Serve specific directory
docker run -it --rm \
  -p 8080:8080 \
  -v /path/to/my-docs:/app/docs \
  ghcr.io/yourusername/servemd:latest

# With custom configuration
docker run -it --rm \
  -p 3000:3000 \
  -e PORT=3000 \
  -e DEBUG=true \
  -e BASE_URL=http://localhost:3000 \
  -v $(pwd):/app/docs \
  ghcr.io/yourusername/servemd:latest
```

### Create a Docker Alias

Add to your `.bashrc` or `.zshrc`:

```bash
# Alias for serving docs with servemd
alias serve-docs='docker run -it --rm -p 8080:8080 -v $(pwd):/app/docs ghcr.io/yourusername/servemd:latest'
```

Usage:

```bash
cd /path/to/my-docs
serve-docs
```

## Configuration Options

All methods support these environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DOCS_ROOT` | `./docs` | Path to documentation directory |
| `CACHE_ROOT` | `./__cache__` | Path to cache directory |
| `PORT` | `8080` | Server port |
| `DEBUG` | `false` | Enable debug mode (auto-reload) |
| `BASE_URL` | Auto-detected | Base URL for llms.txt links |

## Tips

### Watch Mode

With `DEBUG=true`, the server auto-reloads when files change:

```bash
DEBUG=true uvx --from servemd docs-server
```

### Custom Port

Avoid port conflicts:

```bash
PORT=3000 uvx --from servemd docs-server
```

### Base URL for AI Assistants

Set `BASE_URL` for correct links in `llms.txt`:

```bash
BASE_URL=https://docs.mycompany.com uvx --from servemd docs-server
```

## Comparison

| Method | Speed | Isolation | Best For |
|--------|-------|-----------|----------|
| **uvx** | ⚡⚡⚡ Fast | ✅ User-level | Quick local serving |
| **pipx** | ⚡⚡ Fast | ✅ User-level | Frequent use |
| **Docker** | ⚡ Slower startup | ✅✅ Full isolation | Production-like testing |
| **Development** | ⚡⚡ Fast | ❌ Global | Contributing to servemd |

## Troubleshooting

### Port Already in Use

```bash
# Use a different port
PORT=3001 uvx --from servemd docs-server
```

### Permission Denied

```bash
# Make script executable
chmod +x serve-docs.sh

# Or run with bash
bash serve-docs.sh
```

### Module Not Found

```bash
# Ensure uv is installed
uv --version

# Try with explicit python
uvx --from servemd python -m docs_server
```

## Next Steps

- **[User Dockerfile Template](./user-dockerfile.md)** - Bundle docs in Docker image
- **[Kubernetes Deployment](./kubernetes.md)** - Deploy to k3s or k8s
- **[Configuration](../configuration.md)** - Advanced settings
