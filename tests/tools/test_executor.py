"""Tests for tool execution system."""

import asyncio
import pytest

from forma.tools import ToolExecutor, ToolResult, get_registry
from forma.tools.base import ToolCall, EchoTool


@pytest.mark.asyncio
async def test_registry_has_echo_tool():
    """Test that registry contains the echo tool."""
    registry = get_registry()
    assert registry.has_tool("echo")
    assert registry.is_enabled("echo")


@pytest.mark.asyncio
async def test_echo_tool_execution():
    """Test executing the echo tool directly."""
    tool = EchoTool()
    result = await tool.execute(message="Hello, world!")

    assert result.success
    assert result.output["echoed"] == "Hello, world!"


@pytest.mark.asyncio
async def test_tool_call_parsing():
    """Test parsing tool call from OpenAI format."""
    raw_call = {
        "id": "call_abc123",
        "type": "function",
        "function": {"name": "echo", "arguments": '{"message": "test message"}'},
    }

    tool_call = ToolCall.from_openai_format(raw_call)

    assert tool_call.id == "call_abc123"
    assert tool_call.name == "echo"
    assert tool_call.arguments == {"message": "test message"}


@pytest.mark.asyncio
async def test_executor_execute_single_tool():
    """Test executor executing a single tool call."""
    registry = get_registry()
    executor = ToolExecutor(registry=registry)

    tool_call = ToolCall(id="call_test", name="echo", arguments={"message": "Executor test"})

    result = await executor.execute_tool(tool_call)

    assert result.success
    assert result.output["echoed"] == "Executor test"


@pytest.mark.asyncio
async def test_executor_tool_not_found():
    """Test executor handling tool not found."""
    registry = get_registry()
    executor = ToolExecutor(registry=registry)

    tool_call = ToolCall(id="call_missing", name="nonexistent_tool", arguments={})

    result = await executor.execute_tool(tool_call)

    assert not result.success
    assert "not found" in result.error


@pytest.mark.asyncio
async def test_executor_tool_missing_required_param():
    """Test executor handling missing required parameter."""
    registry = get_registry()
    executor = ToolExecutor(registry=registry)

    # Call echo without required 'message' parameter
    tool_call = ToolCall(
        id="call_no_param",
        name="echo",
        arguments={},  # Missing 'message'
    )

    result = await executor.execute_tool(tool_call)

    assert not result.success
    assert "Missing required parameter" in result.error


@pytest.mark.asyncio
async def test_executor_extract_tool_calls():
    """Test extracting tool calls from API response."""
    registry = get_registry()
    executor = ToolExecutor(registry=registry)

    response = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {"name": "echo", "arguments": '{"message": "first"}'},
                        },
                        {
                            "id": "call_2",
                            "type": "function",
                            "function": {"name": "echo", "arguments": '{"message": "second"}'},
                        },
                    ],
                }
            }
        ]
    }

    tool_calls = executor.extract_tool_calls(response)

    assert len(tool_calls) == 2
    assert tool_calls[0].name == "echo"
    assert tool_calls[0].arguments["message"] == "first"
    assert tool_calls[1].name == "echo"
    assert tool_calls[1].arguments["message"] == "second"


@pytest.mark.asyncio
async def test_executor_extract_no_tool_calls():
    """Test extracting from response without tool calls."""
    registry = get_registry()
    executor = ToolExecutor(registry=registry)

    response = {
        "choices": [
            {"message": {"role": "assistant", "content": "Final response without tool calls"}}
        ]
    }

    tool_calls = executor.extract_tool_calls(response)

    assert len(tool_calls) == 0


@pytest.mark.asyncio
async def test_tool_result_to_content():
    """Test ToolResult content conversion."""
    # Success with dict output
    result1 = ToolResult(success=True, output={"key": "value"})
    assert result1.to_content() == '{"key": "value"}'

    # Success with string output
    result2 = ToolResult(success=True, output="plain text")
    assert result2.to_content() == "plain text"

    # Error
    result3 = ToolResult(success=False, error="Something went wrong")
    content = result3.to_content()
    assert "error" in content
    assert "Something went wrong" in content


@pytest.mark.asyncio
async def test_tool_to_openai_format():
    """Test converting tool to OpenAI format."""
    tool = EchoTool()
    format_dict = tool.to_openai_format()

    assert format_dict["type"] == "function"
    assert format_dict["function"]["name"] == "echo"
    assert format_dict["function"]["description"] == tool.description
    assert "parameters" in format_dict["function"]


# Integration test for full tool loop (requires mock upstream)
@pytest.mark.asyncio
async def test_executor_loop_simple():
    """Test simple tool execution loop with mock upstream."""
    registry = get_registry()
    executor = ToolExecutor(registry=registry, max_iterations=3)

    # Mock responses - use a mutable list to track calls
    call_count = [0]

    async def mock_forward(messages, tools, tool_choice):
        """Mock upstream that returns tool call then final response."""
        call_count[0] += 1

        if call_count[0] == 1:
            # First call: request tool
            return {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call_mock",
                                    "type": "function",
                                    "function": {
                                        "name": "echo",
                                        "arguments": '{"message": "test loop"}',
                                    },
                                }
                            ],
                        }
                    }
                ]
            }
        else:
            # Second call: final response
            return {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Final response after tool execution",
                        }
                    }
                ]
            }

    messages = [{"role": "user", "content": "Test message"}]
    tools = [
        {"type": "function", "function": {"name": "echo", "description": "Echo", "parameters": {}}}
    ]

    result = await executor.execute_loop(
        messages=messages,
        tools=tools,
        forward_request=mock_forward,
    )

    assert result.iterations == 1
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].name == "echo"
    assert result.tool_calls[0].result.success
    assert not result.max_iterations_reached
    assert "Final response" in result.response["choices"][0]["message"]["content"]


if __name__ == "__main__":
    asyncio.run(test_registry_has_echo_tool())
    asyncio.run(test_echo_tool_execution())
    asyncio.run(test_tool_call_parsing())
    asyncio.run(test_executor_execute_single_tool())
    asyncio.run(test_executor_loop_simple())
    print("All tests passed!")
