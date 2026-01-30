#!/bin/bash
# Run script for ServeMD Documentation Server Docker container

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

IMAGE_NAME="servemd"
CONTAINER_NAME="servemd-server"
PORT="8080"

echo -e "${YELLOW}🐳 Starting ServeMD Documentation Server...${NC}"

# Stop and remove existing container if it exists
if docker ps -a --format 'table {{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${YELLOW}🛑 Stopping existing container...${NC}"
    docker stop ${CONTAINER_NAME} >/dev/null 2>&1 || true
    docker rm ${CONTAINER_NAME} >/dev/null 2>&1 || true
fi

# Check if image exists
if ! docker images --format 'table {{.Repository}}' | grep -q "^${IMAGE_NAME}$"; then
    echo -e "${RED}❌ Docker image '${IMAGE_NAME}' not found!${NC}"
    echo -e "${YELLOW}💡 Run './docker-build.sh' first to build the image.${NC}"
    exit 1
fi

# Run the container
echo -e "${YELLOW}🚀 Starting container '${CONTAINER_NAME}'...${NC}"
docker run -d \
    --name ${CONTAINER_NAME} \
    -p ${PORT}:8080 \
    ${IMAGE_NAME}

# Wait a moment for the server to start
sleep 3

# Check if container is running
if docker ps --format 'table {{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${GREEN}✅ Container started successfully!${NC}"
    echo -e "${YELLOW}📖 Documentation server is available at:${NC}"
    echo -e "   http://localhost:${PORT}"
    echo -e "   http://localhost:${PORT}/health"
    echo -e "${YELLOW}🔍 To view logs:${NC}"
    echo -e "   docker logs -f ${CONTAINER_NAME}"
    echo -e "${YELLOW}🛑 To stop:${NC}"
    echo -e "   docker stop ${CONTAINER_NAME}"
else
    echo -e "${RED}❌ Failed to start container!${NC}"
    echo -e "${YELLOW}🔍 Check logs:${NC}"
    echo -e "   docker logs ${CONTAINER_NAME}"
    exit 1
fi
