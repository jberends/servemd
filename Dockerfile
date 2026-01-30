# Use Python 3.13 on Debian Trixie
FROM python:3.13-trixie

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app/src
ENV DOCS_ROOT=/app/docs
ENV CACHE_ROOT=/app/cache
ENV PORT=8080
ENV DEBUG=false

# Install system dependencies (if needed for markdown processing)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml, uv.lock and README.md first for better layer caching
COPY pyproject.toml uv.lock README.md ./

# Install uv for faster dependency management
RUN pip install uv

# Install Python dependencies using uv
RUN uv sync --frozen

# Copy the source code
COPY src/ ./src/

# Copy the documentation content to /app/docs
COPY docs/ ./docs/

# Create cache directory
RUN mkdir -p /app/cache

# Activate virtual environment by updating PATH
ENV PATH="/app/.venv/bin:$PATH"

# Expose the port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["python", "-m", "docs_server"]
