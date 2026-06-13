# Web Access MCP

Streamable HTTP MCP Server providing web access tools and SearXNG search integration.

## Features

- **web_fetch_tool** - Fetch web pages and convert to Markdown
- **extract_links_tool** - Extract all links from a web page
- **extract_metadata_tool** - Extract metadata from web pages
- **web_search_tool** - Search the web using SearXNG
- **image_search_tool** - Search for images
- **news_search_tool** - Search for news articles
- **video_search_tool** - Search for videos

## Quick Start with Docker

### 1. Prerequisites

- Docker installed

### 2. Configure and Start

**IMPORTANT**: Before running, you MUST edit `start_docker.sh` and change these values:

```bash
# Generate a secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Edit start_docker.sh
nano start_docker.sh
```

Change these lines:

```bash
SEARXNG_SECRET="your_generated_secret_key_here"  # REQUIRED!
SEARXNG_BASE_URL="https://your-domain.com/searxng/"  # Optional, leave empty if not using reverse proxy
```

### 3. Run

```bash
chmod +x start_docker.sh
./start_docker.sh
```

The script will:
1. Check if you've changed the required values
2. Generate SearXNG settings.yml from template
3. Create Docker network
4. Start SearXNG on port 8888
5. Build and start web-access-mcp on port 4568
### 4. Verify

```bash
# Check services
docker ps

# Test SearXNG HTML
curl http://localhost:8888/

# Test SearXNG JSON API (should return search results)
curl -s "http://localhost:8888/search?q=test&format=json" | head -c 200

# Test web-access-mcp
curl -X POST http://localhost:4568/web-access-mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

## Access URLs

| Service | Local URL |
|---------|-----------|
| SearXNG | http://localhost:8888 |
| web-access-mcp | http://localhost:4568/web-access-mcp |

## Usage Examples

### List Available Tools

```bash
curl -X POST http://localhost:4568/web-access-mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

### Fetch a Web Page

```bash
curl -X POST http://localhost:4568/web-access-mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "jsonrpc":"2.0",
    "id":2,
    "method":"tools/call",
    "params":{
      "name":"web_fetch_tool",
      "arguments":{"url":"https://example.com"}
    }
  }'
```

### Search the Web

```bash
curl -X POST http://localhost:4568/web-access-mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "jsonrpc":"2.0",
    "id":3,
    "method":"tools/call",
    "params":{
      "name":"web_search_tool",
      "arguments":{"query":"python tutorial","max_results":5}
    }
  }'
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SEARXNG_MCP_URL` | SearXNG URL for web-access-mcp | `http://searxng:8080` |
| `WEB_ACCESS_TIMEOUT` | Request timeout (seconds) | `30` |
| `WEB_ACCESS_RETRY_COUNT` | Number of retries | `3` |

### SearXNG Configuration

Edit `searxng/settings.yml` to customize:
- Search engines
- Safe search
- Languages
- UI theme

## Apache2 Reverse Proxy

To expose the services publicly via Apache2, create a virtual host configuration:

### 1. Enable Required Modules

```bash
sudo a2enmod proxy proxy_http proxy_wstunnel ssl rewrite headers
sudo systemctl restart apache2
```

### 2. Create Virtual Host

Create `/etc/apache2/sites-available/web-access.conf`:

```apache
<VirtualHost *:80>
    ServerName your-domain.com

    # Redirect HTTP to HTTPS
    RewriteEngine On
    RewriteCond %{HTTPS} off
    RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
</VirtualHost>

<VirtualHost *:443>
    ServerName your-domain.com

    # SSL Configuration (use Let's Encrypt or your certificate)
    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/your-domain.com/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/your-domain.com/privkey.pem

    # Security headers
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set X-XSS-Protection "1; mode=block"

    # SearXNG (http://localhost:8888)
    # Access: https://your-domain.com/searxng/
    ProxyPreserveHost On
    ProxyPass /searxng/ http://127.0.0.1:8888/
    ProxyPassReverse /searxng/ http://127.0.0.1:8888/

    # web-access-mcp (http://localhost:4568)
    # Access: https://your-domain.com/web-access-mcp
    ProxyPass /web-access-mcp http://127.0.0.1:4568/web-access-mcp
    ProxyPassReverse /web-access-mcp http://127.0.0.1:4568/web-access-mcp

    # WebSocket support for MCP Streamable HTTP
    RewriteEngine On
    RewriteCond %{HTTP:Upgrade} =websocket [NC]
    RewriteCond %{HTTP:Connection} upgrade [NC]
    RewriteRule ^/web-access-mcp$ ws://127.0.0.1:4568/web-access-mcp [P,L]

    # Logging
    ErrorLog ${APACHE_LOG_DIR}/web-access-error.log
    CustomLog ${APACHE_LOG_DIR}/web-access-access.log combined
</VirtualHost>
```

### 3. Enable Site and Restart

```bash
sudo a2ensite web-access
sudo systemctl restart apache2
```

### 4. Update SearXNG Base URL

Edit `start_docker.sh` to set your public URL:

```bash
SEARXNG_BASE_URL="https://your-domain.com/searxng/"
```

Then restart services:

```bash
docker stop searxng web-access-mcp
./start_docker.sh
```
### 5. Firewall (Optional)

Allow HTTP/HTTPS through firewall:

```bash
sudo ufw allow 'Apache Full'
```

### Public URLs After Setup

| Service | Public URL |
|---------|------------|
| SearXNG | https://your-domain.com/searxng/ |
| web-access-mcp | https://your-domain.com/web-access-mcp |

## Manual Docker Commands

If you prefer to run manually, you need to:

1. Generate `searxng/settings.yml` from template:

```bash
# Copy template
cp searxng/settings.yml.template searxng/settings.yml

# Replace placeholder with your secret
SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
sed -i "s/SEARXNG_SECRET_PLACEHOLDER/$SECRET/g" searxng/settings.yml

# (Optional) Set base_url
# sed -i "s|^server:|server:\n  base_url: \"https://your-domain.com/searxng/\"|g" searxng/settings.yml
```

2. Run containers:

```bash
# Create network
docker network create web-access-net

# Start SearXNG
docker run -d \
  --name searxng \
  --network web-access-net \
  --user $(id -u):$(id -g) \
  -p 8888:8080 \
  -v $(pwd)/searxng:/etc/searxng:rw \
  searxng/searxng:latest

# Build and start web-access-mcp
docker build -t web-access-mcp .
docker run -d \
  --name web-access-mcp \
  --network web-access-net \
  -p 4568:4568 \
  -e SEARXNG_MCP_URL=http://searxng:8080 \
  web-access-mcp
```

## Testing

```bash
# Test all tools
python test_mcp_client.py

# Test specific tool
python test_mcp_client.py --tool web_search_tool

# Test against different URL
python test_mcp_client.py --url http://localhost:4568/web-access-mcp
```

## Development

### Local Installation

```bash
pip install -e .
```

### Run Locally

```bash
python -m web_access_mcp.server
```

### Run Tests

```bash
pip install -e ".[dev]"
pytest
```

## Common Commands

```bash
# View logs
docker logs -f searxng
docker logs -f web-access-mcp

# Restart services
docker restart searxng web-access-mcp

# Stop services
docker stop searxng web-access-mcp

# Start services
docker start searxng web-access-mcp
```

## License

MIT
