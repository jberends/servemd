# ServeMD Usage Examples

This directory contains practical examples for using ServeMD in various scenarios.

## Quick Links

| File | Description | Use Case |
|------|-------------|----------|
| **[serve-docs-local.sh](./serve-docs-local.sh)** | Shell script for local serving | Development, testing |
| **[Dockerfile.user-template](./Dockerfile.user-template)** | User Dockerfile template | Building custom images |
| **[docker-compose.user.yml](./docker-compose.user.yml)** | Docker Compose example | Local development, testing |
| **[k8s-simple.yaml](./k8s-simple.yaml)** | Simple Kubernetes deployment | Production deployment |

## 1. Local Development

### Quick Start with uvx

The fastest way to serve your documentation:

```bash
# Copy the script to your docs directory
cp serve-docs-local.sh /path/to/your/docs/
cd /path/to/your/docs/
chmod +x serve-docs-local.sh

# Run it
./serve-docs-local.sh

# Visit http://localhost:8080
```

### One-liner Alternative

```bash
DOCS_ROOT=./my-docs uvx --from servemd docs-server
```

## 2. Docker-based Deployment

### Method A: Volume Mount (Development)

Serve local directory without building an image:

```bash
docker run -it --rm \
  -p 8080:8080 \
  -v $(pwd)/docs:/app/__docs__ \
  docker.io/jberends/servemd:latest
```

### Method B: Custom Image (Production)

Build a standalone image with docs bundled:

```bash
# Copy Dockerfile template to your docs directory
cp Dockerfile.user-template /path/to/your/docs/Dockerfile
cd /path/to/your/docs/

# Build
docker build -t my-docs:latest .

# Run
docker run -p 8080:8080 my-docs:latest

# Push to registry
docker tag my-docs:latest docker.io/mycompany/docs:latest
docker push docker.io/mycompany/docs:latest
```

### Method C: Docker Compose

For more complex setups:

```bash
# Copy compose file
cp docker-compose.user.yml /path/to/your/docs/docker-compose.yml
cd /path/to/your/docs/

# Development mode (volume mount)
docker-compose --profile dev up

# Production mode (built image)
docker-compose --profile prod up -d --build
```

## 3. Kubernetes Deployment

### Quick k8s/k3s Deployment

```bash
# Copy and customize
cp k8s-simple.yaml my-docs-k8s.yaml

# Edit: Replace image with your image
vim my-docs-k8s.yaml

# Deploy
kubectl apply -f my-docs-k8s.yaml

# Port forward to test
kubectl port-forward svc/docs-server 8080:80

# Visit http://localhost:8080
```

## 4. Cloud Platform Deployment

### Heroku

```bash
# Create app
heroku create my-docs-server

# Deploy container
heroku container:push web -a my-docs-server
heroku container:release web -a my-docs-server

# Open
heroku open -a my-docs-server
```

### Railway

```bash
# Login
railway login

# Initialize
railway init

# Deploy
railway up
```

### Fly.io

```bash
# Launch
flyctl launch

# Deploy
flyctl deploy

# Open
flyctl open
```

## Directory Structure

Your documentation directory should have this structure:

```
my-documentation/
├── index.md          # Required: Homepage
├── sidebar.md        # Required: Left sidebar navigation
├── topbar.md         # Required: Top bar with title and links
├── llms.txt          # Optional: Custom AI assistant index
├── assets/           # Optional: Static assets
│   ├── logo.png
│   └── images/
├── guides/           # Your content
│   ├── getting-started.md
│   ├── installation.md
│   └── configuration.md
├── api/              # API documentation
│   └── reference.md
└── Dockerfile        # For Docker deployment (copy from template)
```

### Minimal Required Files

**`index.md`** (homepage):
```markdown
# Welcome

Get started with our documentation!

- [Getting Started](guides/getting-started.html)
- [API Reference](api/reference.html)
```

**`sidebar.md`** (navigation menu):
```markdown
# Navigation

## Guides
- [Getting Started](guides/getting-started.html)
- [Installation](guides/installation.html)

## Reference
- [API](api/reference.html)
```

**`topbar.md`** (top bar):
```markdown
# My Docs

[GitHub](https://github.com/mycompany/project) • [Support](mailto:support@mycompany.com)
```

## Configuration

All deployment methods support these environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DOCS_ROOT` | `/app/__docs__` | Path to documentation directory |
| `CACHE_ROOT` | `/app/__cache__` | Cache directory path |
| `PORT` | `8080` | Server port |
| `DEBUG` | `false` | Enable debug mode (auto-reload) |
| `BASE_URL` | Auto-detected | Base URL for absolute links (llms.txt & MCP) |
| `MCP_ENABLED` | `true` | Enable Model Context Protocol endpoint |
| `MCP_RATE_LIMIT_REQUESTS` | `120` | MCP rate limit (requests per window) |
| `MCP_RATE_LIMIT_WINDOW` | `60` | MCP rate limit window (seconds) |

### Examples

```bash
# Local with custom settings
DOCS_ROOT=./my-docs PORT=3000 DEBUG=true uvx --from servemd docs-server

# Docker with custom settings
docker run -p 3000:3000 \
  -e PORT=3000 \
  -e DEBUG=true \
  -e BASE_URL=https://docs.mycompany.com \
  -e MCP_ENABLED=true \
  -v $(pwd):/app/__docs__ \
  docker.io/jberends/servemd:latest

# Kubernetes (set in deployment YAML)
env:
- name: BASE_URL
  value: "https://docs.mycompany.com"
- name: DEBUG
  value: "false"
```

## Common Workflows

### Workflow 1: Development → Production

```bash
# 1. Develop locally with live reload
cd my-docs
DEBUG=true uvx --from servemd docs-server

# 2. Test with Docker locally
docker build -t my-docs:test .
docker run -p 8080:8080 my-docs:test

# 3. Push to registry
docker tag my-docs:test docker.io/mycompany/docs:latest
docker push docker.io/mycompany/docs:latest

# 4. Deploy to Kubernetes
kubectl set image deployment/docs-server \
  docs-server=docker.io/mycompany/docs:latest
```

### Workflow 2: Git-based CI/CD

```yaml
# .github/workflows/deploy.yml
name: Deploy Documentation

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build Docker image
        run: docker build -t docker.io/${{ github.repository }}/docs:${{ github.sha }} .
      
      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKERHUB_TOKEN }} | docker login docker.io -u ${{ secrets.DOCKERHUB_USERNAME }} --password-stdin
          docker push docker.io/${{ github.repository }}/docs:${{ github.sha }}
          docker tag docker.io/${{ github.repository }}/docs:${{ github.sha }} docker.io/${{ github.repository }}/docs:latest
          docker push docker.io/${{ github.repository }}/docs:latest
      
      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/docs-server docs-server=docker.io/${{ github.repository }}/docs:${{ github.sha }}
          kubectl rollout status deployment/docs-server
```

## Troubleshooting

### Issue: Required files missing

```
Error: index.md not found
```

**Solution**: Create the three required files:
```bash
touch index.md sidebar.md topbar.md
# Or use serve-docs-local.sh which creates them automatically
```

### Issue: Port already in use

```
Error: Address already in use
```

**Solution**: Use a different port:
```bash
PORT=3000 uvx --from servemd docs-server
```

### Issue: Docker volume permissions

```
Error: Permission denied
```

**Solution**: Check your volume mount:
```bash
# Use absolute path
docker run -v $(pwd):/app/__docs__ ...

# Or use named volume
docker run -v docs-data:/app/__docs__ ...
```

## Next Steps

- **[Full Documentation](../docs/index.md)** - Read the complete guide
- **[User Dockerfile Guide](../docs/deployment/user-dockerfile.md)** - Advanced Docker usage
- **[Kubernetes Guide](../docs/deployment/kubernetes.md)** - Production k8s deployment
- **[Cloud Platforms Guide](../docs/deployment/cloud-platforms.md)** - Deploy to Heroku, Railway, Fly.io, etc.

## Support

- **GitHub Issues**: Report bugs and request features
- **GitHub Discussions**: Ask questions and share ideas
- **Documentation**: Read the full documentation at http://localhost:8080 (after starting the server)
