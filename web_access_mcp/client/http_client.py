"""HTTP client for web requests."""

from typing import Optional
import httpx
import random
import asyncio
import logging

from ..config import Settings

logger = logging.getLogger(__name__)


class AsyncHTTPClient:
    """Async HTTP client with retry and user-agent rotation."""

    def __init__(
        self,
        timeout: int = 30,
        max_response_size: int = 10_000_000,
        settings: Optional[Settings] = None,
    ):
        """Initialize the HTTP client.

        Args:
            timeout: Request timeout in seconds
            max_response_size: Maximum response size in bytes
            settings: Optional settings object (overrides other params if provided)
        """
        if settings:
            self.timeout = settings.timeout
            self.max_response_size = settings.max_response_size
            self.settings = settings
        else:
            self.timeout = timeout
            self.max_response_size = max_response_size
            self.settings = None
        self._client: Optional[httpx.AsyncClient] = None
    async def __aenter__(self) -> "AsyncHTTPClient":
        """Enter async context manager."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager."""
        await self.close()

    async def start(self) -> None:
        """Start the HTTP client."""
        # Build headers with user-agent rotation
        headers = {}
        if self.settings:
            headers["User-Agent"] = self.settings.get_random_user_agent()
            headers.update(self.settings.extra_headers)

        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            headers=headers if headers else None,
        )
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get(self, url: str) -> httpx.Response:
        """Perform a GET request with retry logic.

        Args:
            url: URL to fetch

        Returns:
            HTTP response

        Raises:
            httpx.HTTPError: If the request fails after all retries
        """
        if not self._client:
            raise RuntimeError(
                "Client not started. Use async context manager or call start()."
            )

        if not self.settings:
            # No retry logic, just do single request
            response = await self._client.get(url)
            response.raise_for_status()
            return response

        # Retry with exponential backoff
        last_exception = None
        for attempt in range(self.settings.retry_count):
            try:
                # Rotate user-agent on each retry
                if attempt > 0:
                    self._client.headers["User-Agent"] = self.settings.get_random_user_agent()

                response = await self._client.get(url)

                # Check if status code is retryable
                if response.status_code in self.settings.retryable_status_codes:
                    if attempt < self.settings.retry_count - 1:
                        delay = self.settings.retry_backoff_base * (2 ** attempt)
                        delay += random.uniform(0, 0.1) * delay  # Add jitter
                        logger.warning(
                            f"Retry {attempt + 1}/{self.settings.retry_count}: "
                            f"Status {response.status_code}, waiting {delay:.2f}s"
                        )
                        await asyncio.sleep(delay)
                        continue

                response.raise_for_status()
                return response

            except httpx.HTTPStatusError as e:
                last_exception = e
                if e.response.status_code not in self.settings.retryable_status_codes:
                    raise
                if attempt < self.settings.retry_count - 1:
                    delay = self.settings.retry_backoff_base * (2 ** attempt)
                    delay += random.uniform(0, 0.1) * delay
                    logger.warning(
                        f"Retry {attempt + 1}/{self.settings.retry_count}: "
                        f"HTTP {e.response.status_code}, waiting {delay:.2f}s"
                    )
                    await asyncio.sleep(delay)
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout) as e:
                last_exception = e
                if attempt < self.settings.retry_count - 1:
                    delay = self.settings.retry_backoff_base * (2 ** attempt)
                    delay += random.uniform(0, 0.1) * delay
                    logger.warning(
                        f"Retry {attempt + 1}/{self.settings.retry_count}: "
                        f"Connection error {type(e).__name__}, waiting {delay:.2f}s"
                    )
                    await asyncio.sleep(delay)

        # All retries exhausted
        if last_exception:
            raise last_exception
        raise httpx.HTTPError(f"All {self.settings.retry_count} retries failed")
    async def fetch_html(self, url: str) -> str:
        """Fetch HTML content from a URL.

        Args:
            url: URL to fetch

        Returns:
            HTML content as string
        """
        response = await self.get(url)
        return response.text

    @staticmethod
    def from_settings(settings: Settings) -> "AsyncHTTPClient":
        """Create client from settings.

        Args:
            settings: Application settings

        Returns:
            Configured AsyncHTTPClient
        """
        return AsyncHTTPClient(settings=settings)
