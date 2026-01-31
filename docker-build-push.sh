#!/bin/bash
# Build and push Docker images for amd64 using buildx
# Usage: ./docker-build-push.sh [version]

set -e  # Exit on error

# Get version from argument or read from __init__.py
if [ -n "$1" ]; then
    VERSION="$1"
else
    VERSION=$(grep -oP "__version__ = \"\K[^\"]*" src/docs_server/__init__.py 2>/dev/null || echo "0.1.0")
fi

echo "🔨 Building servemd:${VERSION} for linux/amd64..."

# Ensure buildx is available
if ! docker buildx version &> /dev/null; then
    echo "❌ Docker buildx not available. Please update Docker Desktop."
    exit 1
fi

# Create and use buildx builder if not exists
if ! docker buildx inspect multiarch &> /dev/null; then
    echo "📦 Creating buildx builder..."
    docker buildx create --name multiarch --use
else
    docker buildx use multiarch
fi

# Build and push for amd64 only
echo "🚀 Building for linux/amd64..."
docker buildx build \
    --platform linux/amd64 \
    --tag jberends/servemd:${VERSION} \
    --tag jberends/servemd:latest \
    --push \
    .

# Optionally push to GHCR (uncomment if logged in)
# docker buildx build \
#     --platform linux/amd64 \
#     --tag ghcr.io/jberends/servemd:${VERSION} \
#     --tag ghcr.io/jberends/servemd:latest \
#     --push \
#     .

echo ""
echo "✅ Successfully built and pushed to Docker Hub:"
echo "     - jberends/servemd:${VERSION}"
echo "     - jberends/servemd:latest"
echo ""
echo "🔍 Verify:"
echo "  docker pull jberends/servemd:${VERSION}"
echo "  docker run -p 8080:8080 -v \$(pwd)/docs:/app/__docs__ jberends/servemd:${VERSION}"
echo ""
echo "💡 To also push to GHCR:"
echo "  1. Login: echo \$GITHUB_TOKEN | docker login ghcr.io -u jberends --password-stdin"
echo "  2. Uncomment GHCR section in this script"
