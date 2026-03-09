"""Custom exceptions for web-access-mcp."""


class WebAccessError(Exception):
    """Base exception for web-access-mcp errors."""

    def __init__(self, message: str, suggestion: str = ""):
        self.message = message
        self.suggestion = suggestion
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.suggestion:
            return f"{self.message}\nSuggestion: {self.suggestion}"
        return self.message


class NetworkError(WebAccessError):
    """Network-related errors (connection, timeout, DNS)."""

    def __init__(self, message: str, original_error: Exception | None = None):
        suggestion = (
            "Check your network connection and try again. "
            "The target server may be temporarily unavailable."
        )
        super().__init__(message, suggestion)
        self.original_error = original_error


class ForbiddenError(WebAccessError):
    """403 Forbidden error - access denied by the server."""

    def __init__(self, url: str, original_error: Exception | None = None):
        message = f"Access forbidden (403) for URL: {url}"
        suggestion = (
            "The server blocked the request. This may be due to:\n"
            "  - Bot detection (try using browser mode)\n"
            "  - Geographic restrictions\n"
            "  - Authentication requirements\n"
            "  - Rate limiting (wait and try again)"
        )
        super().__init__(message, suggestion)
        self.url = url
        self.original_error = original_error


class SSLError(WebAccessError):
    """SSL/TLS certificate errors."""

    def __init__(self, url: str, original_error: Exception | None = None):
        message = f"SSL certificate error for URL: {url}"
        suggestion = (
            "The server's SSL certificate could not be verified. "
            "This may indicate a security issue or misconfiguration."
        )
        super().__init__(message, suggestion)
        self.url = url
        self.original_error = original_error


class JSError(WebAccessError):
    """Page requires JavaScript to render content."""

    def __init__(self, url: str, reason: str = ""):
        message = f"Page requires JavaScript: {url}"
        if reason:
            message += f" ({reason})"
        suggestion = (
            "This page requires JavaScript to display content. "
            "Use browser mode (Playwright) instead of HTTP client."
        )
        super().__init__(message, suggestion)
        self.url = url
        self.reason = reason


class NotFoundError(WebAccessError):
    """404 Not Found error."""

    def __init__(self, url: str):
        message = f"Resource not found (404): {url}"
        suggestion = (
            "The requested URL does not exist. Check for typos or outdated links."
        )
        super().__init__(message, suggestion)
        self.url = url


class RateLimitError(WebAccessError):
    """429 Too Many Requests error."""

    def __init__(self, url: str, retry_after: int | None = None):
        message = f"Rate limited (429): {url}"
        if retry_after:
            message += f" - Retry after {retry_after} seconds"
        suggestion = (
            "You've made too many requests. "
            "Wait before trying again or reduce request frequency."
        )
        super().__init__(message, suggestion)
        self.url = url
        self.retry_after = retry_after


class ServerError(WebAccessError):
    """5xx server errors."""

    def __init__(
        self, url: str, status_code: int, original_error: Exception | None = None
    ):
        message = f"Server error ({status_code}) for URL: {url}"
        suggestion = (
            "The server encountered an internal error. "
            "This is usually temporary - try again later."
        )
        super().__init__(message, suggestion)
        self.url = url
        self.status_code = status_code
        self.original_error = original_error


class ContentTooLargeError(WebAccessError):
    """Response size exceeds limit."""

    def __init__(self, url: str, size: int, limit: int):
        message = f"Response too large: {url} ({size} bytes > {limit} bytes limit)"
        suggestion = "The page content exceeds the maximum allowed size."
        super().__init__(message, suggestion)
        self.url = url
        self.size = size
        self.limit = limit


def classify_http_error(error: Exception, url: str) -> WebAccessError:
    """Classify an HTTP error into the appropriate custom exception.

    Args:
        error: The original exception
        url: The URL that was being accessed

    Returns:
        Appropriate WebAccessError subclass
    """
    import httpx

    if isinstance(error, httpx.HTTPStatusError):
        status = error.response.status_code

        if status == 403:
            return ForbiddenError(url, error)
        elif status == 404:
            return NotFoundError(url)
        elif status == 429:
            retry_after = error.response.headers.get("Retry-After")
            retry_seconds = (
                int(retry_after) if retry_after and retry_after.isdigit() else None
            )
            return RateLimitError(url, retry_seconds)
        elif 500 <= status < 600:
            return ServerError(url, status, error)
        else:
            return WebAccessError(f"HTTP error {status}: {url}")

    elif isinstance(error, httpx.ConnectError):
        return NetworkError(f"Connection failed: {url}", error)

    elif isinstance(error, (httpx.ReadTimeout, httpx.ConnectTimeout)):
        return NetworkError(f"Request timed out: {url}", error)

    elif isinstance(error, httpx.SSLError):
        return SSLError(url, error)

    else:
        return WebAccessError(
            f"Request failed: {url} - {type(error).__name__}: {error}"
        )
