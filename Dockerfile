# Web Access MCP Server Dockerfile
# 
# Provides web fetch, screenshot, search capabilities via MCP protocol
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
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Required for Playwright
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2t64 \
    libpango-1.0-0 \
    libcairo2 \
    # Required for X11/Playwright
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxext6 \
    # Required for lxml
    libxml2 \
    libxslt1.1 \
    # Clean up
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
RUN useradd --create-home --shell /bin/bash appuser

# Install Playwright browsers to global path and set ownership
RUN playwright install chromium && \
    playwright install-deps chromium && \
    chown -R appuser:appuser /ms-playwright && \
    chown -R appuser:appuser /app

# Verify Playwright installation
USER appuser
RUN python -c "from playwright.sync_api import sync_playwright; print('Playwright installed successfully')"

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
