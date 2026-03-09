"""SearXNG search client for web-access-mcp."""

import logging
import os
from typing import Optional, List

import httpx

logger = logging.getLogger(__name__)

# Default SearXNG URL (local Docker)
DEFAULT_SEARXNG_URL = "http://localhost:8080"


def get_searxng_url() -> str:
    """Get SearXNG URL from environment variable or default.

    Returns:
        SearXNG server URL
    """
    return os.environ.get("SEARXNG_MCP_URL", DEFAULT_SEARXNG_URL)


async def search(
    query: str,
    max_results: int = 5,
    categories: Optional[List[str]] = None,
    language: Optional[str] = None,
    time_range: Optional[str] = None,
    searxng_url: Optional[str] = None,
) -> str:
    """Search the web using SearXNG HTTP API.

    Args:
        query: The search query.
        max_results: Maximum number of results (default: 5).
        categories: SearXNG categories (general, images, news, videos, files, science).
        language: ISO 639-1 language code (e.g., 'en', 'zh').
        time_range: Filter by time range (day, week, month, year).
        searxng_url: Optional SearXNG server URL.

    Returns:
        Formatted search results as text.
    """
    url = searxng_url or get_searxng_url()

    # Build search parameters
    params = {
        "q": query,
        "format": "json",
    }

    if categories:
        params["categories"] = ",".join(categories)

    if language:
        params["language"] = language

    if time_range:
        params["time_range"] = time_range

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{url}/search", params=params)
            response.raise_for_status()
            data = response.json()

        # Format results
        results = data.get("results", [])[:max_results]

        if not results:
            return "No results found."

        output = []
        for i, result in enumerate(results, 1):
            title = result.get("title", "No title")
            link = result.get("url", "")
            snippet = result.get("content", "")

            output.append(f"{i}. **{title}**")
            output.append(f"   URL: {link}")
            if snippet:
                output.append(f"   {snippet}")
            output.append("")

        return "\n".join(output)

    except httpx.HTTPStatusError as e:
        logger.error(f"SearXNG HTTP error: {e}")
        return f"Error: Search failed with HTTP {e.response.status_code}"
    except httpx.RequestError as e:
        logger.error(f"SearXNG request error: {e}")
        return f"Error: Could not connect to SearXNG at {url}"
    except Exception as e:
        logger.error(f"SearXNG search failed: {e}")
        return f"Error: Search failed - {str(e)}"
