"""Browser client using Playwright for JS rendering."""

from typing import Optional
import base64
import random
import asyncio
import logging

from playwright.async_api import async_playwright, Browser, Page, BrowserContext

from ..config import Settings

logger = logging.getLogger(__name__)


class AsyncBrowserClient:
    """Async browser client using Playwright with user-agent spoofing."""

    def __init__(
        self,
        timeout: int = 30,
        headless: bool = True,
        settings: Optional[Settings] = None,
    ):
        """Initialize the browser client.

        Args:
            timeout: Page load timeout in seconds
            headless: Run browser in headless mode
            settings: Optional settings object (overrides other params if provided)
        """
        if settings:
            self.timeout = settings.timeout * 1000  # Convert to milliseconds
            self.settings = settings
        else:
            self.timeout = timeout * 1000
            self.settings = None
        self.headless = headless
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
    async def __aenter__(self) -> "AsyncBrowserClient":
        """Enter async context manager."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager."""
        await self.close()

    async def start(self) -> None:
        """Start the browser."""
        self._playwright = await async_playwright().start()

        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
        )

        # Create context with user-agent spoofing
        context_options = {}
        if self.settings:
            context_options["user_agent"] = self.settings.get_random_user_agent()
            # Add extra headers if provided
            if self.settings.extra_headers:
                context_options["extra_http_headers"] = self.settings.extra_headers

        self._context = await self._browser.new_context(**context_options)
    async def close(self) -> None:
        """Close the browser."""
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    async def _get_page(self) -> Page:
        """Get a new page."""
        if not self._context:
            raise RuntimeError(
                "Browser not started. Use async context manager or call start()."
            )
        return await self._context.new_page()

    async def fetch(self, url: str) -> str:
        """Fetch HTML content from a URL with JS rendering and retry logic.

        Args:
            url: URL to fetch

        Returns:
            HTML content as string
        """
        if not self.settings:
            # No retry logic
            page = await self._get_page()
            try:
                await page.goto(url, timeout=self.timeout, wait_until="domcontentloaded")
                html = await page.content()
                return html
            finally:
                await page.close()

        # Retry with exponential backoff
        last_exception = None
        for attempt in range(self.settings.retry_count):
            page = await self._get_page()
            try:
                # Rotate user-agent on each retry by creating new context
                if attempt > 0:
                    await self._context.close()
                    context_options = {
                        "user_agent": self.settings.get_random_user_agent()
                    }
                    if self.settings.extra_headers:
                        context_options["extra_http_headers"] = self.settings.extra_headers
                    self._context = await self._browser.new_context(**context_options)
                    page = await self._context.new_page()

                await page.goto(url, timeout=self.timeout, wait_until="domcontentloaded")
                html = await page.content()
                return html
            except Exception as e:
                last_exception = e
                if attempt < self.settings.retry_count - 1:
                    delay = self.settings.retry_backoff_base * (2 ** attempt)
                    delay += random.uniform(0, 0.1) * delay
                    logger.warning(
                        f"Browser retry {attempt + 1}/{self.settings.retry_count}: "
                        f"{type(e).__name__}, waiting {delay:.2f}s"
                    )
                    await asyncio.sleep(delay)
            finally:
                await page.close()

        # All retries exhausted
        if last_exception:
            raise last_exception
        raise RuntimeError(f"All {self.settings.retry_count} browser retries failed")
    async def screenshot(
        self,
        url: str,
        full_page: bool = False,
        width: int = 1280,
        height: int = 720,
    ) -> bytes:
        """Take a screenshot of a page.

        Args:
            url: URL to screenshot
            full_page: Capture full page or viewport
            width: Viewport width
            height: Viewport height

        Returns:
            PNG image bytes
        """
        page = await self._get_page()
        try:
            await page.set_viewport_size({"width": width, "height": height})
            await page.goto(url, timeout=self.timeout, wait_until="domcontentloaded")
            screenshot = await page.screenshot(full_page=full_page)
            return screenshot
        finally:
            await page.close()

    async def screenshot_base64(
        self,
        url: str,
        full_page: bool = False,
        width: int = 1280,
        height: int = 720,
    ) -> str:
        """Take a screenshot and return as base64 string.

        Args:
            url: URL to screenshot
            full_page: Capture full page or viewport
            width: Viewport width
            height: Viewport height

        Returns:
            Base64-encoded PNG string
        """
        screenshot_bytes = await self.screenshot(url, full_page, width, height)
        return base64.b64encode(screenshot_bytes).decode("utf-8")

    @staticmethod
    def from_settings(settings: Settings) -> "AsyncBrowserClient":
        """Create client from settings.

        Args:
            settings: Application settings

        Returns:
            Configured AsyncBrowserClient
        """
        return AsyncBrowserClient(settings=settings)
