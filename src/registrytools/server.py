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

from fastmcp import FastMCP

from registrytools.auth.middleware import (
    APIKeyAuthMiddleware,
    APIKeyExpired,
    APIKeyInsufficientPermission,
    APIKeyInvalid,
    APIKeyPermission,
)
from registrytools.registry.models import SearchMethod, ToolMetadata
from registrytools.registry.registry import ToolRegistry
from registrytools.search.bm25_search import BM25Search
from registrytools.search.embedding_search import EmbeddingSearch
from registrytools.search.regex_search import RegexSearch
from registrytools.storage.base import ToolStorage
from registrytools.storage.json_storage import JSONStorage
from registrytools.storage.sqlite_storage import SQLiteStorage

# ============================================================
# MCP 工具和资源注册 (TASK-708: 重构提取公共函数)
# ============================================================

logger = logging.getLogger(__name__)

# ============================================================
# 常量定义 (Phase 33: 输入参数验证)
# ============================================================

# 输入参数限制
MAX_QUERY_LENGTH = 1000  # 查询字符串最大长度
MAX_LIMIT = 100  # 返回结果最大数量


# ============================================================
# 辅助函数 (Phase 33: 认证集成)
# ============================================================


def _get_api_key_from_context() -> str | None:
    """
    从请求上下文中获取 API Key

    FastMCP 在 HTTP 模式下通过环境变量或请求上下文传递 API Key。
    此函数尝试从多个来源获取 API Key：

    1. 环境变量 REGISTRYTOOLS_API_KEY（用于测试）
    2. FastMCP 请求上下文（如果可用）

    Returns:
        API Key 字符串，如果未找到则返回 None
    """
    # 优先从环境变量获取（用于测试和 CLI 场景）
    api_key = os.getenv("REGISTRYTOOLS_API_KEY")
    if api_key:
        return api_key

    # TODO: 从 FastMCP 请求上下文获取（需要进一步研究 FastMCP API）
    # 目前 FastMCP 可能不直接暴露请求上下文到工具函数
    # 如果需要完整的 HTTP 认证支持，可能需要使用 FastMCP 的中间件机制

    return None


def _check_auth(
    auth_middleware: APIKeyAuthMiddleware | None,
    required_permission: APIKeyPermission,
) -> None:
    """
    检查 API Key 认证

    Args:
        auth_middleware: 认证中间件实例
        required_permission: 需要的权限级别

    Raises:
        PermissionError: 如果认证失败或权限不足
    """
    if auth_middleware is None:
        # 未启用认证，跳过检查
        return

    # 获取 API Key
    api_key = _get_api_key_from_context()
    if api_key is None:
        raise PermissionError(
            "API Key is required (set REGISTRYTOOLS_API_KEY environment variable)"
        )

    # 执行认证检查
    try:
        auth_middleware.require_permission(api_key, required_permission)
    except APIKeyInvalid as e:
        raise PermissionError(f"Invalid API Key: {e.message}") from e
    except APIKeyExpired as e:
        raise PermissionError(f"API Key has expired: {e.message}") from e
    except APIKeyInsufficientPermission as e:
        raise PermissionError(f"Insufficient permissions: {e.message}") from e


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
        "统一的 MCP 工具注册与搜索服务，用于发现和筛选可用工具，"
        "提升任务执行工具调用准确性，复杂任务工具调用效率"
    )
    logger.debug("使用默认服务器描述")
    return default_description


def get_default_search_method() -> SearchMethod:
    """
    获取默认搜索方法

    从环境变量 REGISTRYTOOLS_SEARCH_METHOD 读取默认搜索方法，
    如果未设置或无效，则使用默认值 BM25。

    优先级：
        1. 环境变量 REGISTRYTOOLS_SEARCH_METHOD（有效值）
        2. 默认值 BM25

    Returns:
        默认搜索方法枚举值

    Examples:
        >>> # 环境变量未设置
        >>> get_default_search_method()
        <SearchMethod.BM25: 'bm25'>

        >>> # 环境变量设置为有效值
        >>> get_default_search_method()  # REGISTRYTOOLS_SEARCH_METHOD="regex"
        <SearchMethod.REGEX: 'regex'>

        >>> # 环境变量设置为无效值（回退到默认）
        >>> get_default_search_method()  # REGISTRYTOOLS_SEARCH_METHOD="invalid"
        <SearchMethod.BM25: 'bm25'>

    Note:
        embedding 方法需要安装可选依赖 sentence-transformers。
        如果设置了 embedding 但依赖未安装，将回退到 BM25 并发出警告。
    """
    custom_method = os.getenv("REGISTRYTOOLS_SEARCH_METHOD", "").strip().lower()

    if custom_method:
        try:
            method = SearchMethod(custom_method)

            # 检查 embedding 依赖
            if method == SearchMethod.EMBEDDING:
                try:
                    import sentence_transformers  # noqa: F401
                except ImportError:
                    logger.warning(
                        f"Embedding 搜索方法需要安装可选依赖，但未找到 sentence-transformers。"
                        f"使用 'pip install registry-tools[embedding]' 安装。"
                        f"回退到默认值: {SearchMethod.BM25.value}"
                    )
                    return SearchMethod.BM25

            logger.info(f"使用默认搜索方法: {method.value}")
            return method
        except ValueError:
            logger.warning(
                f"无效的搜索方法: {custom_method}，"
                f"支持的方法: {[m.value for m in SearchMethod]}，"
                f"使用默认值: {SearchMethod.BM25.value}"
            )

    # 使用默认值
    logger.debug(f"使用默认搜索方法: {SearchMethod.BM25.value}")
    return SearchMethod.BM25


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
    # MCP 工具: search_tools (Phase 15: API Key 认证, Phase 33: 认证集成)
    # ========================================================

    @mcp.tool()
    def search_tools(
        query: str,
        search_method: str | None = None,
        limit: int = 5,
    ) -> str:
        """
        搜索可用的 MCP 工具

        根据查询字符串在已注册的工具中搜索匹配项。

        Args:
            query: 搜索查询字符串
            search_method: 搜索方法 (regex/bm25/embedding)，默认使用环境变量配置
            limit: 返回结果数量，默认 5

        Returns:
            匹配的工具列表，JSON 格式字符串

        Raises:
            ValueError: 如果搜索方法无效或参数验证失败
            PermissionError: 如果认证失败（仅 HTTP 模式）
        """
        # Phase 33: 认证检查
        _check_auth(auth_middleware, APIKeyPermission.READ)

        # Phase 33: 输入参数验证
        if len(query) > MAX_QUERY_LENGTH:
            raise ValueError(f"查询长度超过限制 ({MAX_QUERY_LENGTH} 字符)")
        if limit > MAX_LIMIT:
            raise ValueError(f"返回数量超过限制 ({MAX_LIMIT})")
        if limit < 1:
            raise ValueError("返回数量必须大于 0")

        # Phase 35: 搜索方法验证（支持全局默认值）
        if search_method is None:
            # 使用全局默认搜索方法
            method = get_default_search_method()
            logger.debug(f"使用全局默认搜索方法: {method.value}")
        else:
            # 验证用户指定的搜索方法
            try:
                method = SearchMethod(search_method)
            except ValueError as err:
                supported_methods = [m.value for m in SearchMethod]
                raise ValueError(
                    f"无效的搜索方法: {search_method}。"
                    f"支持的方法: {', '.join(supported_methods)}"
                ) from err

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
    # MCP 工具: get_tool_definition (Phase 15: API Key 认证, Phase 33: 认证集成)
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
        # Phase 33: 认证检查
        _check_auth(auth_middleware, APIKeyPermission.READ)

        # Phase 33: 输入参数验证
        if not tool_name or not tool_name.strip():
            raise ValueError("工具名称不能为空")

        tool = registry.get_tool(tool_name)
        if tool is None:
            raise ValueError(f"工具不存在: {tool_name}")

        # 转换为字典
        definition = tool.model_dump(mode="json", exclude_none=True)

        return json.dumps(definition, ensure_ascii=False, indent=2)

    # ========================================================
    # MCP 工具: list_tools_by_category (Phase 15: API Key 认证, Phase 33: 认证集成)
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
            ValueError: 如果参数验证失败
            PermissionError: 如果认证失败（仅 HTTP 模式）
        """
        # Phase 33: 认证检查
        _check_auth(auth_middleware, APIKeyPermission.READ)

        # Phase 33: 输入参数验证
        if not category or not category.strip():
            raise ValueError("类别名称不能为空")
        if limit > MAX_LIMIT:
            raise ValueError(f"返回数量超过限制 ({MAX_LIMIT})")
        if limit < 1:
            raise ValueError("返回数量必须大于 0")

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
    # MCP 工具: register_tool (Phase 15: API Key 认证, Phase 33: 认证集成)
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
            ValueError: 如果工具名称已存在或参数验证失败
            PermissionError: 如果认证失败或权限不足（仅 HTTP 模式）
        """
        # Phase 33: 认证检查（需要 WRITE 权限）
        _check_auth(auth_middleware, APIKeyPermission.WRITE)

        # Phase 33: 输入参数验证
        if not name or not name.strip():
            raise ValueError("工具名称不能为空")
        if not description or not description.strip():
            raise ValueError("工具描述不能为空")
        if len(description) > MAX_QUERY_LENGTH:
            raise ValueError(f"工具描述长度超过限制 ({MAX_QUERY_LENGTH} 字符)")

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
    # MCP 工具: unregister_tool (Phase 33: 新增)
    # ========================================================

    @mcp.tool()
    def unregister_tool(tool_name: str) -> str:
        """
        注销工具

        从工具注册表中移除指定的工具。

        Args:
            tool_name: 工具名称

        Returns:
            注销结果，JSON 格式字符串

        Raises:
            ValueError: 如果工具不存在
            PermissionError: 如果认证失败或权限不足（仅 HTTP 模式）
        """
        # Phase 33: 认证检查（需要 WRITE 权限）
        _check_auth(auth_middleware, APIKeyPermission.WRITE)

        # Phase 33: 输入参数验证
        if not tool_name or not tool_name.strip():
            raise ValueError("工具名称不能为空")

        # 检查工具是否存在
        tool = registry.get_tool(tool_name)
        if tool is None:
            raise ValueError(f"工具不存在: {tool_name}")

        # 从注册表中注销
        registry.unregister(tool_name)

        # 从存储中删除
        storage.delete(tool_name)

        result = {
            "success": True,
            "tool_name": tool_name,
            "message": f"工具 '{tool_name}' 已成功注销",
        }

        return json.dumps(result, ensure_ascii=False, indent=2)

    # ========================================================
    # MCP 工具: search_hot_tools (Phase 33: 新增)
    # ========================================================

    @mcp.tool()
    def search_hot_tools(
        query: str,
        search_method: str | None = None,
        limit: int = 5,
    ) -> str:
        """
        快速搜索热工具（性能优化）

        仅搜索热工具和温工具，跳过冷工具以提升搜索性能。
        热工具是高频使用的工具，温工具是中等频率使用的工具。

        Args:
            query: 搜索查询字符串
            search_method: 搜索方法 (regex/bm25)，默认使用环境变量配置
            limit: 返回结果数量，默认 5

        Returns:
            匹配的工具列表，JSON 格式字符串

        Raises:
            ValueError: 如果搜索方法无效或参数验证失败
            PermissionError: 如果认证失败（仅 HTTP 模式）

        Note:
            search_hot_tools 不支持 embedding 搜索方法。
            如果环境变量设置为 embedding，将自动回退到 bm25。
        """
        # Phase 33: 认证检查
        _check_auth(auth_middleware, APIKeyPermission.READ)

        # Phase 33: 输入参数验证
        if len(query) > MAX_QUERY_LENGTH:
            raise ValueError(f"查询长度超过限制 ({MAX_QUERY_LENGTH} 字符)")
        if limit > MAX_LIMIT:
            raise ValueError(f"返回数量超过限制 ({MAX_LIMIT})")
        if limit < 1:
            raise ValueError("返回数量必须大于 0")

        # Phase 35: 搜索方法验证（支持全局默认值）
        if search_method is None:
            # 使用全局默认搜索方法
            method = get_default_search_method()
            logger.debug(f"使用全局默认搜索方法: {method.value}")
        else:
            # 验证用户指定的搜索方法
            try:
                method = SearchMethod(search_method)
            except ValueError as err:
                supported_methods = [m.value for m in SearchMethod]
                raise ValueError(
                    f"无效的搜索方法: {search_method}。"
                    f"支持的方法: {', '.join(supported_methods)}"
                ) from err

        # search_hot_tools 不支持 embedding，自动回退到 bm25
        if method == SearchMethod.EMBEDDING:
            logger.warning("search_hot_tools 不支持 embedding 搜索方法，自动回退到 bm25")
            method = SearchMethod.BM25

        # 执行搜索（仅搜索热工具和温工具）
        results = registry.search_hot_warm(query, method, limit)

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
    # 资源: 工具统计信息 (Phase 33: 认证集成)
    # ========================================================

    @mcp.resource("registry://stats")
    def get_stats() -> str:
        """
        获取工具注册表统计信息

        Returns:
            统计信息，JSON 格式字符串

        Raises:
            PermissionError: 如果认证失败（仅 HTTP 模式）
        """
        # Phase 33: 认证检查
        _check_auth(auth_middleware, APIKeyPermission.READ)

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
    # 资源: 类别列表 (Phase 33: 认证集成)
    # ========================================================

    @mcp.resource("registry://categories")
    def get_categories() -> str:
        """
        获取所有工具类别

        Returns:
            类别列表，JSON 格式字符串

        Raises:
            PermissionError: 如果认证失败（仅 HTTP 模式）
        """
        # Phase 33: 认证检查
        _check_auth(auth_middleware, APIKeyPermission.READ)

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

    # 延迟注册 EmbeddingSearch（仅在配置为 embedding 时）
    # 根据配置决定是否注册，实现按需加载
    default_method = get_default_search_method()

    if default_method == SearchMethod.EMBEDDING:
        # 检查依赖是否安装
        try:
            import sentence_transformers  # noqa: F401

            # 注册延迟加载器（首次搜索时才初始化模型）
            from registrytools.search.embedding_search import EmbeddingSearchLazyLoader

            registry.register_searcher(SearchMethod.EMBEDDING, EmbeddingSearchLazyLoader())
            logger.info(
                "Embedding 搜索器已注册（延迟加载模式，首次搜索时初始化模型）。"
                f"当前配置：REGISTRYTOOLS_SEARCH_METHOD=embedding"
            )
        except ImportError:
            logger.warning(
                "Embedding 搜索方法需要安装可选依赖，但未找到 sentence-transformers。"
                "使用 'pip install registry-tools[embedding]' 安装。"
                "已禁用 Embedding 搜索器。"
            )

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

    # 延迟注册 EmbeddingSearch（仅在配置为 embedding 时）
    # 根据配置决定是否注册，实现按需加载
    default_method = get_default_search_method()

    if default_method == SearchMethod.EMBEDDING:
        # 检查依赖是否安装
        try:
            import sentence_transformers  # noqa: F401

            # 注册延迟加载器（首次搜索时才初始化模型）
            from registrytools.search.embedding_search import EmbeddingSearchLazyLoader

            registry.register_searcher(SearchMethod.EMBEDDING, EmbeddingSearchLazyLoader())
            logger.info(
                "Embedding 搜索器已注册（延迟加载模式，首次搜索时初始化模型）。"
                f"当前配置：REGISTRYTOOLS_SEARCH_METHOD=embedding"
            )
        except ImportError:
            logger.warning(
                "Embedding 搜索方法需要安装可选依赖，但未找到 sentence-transformers。"
                "使用 'pip install registry-tools[embedding]' 安装。"
                "已禁用 Embedding 搜索器。"
            )

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
