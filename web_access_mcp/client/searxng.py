"""SearXNG search client for web-access-mcp."""

import json
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
    return_json: bool = False,
) -> str:
    """Search the web using SearXNG HTTP API.

    Args:
        query: The search query.
        max_results: Maximum number of results (default: 5).
        categories: SearXNG categories (general, images, news, videos, files, science).
        language: ISO 639-1 language code (e.g., 'en', 'zh').
        time_range: Filter by time range (day, week, month, year).
        searxng_url: Optional SearXNG server URL.
        return_json: Return JSON format for frontend compatibility.

    Returns:
        Formatted search results as text or JSON string.
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

        # Get results
        results = data.get("results", [])[:max_results]

        if not results:
            return "No results found."

        if return_json:
            # Return JSON format for frontend compatibility
            formatted_results = [
                {
                    "url": result.get("url", ""),
                    "title": result.get("title", "No title"),
                    "snippet": result.get("content", ""),
                }
                for result in results
            ]
            return json.dumps(formatted_results, ensure_ascii=False)

        # Return formatted text
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


async def image_search(
    query: str,
    max_results: int = 5,
    language: Optional[str] = None,
    searxng_url: Optional[str] = None,
) -> str:
    """Search for images using SearXNG.

    Returns JSON format compatible with frontend:
    {"results": [{"source_url", "thumbnail_url", "image_url", "title"}]}

    Args:
        query: The search query.
        max_results: Maximum number of results (default: 5).
        language: ISO 639-1 language code (e.g., 'en', 'zh').
        searxng_url: Optional SearXNG server URL.

    Returns:
        JSON string with image results.
    """
    url = searxng_url or get_searxng_url()

    # Build search parameters
    params = {
        "q": query,
        "format": "json",
        "categories": "images",
    }

    if language:
        params["language"] = language

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{url}/search", params=params)
            response.raise_for_status()
            data = response.json()

        # Get results
        results = data.get("results", [])[:max_results]

        if not results:
            return json.dumps({"results": []}, ensure_ascii=False)

        # Format for frontend compatibility
        formatted_results = {
            "results": [
                {
                    "source_url": r.get("url", ""),
                    "thumbnail_url": r.get("thumbnail_src", r.get("url", "")),
                    "image_url": r.get("img_src", r.get("url", "")),
                    "title": r.get("title", "No title"),
                }
                for r in results
            ]
        }

        return json.dumps(formatted_results, ensure_ascii=False)

    except httpx.HTTPStatusError as e:
        logger.error(f"SearXNG HTTP error: {e}")
        return json.dumps(
            {"error": f"Search failed with HTTP {e.response.status_code}"}
        )
    except httpx.RequestError as e:
        logger.error(f"SearXNG request error: {e}")
        return json.dumps({"error": f"Could not connect to SearXNG at {url}"})
    except Exception as e:
        logger.error(f"SearXNG image search failed: {e}")
        return json.dumps({"error": f"Search failed - {str(e)}"})


async def news_search(
    query: str,
    max_results: int = 5,
    language: Optional[str] = None,
    time_range: Optional[str] = None,
    searxng_url: Optional[str] = None,
) -> str:
    """Search for news articles using SearXNG.

    Returns JSON format: [{"url", "title", "snippet", "published_date"}]

    Args:
        query: The news search query.
        max_results: Maximum number of articles to return (default: 5).
        language: ISO 639-1 language code (e.g., 'en', 'zh').
        time_range: Filter by time range (day, week, month, year).
        searxng_url: Optional SearXNG server URL.

    Returns:
        JSON string with news results.
    """
    url = searxng_url or get_searxng_url()

    # Build search parameters
    params = {
        "q": query,
        "format": "json",
        "categories": "news",
    }

    if language:
        params["language"] = language

    if time_range:
        params["time_range"] = time_range

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{url}/search", params=params)
            response.raise_for_status()
            data = response.json()

        # Get results
        results = data.get("results", [])[:max_results]

        if not results:
            return json.dumps([], ensure_ascii=False)

        # Format for frontend compatibility
        formatted_results = [
            {
                "url": r.get("url", ""),
                "title": r.get("title", "No title"),
                "snippet": r.get("content", ""),
                "published_date": r.get("publishedDate", ""),
            }
            for r in results
        ]

        return json.dumps(formatted_results, ensure_ascii=False)

    except httpx.HTTPStatusError as e:
        logger.error(f"SearXNG HTTP error: {e}")
        return json.dumps(
            {"error": f"Search failed with HTTP {e.response.status_code}"}
        )
    except httpx.RequestError as e:
        logger.error(f"SearXNG request error: {e}")
        return json.dumps({"error": f"Could not connect to SearXNG at {url}"})
    except Exception as e:
        logger.error(f"SearXNG news search failed: {e}")
        return json.dumps({"error": f"Search failed - {str(e)}"})


async def video_search(
    query: str,
    max_results: int = 5,
    language: Optional[str] = None,
    searxng_url: Optional[str] = None,
) -> str:
    """Search for videos using SearXNG.

    Returns JSON format: [{"url", "title", "thumbnail", "duration"}]

    Args:
        query: The video search query.
        max_results: Maximum number of videos to return (default: 5).
        language: ISO 639-1 language code (e.g., 'en', 'zh').
        searxng_url: Optional SearXNG server URL.

    Returns:
        JSON string with video results.
    """
    url = searxng_url or get_searxng_url()

    # Build search parameters
    params = {
        "q": query,
        "format": "json",
        "categories": "videos",
    }

    if language:
        params["language"] = language

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{url}/search", params=params)
            response.raise_for_status()
            data = response.json()

        # Get results
        results = data.get("results", [])[:max_results]

        if not results:
            return json.dumps([], ensure_ascii=False)

        # Format for frontend compatibility
        formatted_results = [
            {
                "url": r.get("url", ""),
                "title": r.get("title", "No title"),
                "thumbnail": r.get("thumbnail_src", r.get("thumbnail", "")),
                "duration": r.get("duration", ""),
            }
            for r in results
        ]

        return json.dumps(formatted_results, ensure_ascii=False)

    except httpx.HTTPStatusError as e:
        logger.error(f"SearXNG HTTP error: {e}")
        return json.dumps(
            {"error": f"Search failed with HTTP {e.response.status_code}"}
        )
    except httpx.RequestError as e:
        logger.error(f"SearXNG request error: {e}")
        return json.dumps({"error": f"Could not connect to SearXNG at {url}"})
    except Exception as e:
        logger.error(f"SearXNG video search failed: {e}")
        return json.dumps({"error": f"Search failed - {str(e)}"})
