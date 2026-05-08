"""Tool registry for managing available tools."""

import logging
from typing import Any

from forma.tools.base import Tool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for managing available tools.

    Tools can be registered:
    - Programmatically via register_tool()
    - From configuration file (Phase 3)
    - As Python plugins (Phase 4)

    The registry is used by ToolExecutor to:
    - Get tool by name for execution
    - Get all tool definitions for API request
    - Validate tool existence before execution
    """

    def __init__(self, storage: Any = None) -> None:
        """Initialize empty registry.

        Args:
            storage: Optional storage instance for tools that need it (e.g., query_memory)
        """
        self._tools: dict[str, Tool] = {}
        self._enabled_tools: set[str] = set()
        self._storage = storage

    def register_tool(self, tool: Tool, enabled: bool = True) -> None:
        """Register a tool instance.

        Args:
            tool: Tool instance to register
            enabled: Whether the tool is enabled by default
        """
        if tool.name in self._tools:
            logger.warning(f"Tool '{tool.name}' already registered, replacing")

        self._tools[tool.name] = tool
        if enabled:
            self._enabled_tools.add(tool.name)

        logger.info(f"Registered tool: {tool.name} (enabled={enabled})")

    def unregister_tool(self, name: str) -> bool:
        """Remove a tool from the registry.

        Args:
            name: Tool name to remove

        Returns:
            True if tool was removed, False if not found
        """
        if name in self._tools:
            del self._tools[name]
            self._enabled_tools.discard(name)
            logger.info(f"Unregistered tool: {name}")
            return True
        return False

    def get_tool(self, name: str) -> Tool | None:
        """Get a tool by name.

        Args:
            name: Tool name

        Returns:
            Tool instance or None if not found
        """
        return self._tools.get(name)

    def has_tool(self, name: str) -> bool:
        """Check if a tool exists.

        Args:
            name: Tool name

        Returns:
            True if tool exists
        """
        return name in self._tools

    def is_enabled(self, name: str) -> bool:
        """Check if a tool is enabled.

        Args:
            name: Tool name

        Returns:
            True if tool is enabled
        """
        return name in self._enabled_tools

    def set_enabled(self, name: str, enabled: bool) -> bool:
        """Enable or disable a tool.

        Args:
            name: Tool name
            enabled: Whether to enable or disable

        Returns:
            True if tool exists and status was changed
        """
        if name not in self._tools:
            return False

        if enabled:
            self._enabled_tools.add(name)
        else:
            self._enabled_tools.discard(name)

        logger.info(f"Tool '{name}' enabled={enabled}")
        return True

    def get_all_tools(self) -> list[Tool]:
        """Get all registered tools.

        Returns:
            List of all Tool instances
        """
        return list(self._tools.values())

    def get_enabled_tools(self) -> list[Tool]:
        """Get all enabled tools.

        Returns:
            List of enabled Tool instances
        """
        return [self._tools[name] for name in self._enabled_tools if name in self._tools]

    def get_openai_tools(self, include_disabled: bool = False) -> list[dict[str, Any]]:
        """Get tool definitions in OpenAI format.

        Args:
            include_disabled: Whether to include disabled tools

        Returns:
            List of tool definitions in OpenAI format
        """
        tools = self.get_all_tools() if include_disabled else self.get_enabled_tools()
        return [tool.to_openai_format() for tool in tools]

    def get_tool_names(self) -> list[str]:
        """Get all registered tool names.

        Returns:
            List of tool names
        """
        return list(self._tools.keys())

    def set_storage(self, storage: Any) -> None:
        """Set storage reference for tools that need it.

        Args:
            storage: Storage instance (GrafitoDB)
        """
        self._storage = storage
        # Update any tools that need storage
        for tool in self._tools.values():
            if hasattr(tool, "set_storage"):
                tool.set_storage(storage)
        logger.info("Storage reference set for tool registry")

    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()
        self._enabled_tools.clear()
        logger.info("Tool registry cleared")


# Global registry instance (initialized lazily)
_global_registry: ToolRegistry | None = None


def get_registry(storage: Any = None) -> ToolRegistry:
    """Get the global tool registry.

    Args:
        storage: Optional storage instance to pass to tools that need it

    Returns:
        Global ToolRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry(storage=storage)
        # Register built-in tools
        _register_builtin_tools(_global_registry)
    elif storage is not None:
        # Update storage if registry already exists
        _global_registry.set_storage(storage)
    return _global_registry


def _register_builtin_tools(registry: ToolRegistry) -> None:
    """Register built-in tools.

    Phase 1: echo tool for testing.
    Phase 2: web_search, query_memory, get_current_time.
    Phase 3: web_fetch for reading websites.
    """
    from forma.tools.base import EchoTool
    from forma.tools.builtin import WebSearchTool, WebFetchTool, GetCurrentTimeTool, QueryMemoryTool

    # Phase 1: Testing tool
    registry.register_tool(EchoTool(), enabled=True)

    # Phase 2: Built-in tools
    registry.register_tool(WebSearchTool(), enabled=True)
    registry.register_tool(GetCurrentTimeTool(), enabled=True)
    registry.register_tool(QueryMemoryTool(), enabled=True)

    # Phase 3: Web fetch tool
    registry.register_tool(WebFetchTool(), enabled=True)
