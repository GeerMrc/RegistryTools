"""
工具注册表

管理所有工具的元数据和索引，提供工具注册、搜索和使用跟踪功能。

Copyright (c) 2026 Maric
License: MIT
"""

import threading
from collections import defaultdict
from datetime import datetime
from typing import TYPE_CHECKING

from registrytools.defaults import (
    ENABLE_DOWNGRADE,
    HOT_TOOL_INACTIVE_DAYS,
    HOT_TOOL_THRESHOLD,
    WARM_TOOL_INACTIVE_DAYS,
    WARM_TOOL_THRESHOLD,
)
from registrytools.registry.models import SearchMethod, ToolMetadata, ToolSearchResult
from registrytools.search.base import SearchAlgorithm

if TYPE_CHECKING:
    from collections.abc import Mapping

    from registrytools.registry.models import ToolTemperature
    from registrytools.storage.base import ToolStorage


class ToolRegistry:
    """
    工具注册表核心类

    管理所有工具的元数据、搜索索引和使用统计。

    Attributes:
        _tools: 按名称索引的工具字典
        _hot_tools: 热工具字典
        _warm_tools: 温工具字典
        _cold_tools: 冷工具字典
        _searchers: 搜索算法实例字典
        _category_index: 按类别索引的工具名称集合
        _temp_lock: 温度层锁（线程安全）
    """

    def __init__(self) -> None:
        """初始化工具注册表"""
        # 主工具存储：name -> ToolMetadata
        self._tools: dict[str, ToolMetadata] = {}

        # 冷热分层存储 (TASK-802)
        self._hot_tools: dict[str, ToolMetadata] = {}
        self._warm_tools: dict[str, ToolMetadata] = {}
        self._cold_tools: dict[str, ToolMetadata] = {}

        # 温度锁：保护分层存储的并发访问
        self._temp_lock = threading.RLock()

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
    # 冷热工具分类方法 (TASK-802)
    # ============================================================

    def _classify_tool_temperature(self, tool: ToolMetadata) -> "ToolTemperature":
        """
        根据使用频率分类工具温度 (TASK-802)

        Args:
            tool: 工具元数据

        Returns:
            工具温度级别
        """
        from registrytools.registry.models import ToolTemperature

        if tool.use_frequency >= HOT_TOOL_THRESHOLD:
            return ToolTemperature.HOT
        elif tool.use_frequency >= WARM_TOOL_THRESHOLD:
            return ToolTemperature.WARM
        else:
            return ToolTemperature.COLD

    def _add_to_temperature_layer(self, tool: ToolMetadata, temp: "ToolTemperature") -> None:
        """
        将工具添加到对应的温度层 (TASK-802)

        Args:
            tool: 工具元数据
            temp: 温度级别
        """
        tool_name = tool.name

        # 从所有层移除（确保工具只在一个层）
        self._hot_tools.pop(tool_name, None)
        self._warm_tools.pop(tool_name, None)
        self._cold_tools.pop(tool_name, None)

        # 添加到对应层
        if temp.value == "hot":
            self._hot_tools[tool_name] = tool
        elif temp.value == "warm":
            self._warm_tools[tool_name] = tool
        else:
            self._cold_tools[tool_name] = tool

    def _check_downgrade_tool(self, tool: ToolMetadata) -> bool:
        """
        检查工具是否需要降级 (TASK-802)

        Args:
            tool: 工具元数据

        Returns:
            True 如果需要降级，否则 False
        """
        from registrytools.registry.models import ToolTemperature

        # 如果未启用降级机制，直接返回 False
        if not ENABLE_DOWNGRADE:
            return False

        # 如果工具没有使用记录，不需要降级
        if tool.last_used is None:
            return False

        # 计算未使用天数
        days_since_last_use = (datetime.now() - tool.last_used).days

        # 热工具降级检查
        if tool.temperature == ToolTemperature.HOT:
            return days_since_last_use >= HOT_TOOL_INACTIVE_DAYS

        # 温工具降级检查
        if tool.temperature == ToolTemperature.WARM:
            return days_since_last_use >= WARM_TOOL_INACTIVE_DAYS

        # 冷工具不需要降级
        return False

    def _downgrade_tool(self, tool_name: str) -> bool:
        """
        降级工具温度 (TASK-802)

        Args:
            tool_name: 工具名称

        Returns:
            True 如果降级成功，False 如果工具不存在或已经是冷工具
        """
        from registrytools.registry.models import ToolTemperature

        tool = self._tools.get(tool_name)
        if not tool:
            return False

        # 已经是冷工具，无需降级
        if tool.temperature == ToolTemperature.COLD:
            return False

        # 降级：热 -> 温 -> 冷
        if tool.temperature == ToolTemperature.HOT:
            new_temp = ToolTemperature.WARM
        else:  # WARM
            new_temp = ToolTemperature.COLD

        # 更新工具温度
        tool.temperature = new_temp

        # 移动到新温度层
        self._add_to_temperature_layer(tool, new_temp)

        return True

    def load_hot_tools(self, storage: "ToolStorage", limit: int | None = None) -> int:
        """
        从存储预加载热工具 (TASK-802)

        Args:
            storage: 存储实例
            limit: 最大加载数量，None 表示加载所有热工具

        Returns:
            实际加载的热工具数量
        """
        from registrytools.registry.models import ToolTemperature

        # 从存储加载热工具
        hot_tools_from_storage = storage.load_by_temperature(ToolTemperature.HOT, limit)

        # 注册到内存
        for tool in hot_tools_from_storage:
            if tool.name not in self._tools:
                # 确保温度正确
                tool.temperature = ToolTemperature.HOT
                self.register(tool)

        return len(hot_tools_from_storage)

    # ============================================================
    # 工具注册功能 (TASK-302)
    # ============================================================

    def register(self, tool: ToolMetadata) -> None:
        """
        注册工具到注册表

        如果工具名称已存在，将更新其元数据。
        自动分类工具温度并添加到对应层 (TASK-802)。

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

        # 如果工具已存在，先从类别索引和温度层中移除
        if tool_name in self._tools:
            old_tool = self._tools[tool_name]
            if old_tool.category in self._category_index:
                self._category_index[old_tool.category].discard(tool_name)
            # 从温度层移除
            self._hot_tools.pop(tool_name, None)
            self._warm_tools.pop(tool_name, None)
            self._cold_tools.pop(tool_name, None)

        # 添加工具
        self._tools[tool_name] = tool

        # 更新类别索引
        if tool.category:
            self._category_index[tool.category].add(tool_name)
        else:
            self._category_index[None].add(tool_name)

        # 自动分类工具温度并添加到对应层 (TASK-802)
        with self._temp_lock:
            temperature = self._classify_tool_temperature(tool)
            tool.temperature = temperature
            self._add_to_temperature_layer(tool, temperature)

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

        # 从温度层中移除 (TASK-802)
        with self._temp_lock:
            self._hot_tools.pop(tool_name, None)
            self._warm_tools.pop(tool_name, None)
            self._cold_tools.pop(tool_name, None)

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

    def search_hot_warm(
        self,
        query: str,
        method: SearchMethod = SearchMethod.BM25,
        limit: int = 5,
    ) -> list[ToolSearchResult]:
        """
        优先搜索热工具和温工具 (TASK-802)

        性能优化的搜索方法，仅在热工具和温工具中搜索，
        避免冷工具延迟加载开销。

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
            >>> # 快速搜索热+温工具（性能优化）
            >>> results = registry.search_hot_warm("git", method=SearchMethod.BM25)
        """
        # 获取搜索器
        searcher = self._searchers.get(method)
        if searcher is None:
            raise ValueError(
                f"搜索方法 {method.value} 未注册。" f"请先使用 register_searcher() 注册搜索算法。"
            )

        # 获取热工具和温工具（合并列表）
        hot_tools = list(self._hot_tools.values())
        warm_tools = list(self._warm_tools.values())

        # 如果没有热工具和温工具，返回空结果
        if not hot_tools and not warm_tools:
            return []

        # 合并热工具和温工具
        hot_warm_tools = hot_tools + warm_tools

        # 仅在需要时重建索引（使用缓存检测）
        if searcher._should_rebuild_index(hot_warm_tools):
            searcher.index(hot_warm_tools)

        # 执行搜索
        results = searcher.search(query, hot_warm_tools, limit)

        return results

    # ============================================================
    # 使用频率跟踪 (TASK-304)
    # ============================================================

    def update_usage(self, tool_name: str) -> bool:
        """
        更新工具使用频率和最后使用时间 (TASK-304 + TASK-802)

        自动升级工具温度，并检查是否需要降级其他工具。

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
        old_temperature = tool.temperature

        # 更新使用统计
        tool.use_frequency += 1
        tool.last_used = datetime.now()

        # 重新分类工具温度 (TASK-802)
        with self._temp_lock:
            new_temperature = self._classify_tool_temperature(tool)
            if new_temperature != old_temperature:
                tool.temperature = new_temperature
                self._add_to_temperature_layer(tool, new_temperature)

        # 检查是否需要降级其他工具 (TASK-802)
        if ENABLE_DOWNGRADE and new_temperature.value in ("hot", "warm"):
            self._check_and_downgrade_other_tools()

        return True

    def _check_and_downgrade_other_tools(self) -> None:
        """
        检查并降级其他长时间未使用的工具 (TASK-802)

        这是一个后台维护操作，用于在工具升级时触发降级检查。
        """
        with self._temp_lock:
            # 检查热工具是否需要降级
            hot_tools_to_downgrade = [
                name for name, tool in self._hot_tools.items() if self._check_downgrade_tool(tool)
            ]
            for tool_name in hot_tools_to_downgrade:
                self._downgrade_tool(tool_name)

            # 检查温工具是否需要降级
            warm_tools_to_downgrade = [
                name for name, tool in self._warm_tools.items() if self._check_downgrade_tool(tool)
            ]
            for tool_name in warm_tools_to_downgrade:
                self._downgrade_tool(tool_name)

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
        # 清空温度层 (TASK-802)
        with self._temp_lock:
            self._hot_tools.clear()
            self._warm_tools.clear()
            self._cold_tools.clear()
        self._invalidate_search_indexes()
