"""Web fetch tool for reading website content."""

import re
import time
from typing import Any
from urllib.parse import urlparse

import html2text
import httpx

from forma.tools.base import SyncTool, ToolResult


class WebFetchTool(SyncTool):
    """Fetch and read content from a website URL.

    Downloads the webpage and converts it to readable text/markdown format.
    Useful for reading articles, documentation, or any web content.
    """

    name = "web_fetch"
    description = "Fetch and read content from a website URL. Downloads the webpage and converts HTML to readable text format. Use this to read articles, documentation, blog posts, or any web content directly. Returns the extracted text content with metadata."

    parameters = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL to fetch (must be a valid HTTP/HTTPS URL)",
            },
            "max_length": {
                "type": "integer",
                "description": "Maximum content length to return in characters (default: 10000, max: 50000)",
                "default": 10000,
            },
        },
        "required": ["url"],
    }

    timeout = 30.0
    max_content_length = 50000
    max_response_size = 5 * 1024 * 1024  # 5MB max response size

    def execute_sync(self, **kwargs: Any) -> ToolResult:
        """Execute web fetch."""
        url = kwargs.get("url", "")
        max_length = min(kwargs.get("max_length", 10000), self.max_content_length)

        if not url.strip():
            return ToolResult(
                success=False,
                error="URL cannot be empty",
            )

        # Validate URL
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                return ToolResult(
                    success=False,
                    error=f"Invalid URL scheme: {parsed.scheme}. Only HTTP and HTTPS are supported.",
                )
            if not parsed.netloc:
                return ToolResult(
                    success=False,
                    error="Invalid URL: missing domain",
                )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Invalid URL: {str(e)}",
            )

        start_time = time.time()

        try:
            # Fetch the webpage
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                response = client.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (compatible; FormaBot/1.0; +https://github.com/forma)",
                        "Accept": "text/html,application/xhtml+xml,text/plain",
                        "Accept-Language": "en-US,en;q=0.5",
                    },
                )
                response.raise_for_status()

                # Check response size
                content_length = len(response.content)
                if content_length > self.max_response_size:
                    return ToolResult(
                        success=False,
                        error=f"Response too large: {content_length} bytes (max: {self.max_response_size})",
                        duration_ms=(time.time() - start_time) * 1000,
                    )

                # Get content type
                content_type = response.headers.get("content-type", "").lower()

                # Handle different content types
                if "text/html" in content_type or "application/xhtml+xml" in content_type:
                    # Convert HTML to readable text
                    h = html2text.HTML2Text()
                    h.ignore_links = False  # Keep links visible
                    h.ignore_images = True  # Skip images
                    h.ignore_emphasis = False  # Keep emphasis markers
                    h.body_width = 0  # Don't wrap lines
                    h.ignore_scripts = True  # Skip script tags
                    h.ignore_styles = True  # Skip style tags

                    text_content = h.handle(response.text)

                    # Clean up excessive whitespace
                    text_content = re.sub(r"\n{3,}", "\n\n", text_content)
                    text_content = text_content.strip()

                elif "text/plain" in content_type:
                    text_content = response.text.strip()

                elif "application/json" in content_type:
                    # Return JSON as-is (formatted)
                    try:
                        import json

                        data = response.json()
                        text_content = json.dumps(data, indent=2)
                    except json.JSONDecodeError:
                        text_content = response.text

                else:
                    # Unsupported content type
                    return ToolResult(
                        success=True,
                        output={
                            "url": str(response.url),
                            "content_type": content_type,
                            "message": f"Unsupported content type: {content_type}. Cannot extract text.",
                        },
                        duration_ms=(time.time() - start_time) * 1000,
                        metadata={"url": url, "content_type": content_type},
                    )

                # Truncate if too long
                if len(text_content) > max_length:
                    text_content = text_content[:max_length]
                    truncated = True
                else:
                    truncated = False

                duration_ms = (time.time() - start_time) * 1000

                return ToolResult(
                    success=True,
                    output={
                        "url": str(response.url),  # Final URL after redirects
                        "title": self._extract_title(response.text),
                        "content": text_content,
                        "content_type": content_type,
                        "truncated": truncated,
                        "length": len(text_content),
                        "original_length": len(response.content),
                    },
                    duration_ms=duration_ms,
                    metadata={
                        "url": url,
                        "final_url": str(response.url),
                        "content_type": content_type,
                        "status_code": response.status_code,
                    },
                )

        except httpx.TimeoutException:
            duration_ms = (time.time() - start_time) * 1000
            return ToolResult(
                success=False,
                error=f"Request timed out after {self.timeout} seconds",
                duration_ms=duration_ms,
            )

        except httpx.HTTPStatusError as e:
            duration_ms = (time.time() - start_time) * 1000
            return ToolResult(
                success=False,
                error=f"HTTP error {e.response.status_code}: {e.response.reason_phrase}",
                duration_ms=duration_ms,
            )

        except httpx.RequestError as e:
            duration_ms = (time.time() - start_time) * 1000
            return ToolResult(
                success=False,
                error=f"Request failed: {str(e)}",
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return ToolResult(
                success=False,
                error=f"Web fetch failed: {str(e)}",
                duration_ms=duration_ms,
            )

    def _extract_title(self, html: str) -> str:
        """Extract page title from HTML."""
        # Try to find <title> tag
        match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # Try to find <h1> tag
        match = re.search(r"<h1[^>]*>([^<]+)</h1>", html, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        return ""
