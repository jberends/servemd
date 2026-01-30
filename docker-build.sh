#!/bin/bash
# Build script for ServeMD Documentation Server Docker image

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🐳 Building ServeMD Documentation Server Docker image...${NC}"

# Build the Docker image
echo -e "${YELLOW}📦 Building Docker image 'servemd'...${NC}"
docker build -t servemd .

echo -e "${GREEN}✅ Docker image 'servemd' built successfully!${NC}"
echo -e "${YELLOW}🚀 To run the container:${NC}"
echo -e "   docker run -p 8080:8080 servemd"
echo -e "${YELLOW}📖 Then visit:${NC}"
echo -e "   http://localhost:8080"
echo -e "   http://localhost:8080/health"
