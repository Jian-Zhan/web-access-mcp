"""FastMCP Server entry point for web-access-mcp."""

import asyncio
import logging
import os
from mcp.server.fastmcp import FastMCP

from .config import Settings
from .tools.web_fetch import web_fetch
from .tools.extract_links import extract_links
from .tools.extract_metadata import extract_metadata
from .tools.search import web_search, image_search, news_search, video_search

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastMCP server instance
mcp = FastMCP(
    "web-access-mcp",
    stateless_http=True,
    json_response=True,
    host="0.0.0.0",
    port=4568,
    streamable_http_path="/web-access-mcp",
)


@mcp.tool()
async def web_fetch_tool(url: str) -> str:
    """Fetch a web page and return its content as Markdown.

    Args:
        url: The URL to fetch

    Returns:
        Markdown-formatted content of the page
    """
    logger.info(f"web_fetch_tool called: url={url}")
    return await web_fetch(url=url)


@mcp.tool()
async def extract_links_tool(url: str) -> str:
    """Extract all links from a web page.

    Args:
        url: The URL to extract links from

    Returns:
        JSON string containing list of links with href, text, and title
    """
    logger.info(f"extract_links_tool called: url={url}")
    return await extract_links(url=url)


@mcp.tool()
async def extract_metadata_tool(url: str) -> str:
    """Extract metadata from a web page.

    Args:
        url: The URL to extract metadata from

    Returns:
        JSON string containing page metadata (title, description, OG tags, etc.)
    """
    logger.info(f"extract_metadata_tool called: url={url}")
    return await extract_metadata(url=url)


# ============================================================================
# Search Tools (SearXNG)
# ============================================================================

@mcp.tool()
async def web_search_tool(
    query: str,
    max_results: int = 5,
    categories: str | None = None,
    language: str | None = None,
    time_range: str | None = None,
) -> str:
    """Search the web using SearXNG.

    Args:
        query: The search query
        max_results: Maximum number of results (default: 5)
        categories: Comma-separated categories: general, images, news, videos, files, science
        language: ISO 639-1 language code (e.g., 'en', 'zh')
        time_range: Filter by time range: day, week, month, year

    Returns:
        Formatted search results with titles, URLs, and snippets
    """
    logger.info(f"web_search_tool called: query={query}")
    cats = [c.strip() for c in categories.split(",")] if categories else None
    return await web_search(
        query=query,
        max_results=max_results,
        categories=cats,
        language=language,
        time_range=time_range,
    )


@mcp.tool()
async def image_search_tool(query: str, max_results: int = 5) -> str:
    """Search for images using SearXNG.

    Use this tool BEFORE image generation to find reference images for
    characters, portraits, objects, scenes, or any content requiring visual accuracy.

    Args:
        query: Search keywords describing the images you want to find
        max_results: Maximum number of images to return (default: 5)

    Returns:
        Formatted image search results with URLs, thumbnails, and sources
    """
    logger.info(f"image_search_tool called: query={query}")
    return await image_search(query=query, max_results=max_results)


@mcp.tool()
async def news_search_tool(
    query: str,
    max_results: int = 5,
    language: str | None = None,
    time_range: str | None = None,
) -> str:
    """Search for news articles using SearXNG.

    Args:
        query: The news search query
        max_results: Maximum number of articles to return (default: 5)
        language: ISO 639-1 language code (e.g., 'en', 'zh')
        time_range: Filter by time range: day, week, month, year

    Returns:
        Formatted news search results with titles, URLs, sources, and dates
    """
    logger.info(f"news_search_tool called: query={query}")
    return await news_search(
        query=query,
        max_results=max_results,
        language=language,
        time_range=time_range,
    )


@mcp.tool()
async def video_search_tool(query: str, max_results: int = 5) -> str:
    """Search for videos using SearXNG.

    Args:
        query: The video search query
        max_results: Maximum number of videos to return (default: 5)

    Returns:
        Formatted video search results with titles, URLs, thumbnails, and durations
    """
    logger.info(f"video_search_tool called: query={query}")
    return await video_search(query=query, max_results=max_results)

def main():
    """Main entry point for the MCP server."""
    logger.info("Starting web-access-mcp server on port 4568")
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
