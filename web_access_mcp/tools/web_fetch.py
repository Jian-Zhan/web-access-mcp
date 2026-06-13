"""web-fetch tool for MCP server."""

from typing import Optional
from markdownify import markdownify as md
import httpx

from ..config import Settings
from ..client.http_client import AsyncHTTPClient
from ..exceptions import (
    WebAccessError,
    classify_http_error,
    NetworkError,
)

async def web_fetch(
    url: str,
    settings: Optional[Settings] = None,
) -> str:
    """Fetch a web page and return its content as Markdown.

    Args:
        url: The URL to fetch
        settings: Optional settings (uses env vars if not provided)

    Returns:
        Markdown-formatted content of the page

    Raises:
        WebAccessError: If the fetch fails
    """
    settings = settings or Settings.from_env()

    try:
        async with AsyncHTTPClient(settings=settings) as client:
            html = await client.fetch_html(url)
        markdown = md(html)
        return markdown

    except WebAccessError:
        raise
    except httpx.HTTPStatusError as e:
        raise classify_http_error(e, url)
    except httpx.ConnectError as e:
        raise NetworkError(f"Connection failed: {url}", e)
    except httpx.TimeoutException as e:
        raise NetworkError(f"Request timed out: {url}", e)
    except Exception as e:
        raise WebAccessError(f"Failed to fetch {url}: {type(e).__name__}: {e}")
