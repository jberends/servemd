#!/bin/bash
# serve-docs-local.sh - Serve documentation locally with servemd
# Usage: ./serve-docs-local.sh [docs-directory] [port]

set -e

# Configuration
DOCS_DIR="${1:-.}"
PORT="${2:-${PORT:-8080}}"
DEBUG="${DEBUG:-true}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${YELLOW}╔════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║     ServeMD Documentation Server          ║${NC}"
echo -e "${YELLOW}╚════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📁 Documentation: ${GREEN}${DOCS_DIR}${NC}"
echo -e "${BLUE}🌐 Port:          ${GREEN}${PORT}${NC}"
echo -e "${BLUE}🐛 Debug mode:    ${GREEN}${DEBUG}${NC}"
echo ""

# Check if uv is installed
if ! command -v uvx &> /dev/null; then
    echo -e "${YELLOW}⚠️  uvx not found. Installing uv...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo -e "${GREEN}✅ uv installed successfully!${NC}"
    echo -e "${YELLOW}💡 You may need to restart your shell or run: source ~/.bashrc${NC}"
    echo ""
fi

# Check if required files exist
if [ ! -f "${DOCS_DIR}/index.md" ]; then
    echo -e "${YELLOW}⚠️  Warning: ${DOCS_DIR}/index.md not found${NC}"
    echo -e "${YELLOW}💡 Creating minimal example files...${NC}"
    
    # Create index.md
    cat > "${DOCS_DIR}/index.md" <<EOF
# Welcome to Your Documentation

This is a minimal documentation site served by ServeM.

## Getting Started

Edit this file (\`index.md\`) to customize your homepage.

## Features

- ✨ Beautiful design
- 🚀 Fast rendering
- 📱 Mobile responsive
- 🤖 AI-friendly (llms.txt)
EOF

    # Create sidebar.md if missing
    if [ ! -f "${DOCS_DIR}/sidebar.md" ]; then
        cat > "${DOCS_DIR}/sidebar.md" <<EOF
# Navigation

- [Home](index.html)
- [Documentation](index.html)
EOF
    fi

    # Create topbar.md if missing
    if [ ! -f "${DOCS_DIR}/topbar.md" ]; then
        cat > "${DOCS_DIR}/topbar.md" <<EOF
# My Documentation

[GitHub](https://github.com/yourusername/project)
EOF
    fi

    echo -e "${GREEN}✅ Created example files!${NC}"
    echo ""
fi

echo -e "${YELLOW}🚀 Starting server...${NC}"
echo ""

# Run with uvx
DOCS_ROOT="$DOCS_DIR" \
PORT="$PORT" \
DEBUG="$DEBUG" \
uvx --from servemd docs-server &

SERVER_PID=$!

# Wait for server to start
sleep 2

if ps -p $SERVER_PID > /dev/null; then
    echo ""
    echo -e "${GREEN}✅ Server started successfully!${NC}"
    echo ""
    echo -e "${YELLOW}╔════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║     Your documentation is now live!       ║${NC}"
    echo -e "${YELLOW}╚════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}🌐 Open in browser:${NC}"
    echo -e "   ${GREEN}http://localhost:${PORT}${NC}"
    echo -e "   ${GREEN}http://localhost:${PORT}/health${NC}"
    echo ""
    echo -e "${BLUE}📝 Edit your files and refresh to see changes${NC}"
    echo -e "${BLUE}⏹️  Press Ctrl+C to stop the server${NC}"
    echo ""
    
    # Wait for Ctrl+C
    wait $SERVER_PID
else
    echo -e "${RED}❌ Failed to start server!${NC}"
    exit 1
fi
