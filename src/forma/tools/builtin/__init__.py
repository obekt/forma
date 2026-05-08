"""Built-in tools for Forma.

Phase 1: echo tool (for testing)
Phase 2: web_search, query_memory, get_current_time
Phase 3: web_fetch (read websites)
Phase 4: execute_code, read_file (planned)
"""

from forma.tools.builtin.web_search import WebSearchTool
from forma.tools.builtin.web_fetch import WebFetchTool
from forma.tools.builtin.time import GetCurrentTimeTool
from forma.tools.builtin.memory_query import QueryMemoryTool

__all__ = [
    "WebSearchTool",
    "WebFetchTool",
    "GetCurrentTimeTool",
    "QueryMemoryTool",
]
