"""
RegistryTools - MCP Tool Registry Server

一个独立的 MCP Tool Registry Server，提供通用的工具搜索和发现能力。

Copyright (c) 2026 Maric
License: MIT
"""

__version__ = "0.1.0"
__author__ = "Maric"
__license__ = "MIT"

# 导入数据模型
from RegistryTools.registry.models import (
    SearchMethod,
    ToolMetadata,
    ToolSearchResult,
)

# 导入搜索算法
from RegistryTools.search import SearchAlgorithm

# TODO: 在 Phase 3 中添加 ToolRegistry
# from RegistryTools.registry.tool_registry import ToolRegistry

__all__ = [
    "__version__",
    "__author__",
    "__license__",
    "SearchMethod",
    "ToolMetadata",
    "ToolSearchResult",
    "SearchAlgorithm",
    # "ToolRegistry",  # Phase 3
]
