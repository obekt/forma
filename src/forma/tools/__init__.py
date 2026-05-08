"""Server-side tool execution for Forma.

This module provides the infrastructure for executing tools server-side,
allowing models to request tool calls and Forma to execute them automatically
before returning the final response.

Key components:
- Tool: Base class for defining tools
- ToolResult: Result container for tool execution
- ToolRegistry: Registry for managing available tools
- ToolExecutor: Execution loop for tool calling
"""

from forma.tools.base import Tool, ToolResult
from forma.tools.executor import ToolExecutor, ToolExecutionResult
from forma.tools.registry import ToolRegistry, get_registry

__all__ = [
    "Tool",
    "ToolResult",
    "ToolRegistry",
    "ToolExecutor",
    "ToolExecutionResult",
    "get_registry",
]
