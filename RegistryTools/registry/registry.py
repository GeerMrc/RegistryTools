"""
工具注册表

管理所有工具的元数据和索引，提供工具注册、搜索和使用跟踪功能。

Copyright (c) 2026 Maric
License: MIT
"""

from collections import defaultdict
from datetime import datetime
from typing import TYPE_CHECKING

from RegistryTools.registry.models import SearchMethod, ToolMetadata, ToolSearchResult
from RegistryTools.search.base import SearchAlgorithm

if TYPE_CHECKING:
    from collections.abc import Mapping


class ToolRegistry:
    """
    工具注册表核心类

    管理所有工具的元数据、搜索索引和使用统计。

    Attributes:
        _tools: 按名称索引的工具字典
        _searchers: 搜索算法实例字典
        _category_index: 按类别索引的工具名称集合
    """

    def __init__(self) -> None:
        """初始化工具注册表"""
        # 工具存储：name -> ToolMetadata
        self._tools: dict[str, ToolMetadata] = {}

        # 搜索算法实例：SearchMethod -> SearchAlgorithm
        self._searchers: dict[SearchMethod, SearchAlgorithm] = {}

        # 类别索引：category -> set[tool_name]
        self._category_index: dict[str | None, set[str]] = defaultdict(set)

        # 延迟导入搜索算法（避免循环导入）
        self._searcher_classes: dict[SearchMethod, type[SearchAlgorithm]] = {}

    def register_searcher(self, method: SearchMethod, searcher: SearchAlgorithm) -> None:
        """
        注册搜索算法实例

        Args:
            method: 搜索方法类型
            searcher: 搜索算法实例

        Raises:
            ValueError: 如果搜索器类型不匹配
        """
        if searcher.method != method:
            raise ValueError(f"搜索器类型不匹配: 期望 {method}, 实际 {searcher.method}")
        self._searchers[method] = searcher

    def get_searcher(self, method: SearchMethod) -> SearchAlgorithm | None:
        """
        获取搜索算法实例

        Args:
            method: 搜索方法类型

        Returns:
            搜索算法实例，如果未注册则返回 None
        """
        return self._searchers.get(method)

    # ============================================================
    # 工具注册功能 (TASK-302)
    # ============================================================

    def register(self, tool: ToolMetadata) -> None:
        """
        注册工具到注册表

        如果工具名称已存在，将更新其元数据。

        Args:
            tool: 工具元数据

        Examples:
            >>> registry = ToolRegistry()
            >>> tool = ToolMetadata(
            ...     name="github.create_pr",
            ...     description="Create a pull request",
            ...     tags={"github", "git"}
            ... )
            >>> registry.register(tool)
        """
        tool_name = tool.name

        # 如果工具已存在，先从类别索引中移除
        if tool_name in self._tools:
            old_tool = self._tools[tool_name]
            if old_tool.category in self._category_index:
                self._category_index[old_tool.category].discard(tool_name)

        # 添加工具
        self._tools[tool_name] = tool

        # 更新类别索引
        if tool.category:
            self._category_index[tool.category].add(tool_name)
        else:
            self._category_index[None].add(tool_name)

        # 标记搜索索引需要重建（延迟重建）
        self._invalidate_search_indexes()

    def register_many(self, tools: list[ToolMetadata]) -> None:
        """
        批量注册工具

        Args:
            tools: 工具元数据列表

        Examples:
            >>> registry = ToolRegistry()
            >>> tools = [
            ...     ToolMetadata(name="tool1", description="Tool 1"),
            ...     ToolMetadata(name="tool2", description="Tool 2"),
            ... ]
            >>> registry.register_many(tools)
        """
        for tool in tools:
            self.register(tool)

    def unregister(self, tool_name: str) -> bool:
        """
        注销工具

        Args:
            tool_name: 工具名称

        Returns:
            True 如果工具存在并被移除，False 如果工具不存在
        """
        if tool_name not in self._tools:
            return False

        tool = self._tools[tool_name]

        # 从类别索引中移除
        if tool.category in self._category_index:
            self._category_index[tool.category].discard(tool_name)

        # 从注册表中移除
        del self._tools[tool_name]

        # 标记搜索索引需要重建
        self._invalidate_search_indexes()

        return True

    # ============================================================
    # 工具查询功能
    # ============================================================

    def get_tool(self, name: str) -> ToolMetadata | None:
        """
        获取指定工具的元数据

        Args:
            name: 工具名称

        Returns:
            工具元数据，如果不存在则返回 None
        """
        return self._tools.get(name)

    def list_tools(self, category: str | None = None) -> list[ToolMetadata]:
        """
        列出所有工具

        Args:
            category: 可选，按类别筛选

        Returns:
            工具元数据列表
        """
        if category:
            tool_names = self._category_index.get(category, set())
            return [self._tools[name] for name in tool_names if name in self._tools]
        return list(self._tools.values())

    def list_categories(self) -> list[str]:
        """
        列出所有类别

        Returns:
            类别名称列表（不包括 None）
        """
        return [cat for cat in self._category_index.keys() if cat is not None]

    # ============================================================
    # 工具搜索功能 (TASK-303)
    # ============================================================

    def search(
        self,
        query: str,
        method: SearchMethod = SearchMethod.BM25,
        limit: int = 5,
    ) -> list[ToolSearchResult]:
        """
        搜索工具

        使用指定的搜索算法在工具名称、描述和标签中搜索匹配项。

        Args:
            query: 搜索查询字符串
            method: 搜索方法 (REGEX/BM25/EMBEDDING)，默认 BM25
            limit: 返回结果数量限制，默认 5

        Returns:
            搜索结果列表，按相关度降序排列

        Raises:
            ValueError: 如果搜索方法未注册

        Examples:
            >>> registry = ToolRegistry()
            >>> # ... 注册工具和搜索器 ...
            >>> results = registry.search("github pull request", method=SearchMethod.BM25)
            >>> for result in results:
            ...     print(f"{result.tool_name}: {result.score}")
        """
        if not self._tools:
            return []

        # 获取搜索器
        searcher = self._searchers.get(method)
        if searcher is None:
            raise ValueError(
                f"搜索方法 {method.value} 未注册。" f"请先使用 register_searcher() 注册搜索算法。"
            )

        # 获取工具列表
        tools = list(self._tools.values())

        # 执行搜索
        results = searcher.search(query, tools, limit)

        return results

    # ============================================================
    # 使用频率跟踪 (TASK-304)
    # ============================================================

    def update_usage(self, tool_name: str) -> bool:
        """
        更新工具使用频率和最后使用时间

        Args:
            tool_name: 工具名称

        Returns:
            True 如果工具存在并被更新，False 如果工具不存在

        Examples:
            >>> registry = ToolRegistry()
            >>> # ... 注册工具 ...
            >>> registry.update_usage("github.create_pr")
        """
        if tool_name not in self._tools:
            return False

        tool = self._tools[tool_name]
        tool.use_frequency += 1
        tool.last_used = datetime.now()

        return True

    def get_usage_stats(self) -> "Mapping[str, int]":
        """
        获取所有工具的使用频率统计

        Returns:
            工具名称到使用频率的映射
        """
        return {name: tool.use_frequency for name, tool in self._tools.items()}

    def get_most_used(self, limit: int = 10) -> list[ToolMetadata]:
        """
        获取最常用的工具

        Args:
            limit: 返回数量限制，默认 10

        Returns:
            工具元数据列表，按使用频率降序排列
        """
        tools = list(self._tools.values())
        sorted_tools = sorted(tools, key=lambda t: t.use_frequency, reverse=True)
        return sorted_tools[:limit]

    # ============================================================
    # 索引管理
    # ============================================================

    def _invalidate_search_indexes(self) -> None:
        """标记搜索索引需要重建"""
        # 索引将在下次搜索时自动重建
        # 由各个搜索算法的 search() 方法处理
        pass

    def rebuild_indexes(self) -> None:
        """
        重建所有搜索索引

        调用此方法可以强制重建所有搜索算法的索引。
        通常在批量注册工具后调用以提高首次搜索性能。
        """
        tools = list(self._tools.values())
        for searcher in self._searchers.values():
            searcher.index(tools)

    # ============================================================
    # 注册表状态
    # ============================================================

    @property
    def tool_count(self) -> int:
        """获取已注册工具数量"""
        return len(self._tools)

    @property
    def category_count(self) -> int:
        """获取类别数量"""
        return len(self._category_index) - (1 if None in self._category_index else 0)

    def is_empty(self) -> bool:
        """检查注册表是否为空"""
        return len(self._tools) == 0

    def clear(self) -> None:
        """清空注册表"""
        self._tools.clear()
        self._category_index.clear()
        self._invalidate_search_indexes()
