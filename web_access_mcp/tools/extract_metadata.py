"""extract-metadata tool for MCP server."""

import json
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
import httpx

from ..config import Settings
from ..client.http_client import AsyncHTTPClient
from ..exceptions import (
    WebAccessError,
    NetworkError,
)


async def extract_metadata(
    url: str,
    settings: Optional[Settings] = None,
) -> str:
    """Extract metadata from a web page.

    Args:
        url: The URL to extract metadata from
        settings: Optional settings (uses env vars if not provided)

    Returns:
        JSON string containing page metadata (title, description, OG tags, etc.)

    Raises:
        WebAccessError: If the fetch fails
    """
    settings = settings or Settings.from_env()

    try:
        async with AsyncHTTPClient(settings=settings) as client:
            html = await client.fetch_html(url)

        # Parse HTML and extract metadata
        soup = BeautifulSoup(html, "lxml")
        metadata: Dict[str, Any] = {}

        # Title
        title_tag = soup.find("title")
        if title_tag:
            metadata["title"] = title_tag.get_text(strip=True)

        # Meta tags
        for meta in soup.find_all("meta"):
            name = meta.get("name") or meta.get("property") or meta.get("itemprop")
            content = meta.get("content", "")
            if name and content:
                metadata[str(name)] = str(content)

        # Canonical URL
        canonical = soup.find("link", rel="canonical")
        if canonical and canonical.get("href"):
            metadata["canonical_url"] = canonical.get("href")

        # Favicon
        favicon = soup.find("link", rel="icon") or soup.find("link", rel="shortcut icon")
        if favicon and favicon.get("href"):
            metadata["favicon"] = favicon.get("href")

        return json.dumps(metadata, ensure_ascii=False, indent=2)

    except WebAccessError:
        raise
    except httpx.HTTPStatusError as e:
        raise WebAccessError(f"HTTP error {e.response.status_code}: {url}")
    except httpx.ConnectError as e:
        raise NetworkError(f"Connection failed: {url}", e)
    except httpx.TimeoutException as e:
        raise NetworkError(f"Request timed out: {url}", e)
    except Exception as e:
        raise WebAccessError(f"Failed to extract metadata from {url}: {type(e).__name__}: {e}")

