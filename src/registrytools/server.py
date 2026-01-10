"""
MCP 服务器核心模块

使用 FastMCP 框架实现 MCP Tool Registry Server。

Copyright (c) 2026 Maric
License: MIT
"""

import json
import logging
import os
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from fastmcp import FastMCP

from registrytools.registry.models import SearchMethod, ToolMetadata
from registrytools.registry.registry import ToolRegistry
from registrytools.search.bm25_search import BM25Search
from registrytools.search.embedding_search import EmbeddingSearch
from registrytools.search.regex_search import RegexSearch
from registrytools.storage.base import ToolStorage
from registrytools.storage.json_storage import JSONStorage
from registrytools.storage.sqlite_storage import SQLiteStorage

if TYPE_CHECKING:
    from registrytools.auth.middleware import APIKeyAuthMiddleware

# ============================================================
# MCP 工具和资源注册 (TASK-708: 重构提取公共函数)
# ============================================================

logger = logging.getLogger(__name__)


def get_server_description() -> str:
    """
    获取 MCP 服务器描述

    从环境变量 REGISTRYTOOLS_DESCRIPTION 读取自定义描述，
    如果未设置或为空，则使用默认描述。

    优先级：
        1. 环境变量 REGISTRYTOOLS_DESCRIPTION（去除首尾空格后非空）
        2. 默认描述

    Returns:
        服务器描述字符串

    Examples:
        >>> # 环境变量未设置
        >>> get_server_description()
        'RegistryTools - MCP 工具注册表服务器...'

        >>> # 环境变量设置为自定义值
        >>> get_server_description()  # REGISTRYTOOLS_DESCRIPTION="我的工具服务器"
        '我的工具服务器'
    """
    custom_desc = os.getenv("REGISTRYTOOLS_DESCRIPTION", "").strip()

    if custom_desc:
        logger.info(f"使用自定义服务器描述: {custom_desc}")
        return custom_desc

    # 使用默认描述
    default_description = (
        "RegistryTools - MCP 工具注册表服务器\n\n"
        "提供通用工具搜索与发现能力，支持 Regex、BM25、Embedding 多种搜索算法。\n"
        "可作为任何 MCP 客户端（Claude Desktop、Cursor、DeepThinking Agent 等）的工具目录管理器。\n\n"
        "核心功能：\n"
        "- 工具注册与元数据管理\n"
        "- 多算法搜索（Regex/BM25/Embedding）\n"
        "- 分类浏览与统计信息\n"
        "- 动态工具注册 API"
    )
    logger.debug("使用默认服务器描述")
    return default_description


def _register_mcp_tools(
    mcp: FastMCP,
    registry: ToolRegistry,
    storage: ToolStorage,
    save_func: Callable[[ToolMetadata], None],
    auth_middleware: "APIKeyAuthMiddleware | None" = None,
) -> None:
    """
    注册 MCP 工具和资源到 FastMCP 服务器

    这是一个内部辅助函数，用于消除 create_server() 和
    create_server_with_sqlite() 之间的代码重复。

    Args:
        mcp: FastMCP 服务器实例
        registry: 工具注册表实例
        storage: 存储层实例
        save_func: 保存工具到存储的函数
        auth_middleware: API Key 认证中间件（可选）
    """
    # ========================================================
    # MCP 工具: search_tools (Phase 15: API Key 认证)
    # ========================================================

    @mcp.tool()
    def search_tools(
        query: str,
        search_method: str = "bm25",
        limit: int = 5,
    ) -> str:
        """
        搜索可用的 MCP 工具

        根据查询字符串在已注册的工具中搜索匹配项。

        Args:
            query: 搜索查询字符串
            search_method: 搜索方法 (regex/bm25)，默认 bm25
            limit: 返回结果数量，默认 5

        Returns:
            匹配的工具列表，JSON 格式字符串

        Raises:
            ValueError: 如果搜索方法无效
            PermissionError: 如果认证失败（仅 HTTP 模式）
        """
        try:
            method = SearchMethod(search_method)
        except ValueError as err:
            raise ValueError(f"无效的搜索方法: {search_method}。支持的方法: regex, bm25") from err

        # 执行搜索
        results = registry.search(query, method=method, limit=limit)

        # 转换为字典列表
        output = []
        for result in results:
            output.append(
                {
                    "tool_name": result.tool_name,
                    "description": result.description,
                    "score": result.score,
                    "match_reason": result.match_reason,
                }
            )

        return json.dumps(output, ensure_ascii=False, indent=2)

    # ========================================================
    # MCP 工具: get_tool_definition (Phase 15: API Key 认证)
    # ========================================================

    @mcp.tool()
    def get_tool_definition(tool_name: str) -> str:
        """
        获取指定工具的完整定义

        返回工具的完整元数据，包括输入输出 Schema。

        Args:
            tool_name: 工具名称

        Returns:
            工具的完整定义，JSON 格式字符串

        Raises:
            ValueError: 如果工具不存在
            PermissionError: 如果认证失败（仅 HTTP 模式）
        """
        tool = registry.get_tool(tool_name)
        if tool is None:
            raise ValueError(f"工具不存在: {tool_name}")

        # 转换为字典
        definition = tool.model_dump(mode="json", exclude_none=True)

        return json.dumps(definition, ensure_ascii=False, indent=2)

    # ========================================================
    # MCP 工具: list_tools_by_category (Phase 15: API Key 认证)
    # ========================================================

    @mcp.tool()
    def list_tools_by_category(category: str, limit: int = 20) -> str:
        """
        按类别列出工具

        列出指定类别下的所有工具。

        Args:
            category: 工具类别，使用 "all" 列出所有类别
            limit: 返回结果数量，默认 20

        Returns:
            该类别下的工具列表，JSON 格式字符串

        Raises:
            PermissionError: 如果认证失败（仅 HTTP 模式）
        """
        if category.lower() == "all":
            # 列出所有类别
            categories = registry.list_categories()
            result = {"categories": categories}
        else:
            # 按类别列出工具
            tools = registry.list_tools(category=category)[:limit]
            result = {
                "category": category,
                "count": len(tools),
                "tools": [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "tags": list(tool.tags),
                    }
                    for tool in tools
                ],
            }

        return json.dumps(result, ensure_ascii=False, indent=2)

    # ========================================================
    # MCP 工具: register_tool (Phase 15: API Key 认证)
    # ========================================================

    @mcp.tool()
    def register_tool(
        name: str,
        description: str,
        category: str | None = None,
        tags: list[str] | None = None,
    ) -> str:
        """
        动态注册新工具

        向工具注册表中添加一个新的工具元数据。

        Args:
            name: 工具名称（唯一标识符）
            description: 工具描述
            category: 工具类别（可选）
            tags: 工具标签列表（可选）

        Returns:
            注册结果，JSON 格式字符串

        Raises:
            ValueError: 如果工具名称已存在
            PermissionError: 如果认证失败或权限不足（仅 HTTP 模式）
        """
        # 检查工具是否已存在
        if registry.get_tool(name) is not None:
            raise ValueError(f"工具已存在: {name}")

        # 创建工具元数据
        tool = ToolMetadata(
            name=name,
            description=description,
            category=category,
            tags=set(tags) if tags else set(),
        )

        # 注册到注册表
        registry.register(tool)

        # 保存到存储
        save_func(tool)

        result = {
            "success": True,
            "message": f"工具已注册: {name}",
            "tool": {
                "name": tool.name,
                "description": tool.description,
                "category": tool.category,
                "tags": list(tool.tags),
            },
        }

        return json.dumps(result, ensure_ascii=False, indent=2)

    # ========================================================
    # 资源: 工具统计信息
    # ========================================================

    @mcp.resource("registry://stats")
    def get_stats() -> str:
        """
        获取工具注册表统计信息

        Returns:
            统计信息，JSON 格式字符串
        """
        stats = {
            "total_tools": registry.tool_count,
            "total_categories": registry.category_count,
            "categories": registry.list_categories(),
            "most_used": [
                {"name": t.name, "description": t.description, "use_count": t.use_frequency}
                for t in registry.get_most_used(5)
            ],
        }

        return json.dumps(stats, ensure_ascii=False, indent=2)

    # ========================================================
    # 资源: 类别列表
    # ========================================================

    @mcp.resource("registry://categories")
    def get_categories() -> str:
        """
        获取所有工具类别

        Returns:
            类别列表，JSON 格式字符串
        """
        categories = registry.list_categories()
        result = {
            "count": len(categories),
            "categories": categories,
        }

        return json.dumps(result, ensure_ascii=False, indent=2)


# ============================================================
# MCP 服务器创建函数 (Phase 15: 添加认证支持)
# ============================================================


def create_server(
    data_path: Path,
    auth_middleware: "APIKeyAuthMiddleware | None" = None,
) -> FastMCP:
    """
    创建并配置 MCP 服务器

    使用 JSON 存储后端。

    Args:
        data_path: 数据目录路径
        auth_middleware: API Key 认证中间件（可选，仅 HTTP 模式使用）

    Returns:
        配置好的 FastMCP 服务器实例
    """
    # 创建 FastMCP 服务器
    mcp = FastMCP("RegistryTools", instructions=get_server_description())

    # 初始化存储层
    storage = JSONStorage(data_path / "tools.json")

    # 初始化工具注册表
    registry = ToolRegistry()

    # 加载已保存的工具
    if storage.validate():
        tools = storage.load_all()
        registry.register_many(tools)

    # 加载默认工具集（如果注册表为空）(TASK-603)
    from registrytools.defaults import load_default_tools_if_empty

    default_tools = load_default_tools_if_empty(
        tool_count=registry.tool_count,
        storage_path=data_path / "tools.json",
        auto_save=True,
    )
    if default_tools:
        registry.register_many(default_tools)

    # 注册搜索算法
    registry.register_searcher(SearchMethod.REGEX, RegexSearch(case_sensitive=False))
    registry.register_searcher(SearchMethod.BM25, BM25Search())
    registry.register_searcher(SearchMethod.EMBEDDING, EmbeddingSearch())

    # 重建搜索索引
    registry.rebuild_indexes()

    # 注册 MCP 工具和资源 (TASK-708: 使用公共函数, Phase 15: 添加认证支持)
    _register_mcp_tools(mcp, registry, storage, storage.save, auth_middleware)

    return mcp


# ============================================================
# 辅助函数 (Phase 15: 添加认证支持)
# ============================================================


def create_server_with_sqlite(
    data_path: Path,
    auth_middleware: "APIKeyAuthMiddleware | None" = None,
) -> FastMCP:
    """
    创建使用 SQLite 存储的 MCP 服务器

    Args:
        data_path: 数据目录路径
        auth_middleware: API Key 认证中间件（可选，仅 HTTP 模式使用）

    Returns:
        配置好的 FastMCP 服务器实例
    """
    # 创建 FastMCP 服务器
    mcp = FastMCP("RegistryTools", instructions=get_server_description())

    # 初始化 SQLite 存储
    storage = SQLiteStorage(data_path / "tools.db")

    # 初始化工具注册表
    registry = ToolRegistry()

    # 加载已保存的工具
    if storage.validate():
        tools = storage.load_all()
        registry.register_many(tools)

    # 加载默认工具集（如果注册表为空）(TASK-603)
    from registrytools.defaults import load_default_tools_if_empty

    # 获取默认工具（不自动保存到 JSON）
    default_tools = load_default_tools_if_empty(
        tool_count=registry.tool_count,
        storage_path=None,  # 不保存到 JSON
        auto_save=False,
    )
    if default_tools:
        registry.register_many(default_tools)
        # 保存到 SQLite
        storage.save_many(default_tools)

    # 注册搜索算法
    registry.register_searcher(SearchMethod.REGEX, RegexSearch(case_sensitive=False))
    registry.register_searcher(SearchMethod.BM25, BM25Search())
    registry.register_searcher(SearchMethod.EMBEDDING, EmbeddingSearch())

    # 重建搜索索引
    registry.rebuild_indexes()

    # 注册 MCP 工具和资源 (TASK-708: 使用公共函数, Phase 15: 添加认证支持)
    _register_mcp_tools(mcp, registry, storage, storage.save, auth_middleware)

    return mcp


# ============================================================
# 认证中间件创建函数 (Phase 15: 新增)
# ============================================================


def create_auth_middleware_for_server(
    data_path: Path,
    header_name: str = "X-API-Key",
) -> "APIKeyAuthMiddleware | None":
    """
    为 MCP 服务器创建认证中间件

    Args:
        data_path: 数据目录路径（API Key 存储位置）
        header_name: HTTP Header 名称，默认 X-API-Key

    Returns:
        APIKeyAuthMiddleware: 认证中间件实例
    """
    from registrytools.auth import APIKeyAuthMiddleware, APIKeyStorage

    api_key_storage = APIKeyStorage(data_path / "api_keys.db")
    return APIKeyAuthMiddleware(api_key_storage, header_name)
