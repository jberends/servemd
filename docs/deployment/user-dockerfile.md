# User Dockerfile Template

This guide shows how to create a custom Docker image for your documentation project.

## Use Case

You have a documentation directory with your markdown files and want to create a standalone Docker image that bundles everything together.

## Directory Structure

```
my-documentation/
├── index.md
├── sidebar.md
├── topbar.md
├── features/
│   ├── feature1.md
│   └── feature2.md
├── guides/
│   └── guide1.md
└── Dockerfile          # ← Add this
```

## Dockerfile Template

Create a `Dockerfile` in your documentation directory:

```dockerfile
# Use the official servemd image as base
FROM ghcr.io/yourusername/servemd:latest

# Copy your documentation into the container
COPY . /app/docs/

# The base image already has:
# - DOCS_ROOT=/app/docs
# - PORT=8080
# - All dependencies installed
# - CMD to start the server

# Optional: Override environment variables
# ENV BASE_URL=https://docs.yourcompany.com
# ENV DEBUG=false

# That's it! Your docs are now bundled in the image
```

## Build & Run

```bash
# Build your custom image
docker build -t my-company-docs:latest .

# Run it
docker run -p 8080:8080 my-company-docs:latest

# Visit http://localhost:8080
```

## Advanced: Multi-stage Build

For optimal image size, use a multi-stage build:

```dockerfile
# Stage 1: Prepare documentation
FROM alpine:latest AS docs-builder
WORKDIR /docs
COPY . .
# Optional: Run any preprocessing here (e.g., generate additional pages)

# Stage 2: Final image
FROM ghcr.io/yourusername/servemd:latest
COPY --from=docs-builder /docs /app/docs/

# Optional: Set production URL
ENV BASE_URL=https://docs.yourcompany.com
ENV DEBUG=false
```

## Deployment Examples

### Docker Hub

```bash
# Build and tag
docker build -t mycompany/docs:latest .
docker build -t mycompany/docs:v1.0.0 .

# Push to Docker Hub
docker push mycompany/docs:latest
docker push mycompany/docs:v1.0.0

# Pull and run anywhere
docker pull mycompany/docs:latest
docker run -p 8080:8080 mycompany/docs:latest
```

### GitHub Container Registry

```bash
# Tag for GHCR
docker tag my-company-docs:latest ghcr.io/mycompany/docs:latest

# Login and push
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
docker push ghcr.io/mycompany/docs:latest
```

### DigitalOcean Container Registry

```bash
# Tag for DO
docker tag my-company-docs:latest registry.digitalocean.com/myregistry/docs:latest

# Push
doctl registry login
docker push registry.digitalocean.com/myregistry/docs:latest
```

## CI/CD Integration

### GitHub Actions

Create `.github/workflows/deploy-docs.yml`:

```yaml
name: Deploy Documentation

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build Docker image
        run: docker build -t ghcr.io/${{ github.repository }}/docs:${{ github.sha }} .
      
      - name: Login to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Push image
        run: |
          docker push ghcr.io/${{ github.repository }}/docs:${{ github.sha }}
          docker tag ghcr.io/${{ github.repository }}/docs:${{ github.sha }} ghcr.io/${{ github.repository }}/docs:latest
          docker push ghcr.io/${{ github.repository }}/docs:latest
```

## Next Steps

- **[Kubernetes Deployment](./kubernetes.md)** - Deploy to k3s or k8s
- **[Cloud Platforms](./cloud-platforms.md)** - Heroku, Railway, Fly.io
- **[Configuration](../configuration.md)** - Environment variables
