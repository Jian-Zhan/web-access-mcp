"""Configuration module for web-access-mcp."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
import os
import json
import random

# Default user agents - realistic browser signatures
DEFAULT_USER_AGENTS = [
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # Chrome on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    # Firefox on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    # Safari on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
    # Chrome on Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

@dataclass
class Settings:
    """Application settings.

    Attributes:
        timeout: Request timeout in seconds
        max_response_size: Maximum response size in bytes
        user_agents: List of user-agent strings for rotation
        extra_headers: Additional headers to include in requests
        retry_count: Number of retry attempts for failed requests
        retry_backoff_base: Base delay for exponential backoff (seconds)
        retryable_status_codes: HTTP status codes that trigger retry
    """

    timeout: int = 30
    max_response_size: int = 10_000_000  # 10MB
    user_agents: List[str] = field(default_factory=lambda: DEFAULT_USER_AGENTS.copy())
    extra_headers: Dict[str, str] = field(default_factory=dict)
    retry_count: int = 3
    retry_backoff_base: float = 1.0
    retryable_status_codes: List[int] = field(
        default_factory=lambda: [429, 500, 502, 503, 504]
    )

    def get_random_user_agent(self) -> str:
        """Get a random user-agent from the list.

        Returns:
            Random user-agent string
        """
        return random.choice(self.user_agents)

    @staticmethod
    def from_env() -> "Settings":
        """Create settings from environment variables.

        Reads:
        - WEB_ACCESS_TIMEOUT: Timeout in seconds (default: 30)
        - WEB_ACCESS_MAX_SIZE: Max response size in bytes (default: 10MB)
        - WEB_ACCESS_USER_AGENTS: JSON array of user-agent strings
        - WEB_ACCESS_EXTRA_HEADERS: JSON object of extra headers
        - WEB_ACCESS_RETRY_COUNT: Number of retries (default: 3)
        - WEB_ACCESS_RETRY_BACKOFF: Backoff base in seconds (default: 1.0)
        - WEB_ACCESS_RETRYABLE_CODES: JSON array of status codes

        Returns:
            Settings instance
        """
        timeout = int(os.getenv("WEB_ACCESS_TIMEOUT", "30"))
        max_size = int(os.getenv("WEB_ACCESS_MAX_SIZE", "10000000"))

        # Load user agents from env if provided
        user_agents = DEFAULT_USER_AGENTS.copy()
        ua_env = os.getenv("WEB_ACCESS_USER_AGENTS", "").strip()
        if ua_env:
            try:
                user_agents = json.loads(ua_env)
            except json.JSONDecodeError:
                pass

        # Load extra headers from env if provided
        extra_headers: Dict[str, str] = {}
        headers_env = os.getenv("WEB_ACCESS_EXTRA_HEADERS", "").strip()
        if headers_env:
            try:
                extra_headers = json.loads(headers_env)
            except json.JSONDecodeError:
                pass

        # Load retry settings
        retry_count = int(os.getenv("WEB_ACCESS_RETRY_COUNT", "3"))
        retry_backoff = float(os.getenv("WEB_ACCESS_RETRY_BACKOFF", "1.0"))

        # Load retryable status codes
        retryable_codes = [429, 500, 502, 503, 504]
        codes_env = os.getenv("WEB_ACCESS_RETRYABLE_CODES", "").strip()
        if codes_env:
            try:
                retryable_codes = json.loads(codes_env)
            except json.JSONDecodeError:
                pass

        return Settings(
            timeout=timeout,
            max_response_size=max_size,
            user_agents=user_agents,
            extra_headers=extra_headers,
            retry_count=retry_count,
            retry_backoff_base=retry_backoff,
            retryable_status_codes=retryable_codes,
        )
