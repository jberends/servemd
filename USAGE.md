# ServeMD Usage Guide

This document provides a quick overview of the best ways to use ServeMD as an end-user.

## 🎯 What's Your Use Case?

### 1. Quick Local Testing (30 seconds)

**You want to:** Quickly see how your docs look with ServeMD

**Solution:** Use uvx or Docker with volume mount

```bash
# Option A: uvx (fastest)
cd /path/to/your/docs
uvx --from servemd docs-server

# Option B: Docker
docker run -it --rm -p 8080:8080 -v $(pwd):/app/docs ghcr.io/yourusername/servemd:latest
```

Visit: http://localhost:8080

---

### 2. Local Development (2 minutes)

**You want to:** Write documentation with live preview and auto-reload

**Solution:** Use the provided shell script

```bash
# Copy the script
cp examples/serve-docs-local.sh /path/to/your/docs/
cd /path/to/your/docs/

# Run it
./serve-docs-local.sh

# Auto-reloads when you edit files!
```

Or manually:
```bash
DEBUG=true uvx --from servemd docs-server
```

**Guide:** [docs/deployment/local-development.md](docs/deployment/local-development.md)

---

### 3. Containerized Deployment (5 minutes)

**You want to:** Bundle your docs into a Docker image for deployment

**Solution:** Create a Dockerfile in your docs directory

```dockerfile
# Copy from examples/Dockerfile.user-template
FROM ghcr.io/yourusername/servemd:latest
COPY . /app/docs/
ENV BASE_URL=https://docs.yourcompany.com
```

```bash
# Build
docker build -t my-company-docs:latest .

# Run
docker run -p 8080:8080 my-company-docs:latest

# Push to registry
docker push ghcr.io/mycompany/docs:latest
```

**Guide:** [docs/deployment/user-dockerfile.md](docs/deployment/user-dockerfile.md)

---

### 4. Cloud Deployment (5-10 minutes)

**You want to:** Host your docs on a cloud platform

**Solutions:**

#### Heroku
```bash
heroku container:push web && heroku container:release web
```

#### Railway
```bash
railway init && railway up
```

#### Fly.io
```bash
flyctl launch && flyctl deploy
```

**Guide:** [docs/deployment/cloud-platforms.md](docs/deployment/cloud-platforms.md)

---

### 5. Kubernetes Deployment (10 minutes)

**You want to:** Deploy to k8s, k3s, or OpenShift

**Solution:** Use the provided Kubernetes manifest

```bash
# Copy and customize
cp examples/k8s-simple.yaml my-deployment.yaml

# Update image URL in the file
# Deploy
kubectl apply -f my-deployment.yaml
```

**Guide:** [docs/deployment/kubernetes.md](docs/deployment/kubernetes.md)

---

## 📁 What You Need

### Minimum Required Files

Your documentation directory needs these 3 files:

```
my-docs/
├── index.md          # Homepage (required)
├── sidebar.md        # Left navigation (required)
└── topbar.md         # Top bar (required)
```

### Complete Structure

For a full-featured documentation site:

```
my-docs/
├── index.md          # Homepage
├── sidebar.md        # Navigation menu
├── topbar.md         # Top bar with links
├── llms.txt          # Optional: AI assistant index
├── assets/           # Optional: Images, logos
│   └── logo.png
├── guides/           # Your content (any structure)
│   ├── getting-started.md
│   └── advanced.md
└── api/
    └── reference.md
```

---

## ⚙️ Configuration

All methods support these environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DOCS_ROOT` | `./docs` | Path to documentation directory |
| `PORT` | `8080` | Server port |
| `DEBUG` | `false` | Enable debug mode (auto-reload) |
| `BASE_URL` | Auto-detected | Base URL for absolute links |
| `CACHE_ROOT` | `./__cache__` | Cache directory |

**Examples:**

```bash
# Local with custom settings
DOCS_ROOT=./my-docs PORT=3000 DEBUG=true uvx --from servemd docs-server

# Docker
docker run -p 3000:3000 \
  -e PORT=3000 \
  -e DEBUG=true \
  -e BASE_URL=https://docs.mycompany.com \
  -v $(pwd):/app/docs \
  ghcr.io/yourusername/servemd:latest
```

---

## 🛠️ Ready-to-Use Resources

### Shell Scripts

- **`examples/serve-docs-local.sh`** - Local development server
  - Auto-creates required files if missing
  - Configurable port and directory
  - Pretty output with colors

### Docker Files

- **`examples/Dockerfile.user-template`** - Template for your custom image
  - Copy to your docs directory
  - Customize BASE_URL
  - Build and deploy

- **`examples/docker-compose.user.yml`** - Docker Compose setup
  - Development profile (volume mount)
  - Production profile (built image)
  - Health checks included

### Kubernetes

- **`examples/k8s-simple.yaml`** - Complete k8s deployment
  - Deployment with 2 replicas
  - Service (ClusterIP)
  - Ingress with TLS
  - Health checks and resource limits

---

## 📚 Documentation

### For End Users

1. **[Quick Start Guide](docs/quick-start-user.md)** - Overview of all options
2. **[Local Development](docs/deployment/local-development.md)** - Development workflow
3. **[User Dockerfile](docs/deployment/user-dockerfile.md)** - Docker deployment
4. **[Cloud Platforms](docs/deployment/cloud-platforms.md)** - Heroku, Railway, Fly.io, etc.
5. **[Kubernetes](docs/deployment/kubernetes.md)** - k8s/k3s deployment

### Core Documentation

- **[Configuration](docs/configuration.md)** - Environment variables
- **[Markdown Features](docs/features/markdown.md)** - What's supported
- **[Navigation](docs/features/navigation.md)** - Sidebar and topbar
- **[LLMs.txt](docs/features/llms-txt.md)** - AI assistant integration
- **[API Reference](docs/api/endpoints.md)** - HTTP endpoints

### Examples

Check **[examples/README.md](examples/README.md)** for practical examples and workflows.

---

## 🔄 Common Workflows

### Workflow 1: Development → Docker → Cloud

```bash
# 1. Develop locally
cd my-docs
DEBUG=true uvx --from servemd docs-server

# 2. Build Docker image
docker build -t my-docs:latest .

# 3. Test locally
docker run -p 8080:8080 my-docs:latest

# 4. Push to registry
docker push ghcr.io/mycompany/docs:latest

# 5. Deploy (example: Railway)
railway up
```

### Workflow 2: Git → CI/CD → Production

```bash
# 1. Commit docs
git add .
git commit -m "Update documentation"
git push

# 2. GitHub Actions builds and deploys automatically
# (See deployment guides for CI/CD examples)

# 3. Visit your production URL
curl https://docs.mycompany.com
```

### Workflow 3: Quick Local → k3s Edge

```bash
# 1. Test locally
uvx --from servemd docs-server

# 2. Build image
docker build -t my-docs:latest .

# 3. Push to local registry
docker tag my-docs:latest localhost:5000/docs:latest
docker push localhost:5000/docs:latest

# 4. Deploy to k3s
kubectl apply -f k8s-simple.yaml
```

---

## 🎓 Learning Path

### Beginner Path

1. Start with **Quick Local Testing** (uvx or Docker volume)
2. Read **[Quick Start Guide](docs/quick-start-user.md)**
3. Create your 3 required files
4. Explore **[Markdown Features](docs/features/markdown.md)**

### Intermediate Path

1. Use **serve-docs-local.sh** for development
2. Create a **Dockerfile** for your docs
3. Deploy to a **Cloud Platform** (Railway, Fly.io)
4. Set up **CI/CD** with GitHub Actions

### Advanced Path

1. Deploy to **Kubernetes** cluster
2. Set up **Helm chart** for reusability
3. Implement **GitOps** with ArgoCD
4. Configure **multi-region** deployment

---

## ❓ Quick Troubleshooting

### Missing Files Error

```
Error: index.md not found
```

**Fix:** Create the 3 required files or use `serve-docs-local.sh` (auto-creates them)

### Port In Use

```
Error: Address already in use
```

**Fix:** Use a different port: `PORT=3000 uvx --from servemd docs-server`

### Docker Permissions

```
Error: Permission denied
```

**Fix:** Use absolute paths: `docker run -v $(pwd):/app/docs ...`

### uvx Not Found

```
bash: uvx: command not found
```

**Fix:** Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`

---

## 🆘 Getting Help

- **📖 Full Documentation**: [docs/index.md](docs/index.md)
- **💡 Examples**: [examples/README.md](examples/README.md)
- **🐛 Issues**: GitHub Issues
- **💬 Discussions**: GitHub Discussions

---

## 🚀 Quick Commands Reference

```bash
# Local development
uvx --from servemd docs-server
DEBUG=true uvx --from servemd docs-server

# Docker - volume mount
docker run -it --rm -p 8080:8080 -v $(pwd):/app/docs ghcr.io/yourusername/servemd:latest

# Docker - build custom image
docker build -t my-docs:latest .
docker run -p 8080:8080 my-docs:latest

# Kubernetes
kubectl apply -f k8s-simple.yaml
kubectl port-forward svc/docs-server 8080:80

# Cloud platforms
heroku container:push web && heroku container:release web  # Heroku
railway up                                                  # Railway
flyctl deploy                                               # Fly.io
```

---

## 📦 What Was Created

This guide references these new files:

### Documentation
- `docs/quick-start-user.md` - Complete end-user guide
- `docs/deployment/local-development.md` - Local development guide
- `docs/deployment/user-dockerfile.md` - Docker deployment guide
- `docs/deployment/cloud-platforms.md` - Cloud platform guides
- `docs/deployment/kubernetes.md` - Kubernetes deployment guide

### Examples
- `examples/serve-docs-local.sh` - Local serving script
- `examples/Dockerfile.user-template` - User Dockerfile template
- `examples/docker-compose.user.yml` - Docker Compose setup
- `examples/k8s-simple.yaml` - Kubernetes manifest
- `examples/README.md` - Examples overview

### Updated Files
- `README.md` - Added end-user quick start section
- `docs/sidebar.md` - Added end-user guides section

---

**Happy Documenting! 🎉**
