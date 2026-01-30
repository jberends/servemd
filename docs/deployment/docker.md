# Docker Deployment

Deploy the documentation server with Docker for production use.

## Quick Start

```bash
# Build the image
docker build -t markdown-docs-server .

# Run with your docs
docker run -d \
  -p 8080:8080 \
  -v $(pwd)/docs:/app/docs \
  --name docs-server \
  markdown-docs-server
```

Visit http://localhost:8080

---

## Dockerfile

The included Dockerfile is production-optimized:

```dockerfile
FROM python:3.13-slim

# Install uv
RUN pip install --no-cache-dir uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --no-dev

# Copy source code
COPY src/ ./src/

# Create directories
RUN mkdir -p /app/docs /app/cache

# Default environment variables
ENV DOCS_ROOT=/app/docs
ENV CACHE_ROOT=/app/cache
ENV PORT=8080

# Expose port
EXPOSE 8080

# Run server
CMD ["uv", "run", "python", "-m", "docs_server"]
```

**Features:**
- Python 3.13 slim base
- Multi-stage build for minimal size
- Non-root user (TODO: add in production)
- Caching layers for fast rebuilds
- Healthcheck support

---

## Building

### Basic Build

```bash
docker build -t my-docs .
```

### With Build Args

```bash
docker build \
  --build-arg PYTHON_VERSION=3.13 \
  -t my-docs:v1.0.0 \
  .
```

### Multi-Platform

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t my-docs:latest \
  .
```

---

## Running

### Development

```bash
docker run -it \
  -p 8080:8080 \
  -v $(pwd)/docs:/app/docs \
  -e DEBUG=true \
  markdown-docs-server
```

### Production

```bash
docker run -d \
  --name docs-server \
  -p 8080:8080 \
  -v /var/www/docs:/app/docs:ro \
  -e BASE_URL=https://docs.mysite.com \
  -e DEBUG=false \
  --restart unless-stopped \
  --memory=512m \
  --cpus=1 \
  markdown-docs-server
```

### With Environment File

```bash
# Create .env file
cat > .env <<EOF
DOCS_ROOT=/app/docs
BASE_URL=https://docs.example.com
DEBUG=false
PORT=8080
EOF

# Run with env file
docker run -d \
  --env-file .env \
  -p 8080:8080 \
  -v $(pwd)/docs:/app/docs \
  markdown-docs-server
```

---

## Docker Compose

### Basic Setup

```yaml
version: '3.8'

services:
  docs:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - ./docs:/app/docs:ro
    environment:
      - BASE_URL=https://docs.mysite.com
      - DEBUG=false
    restart: unless-stopped
```

### With Reverse Proxy

```yaml
version: '3.8'

services:
  docs:
    build: .
    expose:
      - "8080"
    volumes:
      - ./docs:/app/docs:ro
    environment:
      - BASE_URL=https://docs.mysite.com
    restart: unless-stopped
    networks:
      - web

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - docs
    networks:
      - web

networks:
  web:
```

### With Health Checks

```yaml
version: '3.8'

services:
  docs:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - ./docs:/app/docs:ro
    environment:
      - BASE_URL=https://docs.mysite.com
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped
```

---

## Volume Mounts

### Read-Only Docs

```bash
docker run -v $(pwd)/docs:/app/docs:ro markdown-docs-server
```

### Persistent Cache

```bash
docker run \
  -v $(pwd)/docs:/app/docs:ro \
  -v docs-cache:/app/cache \
  markdown-docs-server
```

### Assets Only

```bash
docker run \
  -v $(pwd)/docs:/app/docs:ro \
  -v $(pwd)/assets:/app/docs/assets:ro \
  markdown-docs-server
```

---

## Environment Variables

```bash
docker run \
  -e DOCS_ROOT=/app/docs \
  -e CACHE_ROOT=/app/cache \
  -e BASE_URL=https://docs.example.com \
  -e DEBUG=false \
  -e PORT=8080 \
  -p 8080:8080 \
  markdown-docs-server
```

See [Environment Variables](environment.md) for complete reference.

---

## Networking

### Host Network

```bash
docker run --network host markdown-docs-server
```

### Custom Network

```bash
# Create network
docker network create docs-net

# Run container
docker run --network docs-net markdown-docs-server
```

### Link to Other Containers

```bash
docker run \
  --link database:db \
  --link redis:cache \
  markdown-docs-server
```

---

## Resource Limits

### Memory Limit

```bash
docker run --memory=512m markdown-docs-server
```

### CPU Limit

```bash
docker run --cpus=1.5 markdown-docs-server
```

### Combined

```bash
docker run \
  --memory=512m \
  --cpus=1 \
  --memory-swap=1g \
  markdown-docs-server
```

---

## Production Best Practices

### 1. Use Specific Tags

```bash
# Bad
docker pull markdown-docs-server:latest

# Good
docker pull markdown-docs-server:v1.0.0
```

### 2. Read-Only Volumes

```bash
-v $(pwd)/docs:/app/docs:ro
```

### 3. Health Checks

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

### 4. Restart Policies

```bash
--restart unless-stopped
```

### 5. Logging

```bash
docker run \
  --log-driver json-file \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  markdown-docs-server
```

### 6. Security

```bash
# Run as non-root (add to Dockerfile)
USER nobody

# Drop capabilities
--cap-drop=ALL
```

---

## Monitoring

### View Logs

```bash
# Real-time logs
docker logs -f docs-server

# Last 100 lines
docker logs --tail 100 docs-server

# Since timestamp
docker logs --since 2024-01-01T00:00:00 docs-server
```

### Container Stats

```bash
docker stats docs-server
```

### Health Check

```bash
docker inspect --format='{{json .State.Health}}' docs-server | jq
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs docs-server

# Inspect container
docker inspect docs-server

# Check if port is in use
docker ps | grep 8080
```

### Permission Issues

```bash
# Check volume mounts
docker inspect docs-server | jq '.[0].Mounts'

# Fix permissions
chmod -R 755 docs/
```

### Out of Memory

```bash
# Increase memory limit
docker update --memory=1g docs-server

# Or restart with new limit
docker stop docs-server
docker run --memory=1g ...
```

---

## Updating

### Rolling Update

```bash
# Pull new image
docker pull markdown-docs-server:latest

# Stop old container
docker stop docs-server
docker rm docs-server

# Start new container
docker run -d \
  --name docs-server \
  -p 8080:8080 \
  -v $(pwd)/docs:/app/docs \
  markdown-docs-server:latest
```

### Zero-Downtime Update

Use Docker Compose:

```bash
docker-compose up -d --no-deps --build docs
```

---

## Clean Up

### Remove Container

```bash
docker stop docs-server
docker rm docs-server
```

### Remove Image

```bash
docker rmi markdown-docs-server
```

### Clean All

```bash
docker system prune -a
```

---

## Next Steps

- **[Environment Variables](environment.md)** - Configuration reference
- **[Production Tips](production.md)** - Optimization guide
- **[Examples](../examples/advanced.md)** - Advanced configurations
