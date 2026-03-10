"""Web search and image search tools using SearXNG."""

from typing import Optional, List

from ..client.searxng import search, image_search as searxng_image_search
from ..client.searxng import news_search as searxng_news_search
from ..client.searxng import video_search as searxng_video_search


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
        JSON array of search results: [{"url", "title", "snippet"}]
    """
    return await search(
        query=query,
        max_results=max_results,
        categories=categories,
        language=language,
        time_range=time_range,
        searxng_url=searxng_url,
        return_json=True,
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
        JSON object: {"results": [{"source_url", "thumbnail_url", "image_url", "title"}]}
    """
    return await searxng_image_search(
        query=query,
        max_results=max_results,
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
        JSON array: [{"url", "title", "snippet", "published_date"}]
    """
    return await searxng_news_search(
        query=query,
        max_results=max_results,
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
        JSON array: [{"url", "title", "thumbnail", "duration"}]
    """
    return await searxng_video_search(
        query=query,
        max_results=max_results,
        language=language,
        searxng_url=searxng_url,
    )
