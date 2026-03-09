"""Tools for web-access-mcp."""

from .web_fetch import web_fetch
from .extract_links import extract_links
from .screenshot import screenshot
from .extract_metadata import extract_metadata

__all__ = ["web_fetch", "extract_links", "screenshot", "extract_metadata"]
