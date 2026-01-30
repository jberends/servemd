# Quick Start for End Users

Get your documentation site running in under 5 minutes!

## I Want To...

### 🏃‍♂️ Quickly Test Locally (30 seconds)

Perfect for: Trying out servemd with your existing docs.

```bash
# Option 1: Using uvx (recommended - no installation needed)
cd /path/to/your/docs
uvx --from servemd docs-server

# Option 2: Using Docker
docker run -it --rm -p 8080:8080 -v $(pwd):/app/docs ghcr.io/yourusername/servemd:latest
```

Visit: **http://localhost:8080**

**Requirements**: Your docs directory needs:
- `index.md` (homepage)
- `sidebar.md` (navigation)
- `topbar.md` (top bar)

---

### 📦 Deploy My Docs as a Docker Image (5 minutes)

Perfect for: Production deployment, CI/CD, Kubernetes.

**Step 1**: Create `Dockerfile` in your docs directory:

```dockerfile
FROM ghcr.io/yourusername/servemd:latest
COPY . /app/docs/
ENV BASE_URL=https://docs.yourcompany.com
```

**Step 2**: Build and run:

```bash
# Build
docker build -t my-company-docs:latest .

# Run
docker run -p 8080:8080 my-company-docs:latest

# Push to registry
docker tag my-company-docs:latest ghcr.io/mycompany/docs:latest
docker push ghcr.io/mycompany/docs:latest
```

**[Full guide →](./deployment/user-dockerfile.md)**

---

### 🖥️ Use Locally for Development (2 minutes)

Perfect for: Writing documentation with live preview.

**Create `serve-docs.sh`**:

```bash
#!/bin/bash
DOCS_ROOT="${1:-.}" PORT="${PORT:-8080}" DEBUG=true uvx --from servemd docs-server
```

**Usage**:

```bash
chmod +x serve-docs.sh
./serve-docs.sh

# Custom directory
./serve-docs.sh ./my-docs

# Custom port
PORT=3000 ./serve-docs.sh
```

**[Full guide →](./deployment/local-development.md)**

---

### ☁️ Deploy to Cloud Platform (5-10 minutes)

Perfect for: Hosting publicly accessible documentation.

#### Heroku

```bash
heroku create my-docs
heroku container:push web
heroku container:release web
```

#### Railway

```bash
railway init
railway up
```

#### Fly.io

```bash
flyctl launch
flyctl deploy
```

**[Full guide →](./deployment/cloud-platforms.md)**

---

### ⚙️ Deploy to Kubernetes/k3s (10 minutes)

Perfect for: Self-hosted, enterprise deployments.

```bash
# Quick k3s deployment
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: docs-server
spec:
  replicas: 2
  selector:
    matchLabels:
      app: docs-server
  template:
    metadata:
      labels:
        app: docs-server
    spec:
      containers:
      - name: docs-server
        image: ghcr.io/mycompany/docs:latest
        ports:
        - containerPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: docs-server
spec:
  selector:
    app: docs-server
  ports:
  - port: 80
    targetPort: 8080
EOF
```

**[Full guide →](./deployment/kubernetes.md)**

---

## Common Patterns

### Pattern 1: Development → Production Workflow

```bash
# 1. Develop locally with live reload
DEBUG=true uvx --from servemd docs-server

# 2. Build Docker image
docker build -t my-docs:latest .

# 3. Test production build locally
docker run -p 8080:8080 my-docs:latest

# 4. Push to registry
docker push ghcr.io/mycompany/docs:latest

# 5. Deploy to production
kubectl set image deployment/docs-server docs-server=ghcr.io/mycompany/docs:latest
```

### Pattern 2: Git-based Deployment

```bash
# Create docs repository
git init
git add .
git commit -m "Initial docs"
git push

# Deploy automatically via GitHub Actions
# (See CI/CD examples in deployment guides)
```

### Pattern 3: Multi-environment Setup

```bash
# Development
DOCS_ROOT=./docs DEBUG=true uvx --from servemd docs-server

# Staging
docker run -p 8080:8080 -e BASE_URL=https://staging-docs.com my-docs:staging

# Production
docker run -p 8080:8080 -e BASE_URL=https://docs.com my-docs:latest
```

---

## Directory Structure

Your documentation directory should look like this:

```
my-documentation/
├── index.md          # Required: Homepage
├── sidebar.md        # Required: Navigation menu
├── topbar.md         # Required: Top bar links
├── llms.txt          # Optional: AI assistant index
├── assets/           # Optional: Images, logos, etc.
│   └── logo.png
├── guides/           # Your content
│   ├── getting-started.md
│   └── advanced.md
├── api/              # API documentation
│   └── reference.md
└── Dockerfile        # For containerized deployment
```

### Minimal Example Files

**`index.md`**:
```markdown
# Welcome to Our Documentation

Get started with our product in minutes!

- [Quick Start](guides/getting-started.html)
- [API Reference](api/reference.html)
```

**`sidebar.md`**:
```markdown
# Navigation

## Getting Started
- [Introduction](index.html)
- [Installation](guides/getting-started.html)

## API
- [Reference](api/reference.html)
```

**`topbar.md`**:
```markdown
# My Documentation

[GitHub](https://github.com/mycompany/product) • [Support](https://support.mycompany.com)
```

---

## Configuration

Configure via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DOCS_ROOT` | `./docs` | Path to documentation directory |
| `PORT` | `8080` | Server port |
| `DEBUG` | `false` | Enable debug mode (auto-reload) |
| `BASE_URL` | Auto-detected | Base URL for absolute links |
| `CACHE_ROOT` | `./__cache__` | Cache directory path |

Examples:

```bash
# Local development
DOCS_ROOT=./my-docs PORT=3000 DEBUG=true uvx --from servemd docs-server

# Docker
docker run -p 8080:8080 \
  -e BASE_URL=https://docs.mycompany.com \
  -e DEBUG=false \
  my-docs:latest
```

**[Full configuration guide →](./configuration.md)**

---

## Troubleshooting

### Required Files Missing

```
Error: index.md, sidebar.md, or topbar.md not found
```

**Solution**: Create the three required files in your `DOCS_ROOT`:
```bash
touch index.md sidebar.md topbar.md
```

### Port Already in Use

```
Error: Address already in use
```

**Solution**: Use a different port:
```bash
PORT=3000 uvx --from servemd docs-server
```

### Docker Volume Issues

```
Error: Permission denied
```

**Solution**: Check volume mount paths:
```bash
# Correct
docker run -v $(pwd):/app/docs ...

# Also works
docker run -v /absolute/path/to/docs:/app/docs ...
```

---

## Next Steps

Choose your deployment method:

1. **[Local Development Guide](./deployment/local-development.md)** - uvx, pipx, Docker volumes
2. **[Docker Image Guide](./deployment/user-dockerfile.md)** - Build custom images
3. **[Cloud Platforms](./deployment/cloud-platforms.md)** - Heroku, Railway, Fly.io, etc.
4. **[Kubernetes](./deployment/kubernetes.md)** - k8s, k3s, Helm charts

---

## Getting Help

- **📖 Documentation**: Read the [full documentation](./index.html)
- **🐛 Issues**: Report bugs on [GitHub Issues](https://github.com/yourusername/servemd/issues)
- **💬 Discussions**: Ask questions in [GitHub Discussions](https://github.com/yourusername/servemd/discussions)
- **💼 Commercial Support**: Contact [support@yourcompany.com](mailto:support@yourcompany.com)
