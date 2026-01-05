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
from registrytools.registry.models import (
    SearchMethod,
    ToolMetadata,
    ToolSearchResult,
)

# 导入工具注册表
from registrytools.registry.registry import ToolRegistry

# 导入搜索算法
from registrytools.search import SearchAlgorithm

# 导入存储层
from registrytools.storage import JSONStorage, SQLiteStorage, ToolStorage

__all__ = [
    "__version__",
    "__author__",
    "__license__",
    # 数据模型
    "SearchMethod",
    "ToolMetadata",
    "ToolSearchResult",
    # 搜索算法
    "SearchAlgorithm",
    # 工具注册表
    "ToolRegistry",
    # 存储层
    "ToolStorage",
    "JSONStorage",
    "SQLiteStorage",
]
