#!/usr/bin/env python3
"""
Test client for Web Access MCP Server.

Tests all available tools against a running MCP server.

Usage:
    # Default URL (http://localhost:4568/web-access-mcp)
    python test_mcp_client.py

    # Custom URL
    python test_mcp_client.py --url http://localhost:4568/web-access-mcp

    # Test specific tool
    python test_mcp_client.py --tool web_search_tool
"""

import argparse
import asyncio
import json
import sys
from typing import Any

import httpx


class MCPClient:
    """Simple MCP client for testing."""

    def __init__(self, url: str):
        self.url = url
        self.client = httpx.AsyncClient(timeout=60.0)
        self.request_id = 0

    async def close(self):
        await self.client.aclose()

    async def call(self, method: str, params: dict | None = None) -> dict:
        """Make an MCP JSON-RPC call."""
        self.request_id += 1
        payload = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {},
        }

        response = await self.client.post(
            self.url,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        response.raise_for_status()
        return response.json()

    async def list_tools(self) -> list[dict]:
        """Get list of available tools."""
        result = await self.call("tools/list")
        return result.get("result", {}).get("tools", [])

    async def call_tool(self, name: str, arguments: dict) -> Any:
        """Call a specific tool."""
        result = await self.call(
            "tools/call",
            {
                "name": name,
                "arguments": arguments,
            },
        )

        # Handle MCP response format
        content = result.get("result", {}).get("content", [])
        if content and len(content) > 0:
            text = content[0].get("text", "")
            # Try to parse as JSON
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text
        return None


async def test_tools(client: MCPClient, specific_tool: str | None = None):
    """Test all or specific tools."""

    print("=" * 60)
    print(f"Testing MCP Server: {client.url}")
    print("=" * 60)

    # List tools
    print("\n📋 Listing available tools...")
    try:
        tools = await client.list_tools()
        print(f"Found {len(tools)} tools:")
        for tool in tools:
            print(
                f"  - {tool['name']}: {tool.get('description', 'No description')[:50]}..."
            )
    except Exception as e:
        print(f"❌ Failed to list tools: {e}")
        return

    # Define test cases
    test_cases = {
        "web_fetch_tool": {
            "url": "https://www.python.org",
            "render_js": True,
        },
        "extract_links_tool": {
            "url": "https://www.python.org",
            "render_js": False,
        },
        "screenshot_tool": {
            "url": "https://www.python.org",
            "full_page": False,
            "width": 1280,
            "height": 720,
        },
        "extract_metadata_tool": {
            "url": "https://www.python.org",
        },
        "web_search_tool": {
            "query": "Python programming",
            "max_results": 3,
        },
        "image_search_tool": {
            "query": "cute cats",
            "max_results": 3,
        },
        "news_search_tool": {
            "query": "technology news",
            "max_results": 3,
        },
        "video_search_tool": {
            "query": "Python tutorial",
            "max_results": 3,
        },
    }

    # Filter to specific tool if requested
    if specific_tool:
        if specific_tool not in test_cases:
            print(f"\n❌ Unknown tool: {specific_tool}")
            print(f"Available tools: {list(test_cases.keys())}")
            return
        test_cases = {specific_tool: test_cases[specific_tool]}

    # Run tests
    print("\n" + "=" * 60)
    print("Running Tests")
    print("=" * 60)

    results = {"passed": 0, "failed": 0, "errors": []}

    for tool_name, arguments in test_cases.items():
        print(f"\n🔍 Testing: {tool_name}")
        print(f"   Arguments: {arguments}")

        try:
            result = await client.call_tool(tool_name, arguments)

            # Validate result
            if result is None:
                print(f"   ❌ FAILED: No result returned")
                results["failed"] += 1
                results["errors"].append(f"{tool_name}: No result")
                continue

            # Print result preview
            if isinstance(result, str):
                preview = result[:200] + "..." if len(result) > 200 else result
                print(f"   ✅ PASSED: {preview}")
            elif isinstance(result, dict):
                print(f"   ✅ PASSED: {json.dumps(result, indent=2)[:300]}...")
            else:
                print(f"   ✅ PASSED: {type(result).__name__}")

            results["passed"] += 1

        except httpx.HTTPStatusError as e:
            print(f"   ❌ FAILED: HTTP {e.response.status_code}")
            results["failed"] += 1
            results["errors"].append(f"{tool_name}: HTTP {e.response.status_code}")
        except Exception as e:
            print(f"   ❌ FAILED: {type(e).__name__}: {e}")
            results["failed"] += 1
            results["errors"].append(f"{tool_name}: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")

    if results["errors"]:
        print("\nErrors:")
        for error in results["errors"]:
            print(f"  - {error}")

    return results


async def main():
    parser = argparse.ArgumentParser(description="Test Web Access MCP Server")
    parser.add_argument(
        "--url",
        default="http://localhost:4568/web-access-mcp",
        help="MCP Server URL (default: http://localhost:4568/web-access-mcp)",
    )
    parser.add_argument(
        "--tool",
        help="Test a specific tool only",
    )
    args = parser.parse_args()

    client = MCPClient(args.url)

    try:
        results = await test_tools(client, args.tool)

        # Exit with error code if any tests failed
        if results and results["failed"] > 0:
            sys.exit(1)
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
