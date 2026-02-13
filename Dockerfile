# =============================================================================
# ServeM Documentation Server - Multi-stage Dockerfile
# =============================================================================
# This Dockerfile builds a production-ready image for serving markdown docs.
# It uses multi-stage builds to keep the final image small and secure.
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Base Image with Dependencies
# -----------------------------------------------------------------------------
FROM python:3.13-bookworm AS base

# Set working directory
WORKDIR /app

# Security: Update packages and install only necessary dependencies
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install uv for faster dependency management
RUN pip install --no-cache-dir uv

# Copy dependency files for layer caching
COPY pyproject.toml uv.lock README.md ./

# Copy source code (needed for version detection during build)
COPY src/ ./src/

# Install Python dependencies
RUN uv sync --frozen --no-dev

# -----------------------------------------------------------------------------
# Stage 2: Application Image
# -----------------------------------------------------------------------------
FROM python:3.13-slim-bookworm AS app

# Security: Create non-root user
RUN groupadd -r servemd --gid=1000 && \
    useradd -r -g servemd --uid=1000 --home-dir=/app --shell=/sbin/nologin servemd

# Set working directory
WORKDIR /app

# Security: Update packages and install minimal runtime dependencies
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && apt-get autoremove -y

# Copy virtual environment and source from base stage
COPY --from=base --chown=servemd:servemd /app/.venv /app/.venv
COPY --from=base --chown=servemd:servemd /app/src /app/src

# =============================================================================
# DOCUMENTATION DIRECTORY SETUP
# =============================================================================
# DOCS_ROOT is where the server reads markdown files from.
# Default location: /app/__docs__
# 
# This can be:
# 1. Built into the image (COPY docs/ below) - for standalone images
# 2. Mounted at runtime (docker run -v ./docs:/app/__docs__) - for development
# =============================================================================

# Set DOCS_ROOT environment variable (where markdown files are read from)
ENV DOCS_ROOT=/app/__docs__

# Create the docs directory
RUN mkdir -p ${DOCS_ROOT} && chown servemd:servemd ${DOCS_ROOT}

# Copy documentation files into the image
# NOTE: This includes the example docs from the servemd repository.
# For production, replace this with your own documentation:
#   COPY ./my-docs/ /app/__docs__/
# Or mount a volume at runtime:
#   docker run -v $(pwd)/docs:/app/__docs__ servemd
COPY --chown=servemd:servemd docs/ ${DOCS_ROOT}/

# =============================================================================
# CACHE DIRECTORY SETUP
# =============================================================================
ENV CACHE_ROOT=/app/__cache__
RUN mkdir -p ${CACHE_ROOT} && chown servemd:servemd ${CACHE_ROOT}

# =============================================================================
# SERVER CONFIGURATION
# =============================================================================
ENV PYTHONPATH=/app/src
ENV PATH="/app/.venv/bin:$PATH"
ENV PORT=8080
ENV DEBUG=false

# Security: Run as non-root user
USER servemd

# Expose HTTP port
EXPOSE 8080

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Run the documentation server (exec form for security)
CMD ["python", "-m", "docs_server"]
