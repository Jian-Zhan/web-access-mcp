# Web Access MCP Server Dockerfile
# 
# Provides web fetch, search capabilities via MCP protocol
#
# Build: docker build -t web-access-mcp .
# Run: docker run -p 4568:4568 web-access-mcp

FROM python:3.12-slim

LABEL maintainer="web-access-mcp"
LABEL description="Streamable HTTP MCP Server with web access tools and SearXNG search integration"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2 \
    libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy project files
COPY pyproject.toml ./
COPY web_access_mcp/ ./web_access_mcp/
COPY README.md ./

# Install Python dependencies
RUN pip install --no-cache-dir .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app

# Expose port
EXPOSE 4568

# Default environment variables
ENV WEB_ACCESS_TIMEOUT=30 \
    WEB_ACCESS_MAX_SIZE=10000000 \
    WEB_ACCESS_RETRY_COUNT=3 \
    WEB_ACCESS_RETRY_BACKOFF=1.0 \
    SEARXNG_MCP_URL=http://searxng:8080

# Run the server
CMD ["python", "-m", "web_access_mcp.server"]
