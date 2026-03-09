"""Web search and image search tools using SearXNG."""

from typing import Optional, List

from ..client.searxng import search


async def web_search(
    query: str,
    max_results: int = 5,
    categories: Optional[List[str]] = None,
    language: Optional[str] = None,
    time_range: Optional[str] = None,
    searxng_url: Optional[str] = None,
) -> str:
    """Search the web using SearXNG.

    Args:
        query: The search query.
        max_results: Maximum number of results (default: 5).
        categories: SearXNG categories:
            - "general": General web search (default)
            - "images": Image search
            - "news": News articles
            - "videos": Video search
            - "files": File search
            - "science": Scientific articles
        language: ISO 639-1 language code (e.g., 'en', 'zh').
        time_range: Filter by time range:
            - "day": Last 24 hours
            - "week": Last week
            - "month": Last month
            - "year": Last year
        searxng_url: Optional SearXNG MCP server URL.

    Returns:
        Formatted search results with titles, URLs, and snippets.
    """
    return await search(
        query=query,
        max_results=max_results,
        categories=categories,
        language=language,
        time_range=time_range,
        searxng_url=searxng_url,
    )


async def image_search(
    query: str,
    max_results: int = 5,
    language: Optional[str] = None,
    searxng_url: Optional[str] = None,
) -> str:
    """Search for images using SearXNG.

    Use this tool BEFORE image generation to find reference images for
    characters, portraits, objects, scenes, or any content requiring visual accuracy.

    The returned image URLs can be used as reference images in image
    generation to significantly improve quality.

    Args:
        query: Search keywords describing the images you want to find.
        max_results: Maximum number of images to return (default: 5).
        language: ISO 639-1 language code (e.g., 'en', 'zh').
        searxng_url: Optional SearXNG MCP server URL.

    Returns:
        Formatted image search results with URLs, thumbnails, and sources.
    """
    return await search(
        query=query,
        max_results=max_results,
        categories=["images"],
        language=language,
        searxng_url=searxng_url,
    )


async def news_search(
    query: str,
    max_results: int = 5,
    language: Optional[str] = None,
    time_range: Optional[str] = None,
    searxng_url: Optional[str] = None,
) -> str:
    """Search for news articles using SearXNG.

    Args:
        query: The news search query.
        max_results: Maximum number of articles to return (default: 5).
        language: ISO 639-1 language code (e.g., 'en', 'zh').
        time_range: Filter by time range (day, week, month, year).
        searxng_url: Optional SearXNG MCP server URL.

    Returns:
        Formatted news search results with titles, URLs, sources, and dates.
    """
    return await search(
        query=query,
        max_results=max_results,
        categories=["news"],
        language=language,
        time_range=time_range,
        searxng_url=searxng_url,
    )


async def video_search(
    query: str,
    max_results: int = 5,
    language: Optional[str] = None,
    searxng_url: Optional[str] = None,
) -> str:
    """Search for videos using SearXNG.

    Args:
        query: The video search query.
        max_results: Maximum number of videos to return (default: 5).
        language: ISO 639-1 language code (e.g., 'en', 'zh').
        searxng_url: Optional SearXNG MCP server URL.

    Returns:
        Formatted video search results with titles, URLs, thumbnails, and durations.
    """
    return await search(
        query=query,
        max_results=max_results,
        categories=["videos"],
        language=language,
        searxng_url=searxng_url,
    )
