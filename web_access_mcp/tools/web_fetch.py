"""web-fetch tool for MCP server."""

from typing import Optional
from markdownify import markdownify as md
from bs4 import BeautifulSoup
import httpx

from ..config import Settings
from ..client.http_client import AsyncHTTPClient
from ..client.browser import AsyncBrowserClient
from ..exceptions import (
    WebAccessError,
    classify_http_error,
    JSError,
    NetworkError,
)

async def web_fetch(
    url: str,
    render_js: bool = False,
    settings: Optional[Settings] = None,
) -> str:
    """Fetch a web page and return its content as Markdown.

    Args:
        url: The URL to fetch
        render_js: Whether to render JavaScript using Playwright
        settings: Optional settings (uses env vars if not provided)

    Returns:
        Markdown-formatted content of the page

    Raises:
        WebAccessError: If the fetch fails
    """
    settings = settings or Settings.from_env()

    try:
        if render_js:
            # Use browser client for JS rendering
            async with AsyncBrowserClient(settings=settings) as browser:
                html = await browser.fetch(url)
        else:
            # Use HTTP client for simple fetch
            async with AsyncHTTPClient(settings=settings) as client:
                html = await client.fetch_html(url)

        # Check if content looks like JS is required
        if not render_js and _looks_like_js_required(html):
            # Try again with browser
            try:
                async with AsyncBrowserClient(settings=settings) as browser:
                    html = await browser.fetch(url)
            except Exception:
                pass  # Return HTTP content if browser fails

        # Convert HTML to Markdown
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


def _looks_like_js_required(html: str) -> bool:
    """Check if HTML content suggests JavaScript is required.

    Args:
        html: HTML content to analyze

    Returns:
        True if the page likely requires JavaScript
    """
    html_lower = html.lower()

    # Common indicators of JS-required pages
    js_indicators = [
        "<noscript>",
        "enable javascript",
        "javascript is disabled",
        "you need to enable javascript",
        "app-root",
        "app id=\"root\"",
        "<div id=\"root\"></div>",
        "<div id=\"app\"></div>",
        "loading...",
        "<body></body>",
    ]

    # Check for empty or minimal body
    if len(html.strip()) < 500:
        return True

    # Check for JS indicators
    for indicator in js_indicators:
        if indicator in html_lower:
            return True

    return False
