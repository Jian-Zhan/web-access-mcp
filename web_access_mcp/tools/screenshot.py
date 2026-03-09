"""screenshot tool for MCP server."""

from typing import Optional
import httpx

from ..config import Settings
from ..client.browser import AsyncBrowserClient
from ..exceptions import (
    WebAccessError,
    NetworkError,
)

async def screenshot(
    url: str,
    full_page: bool = False,
    width: int = 1280,
    height: int = 720,
    settings: Optional[Settings] = None,
) -> str:
    """Take a screenshot of a web page.

    Args:
        url: The URL to screenshot
        full_page: Whether to capture the full page or just viewport
        width: Viewport width in pixels
        height: Viewport height in pixels
        settings: Optional settings (uses env vars if not provided)

    Returns:
        Base64-encoded PNG image string

    Raises:
        WebAccessError: If the screenshot fails
    """
    settings = settings or Settings.from_env()

    try:
        async with AsyncBrowserClient(settings=settings) as browser:
            b64_image = await browser.screenshot_base64(
                url=url,
                full_page=full_page,
                width=width,
                height=height,
            )
        return b64_image

    except WebAccessError:
        raise
    except Exception as e:
        # Playwright errors don't map to httpx, so handle generically
        error_name = type(e).__name__
        if "timeout" in error_name.lower() or "Timeout" in error_name:
            raise NetworkError(f"Screenshot timed out: {url}", e)
        raise WebAccessError(f"Failed to screenshot {url}: {error_name}: {e}")
