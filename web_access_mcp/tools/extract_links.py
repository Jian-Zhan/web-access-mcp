"""extract-links tool for MCP server."""

import json
from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup
import httpx

from ..config import Settings
from ..client.http_client import AsyncHTTPClient
from ..client.browser import AsyncBrowserClient
from ..exceptions import (
    WebAccessError,
    classify_http_error,
    NetworkError,
)

async def extract_links(
    url: str,
    render_js: bool = False,
    settings: Optional[Settings] = None,
) -> str:
    """Extract all links from a web page.

    Args:
        url: The URL to extract links from
        render_js: Whether to render JavaScript using Playwright
        settings: Optional settings (uses env vars if not provided)

    Returns:
        JSON string containing list of links with href, text, and title

    Raises:
        WebAccessError: If the fetch fails
    """
    settings = settings or Settings.from_env()

    try:
        if render_js:
            async with AsyncBrowserClient(settings=settings) as browser:
                html = await browser.fetch(url)
        else:
            async with AsyncHTTPClient(settings=settings) as client:
                html = await client.fetch_html(url)

        # Parse HTML and extract links
        soup = BeautifulSoup(html, "lxml")
        links: List[Dict[str, Any]] = []

        for a_tag in soup.find_all("a", href=True):
            link = {
                "href": a_tag.get("href", ""),
                "text": a_tag.get_text(strip=True),
                "title": a_tag.get("title", ""),
            }
            links.append(link)

        return json.dumps({"links": links}, ensure_ascii=False, indent=2)

    except WebAccessError:
        raise
    except httpx.HTTPStatusError as e:
        raise classify_http_error(e, url)
    except httpx.ConnectError as e:
        raise NetworkError(f"Connection failed: {url}", e)
    except httpx.TimeoutException as e:
        raise NetworkError(f"Request timed out: {url}", e)
    except Exception as e:
        raise WebAccessError(f"Failed to extract links from {url}: {type(e).__name__}: {e}")
