"""
VPS-CC-MCP Tools Package.

Importing this module registers all tools in the global registry.
"""

# Import all tool modules to trigger registration
from tools import project
from tools import files
from tools import code
from tools import services
from tools import vps
from tools import bash

# Re-export registry functions
from tools.base import (
    get_tool,
    get_all_tools,
    list_tools,
    create_tool,
    BaseTool,
    ToolMetadata,
    register_tool,
)

__all__ = [
    "get_tool",
    "get_all_tools",
    "list_tools",
    "create_tool",
    "BaseTool",
    "ToolMetadata",
    "register_tool",
]
