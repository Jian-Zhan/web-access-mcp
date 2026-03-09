#!/bin/bash

# ============================================================
# Web Access MCP + SearXNG Docker Startup Script
# ============================================================
#
# IMPORTANT: You MUST modify the variables below before running!
#
# SEARXNG_SECRET: A random secret key for SearXNG session encryption
#   - Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
#
# SEARXNG_BASE_URL: (Optional) The public URL where SearXNG will be accessible
#   - This is the URL users will use to access SearXNG via reverse proxy
#   - Example: https://your-domain.com/searxng/
#   - Leave empty if not using reverse proxy
#
# ============================================================

set -e

# --- REQUIRED: Change these values! ---
SEARXNG_SECRET="your_secret_key_here_please_change_this"
SEARXNG_BASE_URL=""  # Optional: leave empty if not using reverse proxy

# --- Check if secret is changed ---
if [[ "$SEARXNG_SECRET" == "your_secret_key_here_please_change_this" ]]; then
    echo "ERROR: You must change SEARXNG_SECRET in this script!"
    echo "Generate a secret with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
    exit 1
fi

# --- Create searxng directory if not exists ---
mkdir -p searxng

# --- Generate settings.yml from template ---
echo "Generating SearXNG settings..."
cp searxng/settings.yml.template searxng/settings.yml

# Replace secret key
sed -i "s/SEARXNG_SECRET_PLACEHOLDER/${SEARXNG_SECRET}/g" searxng/settings.yml

# Handle base_url: replace placeholder with actual value or set to false
if [[ -n "$SEARXNG_BASE_URL" ]]; then
    sed -i "s|SEARXNG_BASE_URL_PLACEHOLDER|${SEARXNG_BASE_URL}|g" searxng/settings.yml
else
    sed -i 's/base_url: "SEARXNG_BASE_URL_PLACEHOLDER"/base_url: false/g' searxng/settings.yml
fi

# --- Set proper permissions ---
echo "Setting permissions..."
chmod -R 777 searxng/ 2>/dev/null || true

# --- Create network if not exists ---
docker network create web-access-net 2>/dev/null || true

# --- Start SearXNG ---
echo "Starting SearXNG..."
docker rm -f searxng 2>/dev/null || true
docker run -d \
  --name searxng \
  --network web-access-net \
  -p 8888:8080 \
  -v "$(pwd)/searxng:/etc/searxng:rw" \
  searxng/searxng:latest

# --- Build web-access-mcp ---
echo "Building web-access-mcp..."
docker build -t web-access-mcp .

# --- Start web-access-mcp ---
echo "Starting web-access-mcp..."
docker rm -f web-access-mcp 2>/dev/null || true
docker run -d \
  --name web-access-mcp \
  --network web-access-net \
  -p 4568:4568 \
  -e SEARXNG_MCP_URL=http://searxng:8080 \
  web-access-mcp

# --- Wait for services ---
echo "Waiting for services to start..."
sleep 5

# --- Show status ---
echo ""
echo "=== Services Status ==="
docker ps --filter "name=searxng" --filter "name=web-access-mcp" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "=== Access URLs ==="
echo "SearXNG:         http://localhost:8888"
echo "web-access-mcp:  http://localhost:4568/web-access-mcp"
echo ""
echo "=== Test SearXNG JSON API ==="
echo "curl -s 'http://localhost:8888/search?q=test&format=json' | jq '.results[0].title'"
echo ""
echo "To view logs:"
echo "  docker logs -f searxng"
echo "  docker logs -f web-access-mcp"
