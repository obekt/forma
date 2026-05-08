"""Tests for built-in tools."""

import asyncio
import pytest

from forma.tools import get_registry
from forma.tools.builtin import WebSearchTool, WebFetchTool, GetCurrentTimeTool, QueryMemoryTool


@pytest.mark.asyncio
async def test_registry_has_all_builtin_tools():
    """Test that registry contains all Phase 2-3 built-in tools."""
    registry = get_registry()
    assert registry.has_tool("echo")
    assert registry.has_tool("search_web")
    assert registry.has_tool("get_current_time")
    assert registry.has_tool("query_memory")
    assert registry.has_tool("web_fetch")


@pytest.mark.asyncio
async def test_web_search_tool_definition():
    """Test web search tool has correct definition."""
    tool = WebSearchTool()

    assert tool.name == "search_web"
    assert "search" in tool.description.lower()
    assert "query" in tool.parameters["properties"]
    assert tool.parameters["properties"]["query"]["type"] == "string"
    assert "query" in tool.parameters["required"]


@pytest.mark.asyncio
async def test_web_search_tool_format():
    """Test web search tool OpenAI format."""
    tool = WebSearchTool()
    format_dict = tool.to_openai_format()

    assert format_dict["type"] == "function"
    assert format_dict["function"]["name"] == "search_web"
    assert "description" in format_dict["function"]
    assert "parameters" in format_dict["function"]


@pytest.mark.asyncio
async def test_web_fetch_tool_definition():
    """Test web_fetch tool has correct definition."""
    tool = WebFetchTool()

    assert tool.name == "web_fetch"
    assert "fetch" in tool.description.lower() or "read" in tool.description.lower()
    assert "url" in tool.parameters["properties"]
    assert tool.parameters["properties"]["url"]["type"] == "string"
    assert "url" in tool.parameters["required"]
    # Optional parameters
    assert "max_length" in tool.parameters["properties"]


@pytest.mark.asyncio
async def test_web_fetch_tool_format():
    """Test web_fetch tool OpenAI format."""
    tool = WebFetchTool()
    format_dict = tool.to_openai_format()

    assert format_dict["type"] == "function"
    assert format_dict["function"]["name"] == "web_fetch"
    assert "description" in format_dict["function"]
    assert "parameters" in format_dict["function"]


@pytest.mark.asyncio
async def test_web_fetch_empty_url():
    """Test web_fetch with empty URL."""
    tool = WebFetchTool()
    result = await tool.execute(url="")

    assert not result.success
    assert "empty" in result.error.lower()


@pytest.mark.asyncio
async def test_web_fetch_invalid_url():
    """Test web_fetch with invalid URL."""
    tool = WebFetchTool()

    # Test invalid scheme
    result = await tool.execute(url="ftp://example.com")
    assert not result.success
    assert "scheme" in result.error.lower() or "invalid" in result.error.lower()

    # Test missing domain
    result = await tool.execute(url="http://")
    assert not result.success
    assert "invalid" in result.error.lower() or "domain" in result.error.lower()


@pytest.mark.asyncio
async def test_get_current_time_tool_definition():
    """Test get_current_time tool has correct definition."""
    tool = GetCurrentTimeTool()

    assert tool.name == "get_current_time"
    assert "time" in tool.description.lower() or "date" in tool.description.lower()
    # Check optional parameters
    assert "timezone" in tool.parameters["properties"]
    assert "format" in tool.parameters["properties"]
    # No required parameters
    assert tool.parameters.get("required", []) == []


@pytest.mark.asyncio
async def test_get_current_time_tool_execution():
    """Test executing get_current_time tool."""
    tool = GetCurrentTimeTool()
    result = await tool.execute()

    assert result.success
    # Should have UTC time
    assert "utc_iso" in result.output or "utc_readable" in result.output
    assert "unix_timestamp" in result.output
    assert "date" in result.output
    # Should have day of week
    assert "day_of_week" in result.output


@pytest.mark.asyncio
async def test_get_current_time_with_timezone():
    """Test get_current_time with specific timezone."""
    tool = GetCurrentTimeTool()
    result = await tool.execute(timezone="Europe/Berlin")

    assert result.success
    assert "timezone" in result.output
    assert result.output["timezone"] == "Europe/Berlin"
    # Should have local time
    assert "local_iso" in result.output or "local_readable" in result.output


@pytest.mark.asyncio
async def test_get_current_time_invalid_timezone():
    """Test get_current_time with invalid timezone."""
    tool = GetCurrentTimeTool()
    result = await tool.execute(timezone="Invalid/Timezone")

    # Should still succeed but report timezone error
    assert result.success
    assert "timezone_error" in result.output


@pytest.mark.asyncio
async def test_get_current_time_iso_format():
    """Test get_current_time with ISO format only."""
    tool = GetCurrentTimeTool()
    result = await tool.execute(format="iso")

    assert result.success
    assert "utc_iso" in result.output
    # Should NOT have readable format
    assert "utc_readable" not in result.output


@pytest.mark.asyncio
async def test_query_memory_tool_definition():
    """Test query_memory tool has correct definition."""
    tool = QueryMemoryTool()

    assert tool.name == "query_memory"
    assert "memory" in tool.description.lower() or "query" in tool.description.lower()
    assert "query" in tool.parameters["properties"]
    assert "query" in tool.parameters["required"]
    assert "query_type" in tool.parameters["properties"]
    assert "limit" in tool.parameters["properties"]


@pytest.mark.asyncio
async def test_query_memory_without_storage():
    """Test query_memory tool fails gracefully without storage."""
    tool = QueryMemoryTool()
    # Don't set storage
    result = await tool.execute(query="test")

    assert not result.success
    assert "storage" in result.error.lower() or "not available" in result.error.lower()


@pytest.mark.asyncio
async def test_query_memory_empty_query():
    """Test query_memory with empty query."""
    tool = QueryMemoryTool()
    result = await tool.execute(query="")

    assert not result.success
    assert "empty" in result.error.lower()


@pytest.mark.asyncio
async def test_tool_enabled_by_default():
    """Test that all built-in tools are enabled by default."""
    registry = get_registry()

    assert registry.is_enabled("echo")
    assert registry.is_enabled("search_web")
    assert registry.is_enabled("get_current_time")
    assert registry.is_enabled("query_memory")
    assert registry.is_enabled("web_fetch")


@pytest.mark.asyncio
async def test_tool_can_be_disabled():
    """Test that tools can be disabled."""
    registry = get_registry()

    # Disable a tool
    registry.set_enabled("echo", enabled=False)
    assert not registry.is_enabled("echo")

    # Re-enable
    registry.set_enabled("echo", enabled=True)
    assert registry.is_enabled("echo")


@pytest.mark.asyncio
async def test_get_all_tools():
    """Test getting all registered tools."""
    registry = get_registry()
    tools = registry.get_all_tools()

    assert len(tools) >= 5  # echo + 4 new tools
    tool_names = [t.name for t in tools]
    assert "echo" in tool_names
    assert "search_web" in tool_names
    assert "get_current_time" in tool_names
    assert "query_memory" in tool_names
    assert "web_fetch" in tool_names


@pytest.mark.asyncio
async def test_get_openai_tools():
    """Test getting tools in OpenAI format."""
    registry = get_registry()
    tools = registry.get_openai_tools()

    assert len(tools) >= 5
    for tool_def in tools:
        assert tool_def["type"] == "function"
        assert "name" in tool_def["function"]
        assert "description" in tool_def["function"]
        assert "parameters" in tool_def["function"]


# Live tests (can be skipped in CI)
@pytest.mark.skipif(
    True,  # Skip by default, enable for live testing
    reason="Live web search test, enable manually for integration testing",
)
@pytest.mark.asyncio
async def test_web_search_live():
    """Test live web search (requires network)."""
    tool = WebSearchTool()
    result = await tool.execute(query="Python programming language", num_results=3)

    assert result.success
    assert "results" in result.output
    assert result.output["count"] > 0

    # Check result structure
    first_result = result.output["results"][0]
    assert "title" in first_result
    assert "url" in first_result
    assert "snippet" in first_result


@pytest.mark.skipif(
    True,  # Skip by default, enable for live testing
    reason="Live web fetch test, enable manually for integration testing",
)
@pytest.mark.asyncio
async def test_web_fetch_live():
    """Test live web fetch (requires network)."""
    tool = WebFetchTool()
    result = await tool.execute(url="https://example.com")

    assert result.success
    assert "content" in result.output
    assert "url" in result.output
    assert len(result.output["content"]) > 0

    # Check metadata
    assert result.metadata["url"] == "https://example.com"
    assert "status_code" in result.metadata


if __name__ == "__main__":
    asyncio.run(test_registry_has_all_builtin_tools())
    asyncio.run(test_get_current_time_tool_execution())
    asyncio.run(test_get_current_time_with_timezone())
    asyncio.run(test_query_memory_without_storage())
    asyncio.run(test_tool_enabled_by_default())
    print("All built-in tool tests passed!")
