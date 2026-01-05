"""
搜索算法基类

定义所有搜索算法的抽象接口。

Copyright (c) 2026 Maric
License: MIT
"""

import hashlib
import json
import threading
from abc import ABC, abstractmethod

from registrytools.registry.models import SearchMethod, ToolMetadata, ToolSearchResult


class SearchAlgorithm(ABC):
    """
    搜索算法抽象基类

    所有搜索算法必须继承此类并实现核心方法。

    Attributes:
        method: 搜索方法类型
        indexed: 是否已建立索引
        _tools_hash: 工具列表哈希值，用于缓存检测
        _lock: 线程锁，保护索引操作
    """

    method: SearchMethod
    """搜索方法类型"""

    def __init__(self) -> None:
        """初始化搜索算法"""
        self._indexed = False
        self._tools: list[ToolMetadata] = []
        self._tools_hash: str | None = None
        self._lock = threading.RLock()

    @abstractmethod
    def index(self, tools: list[ToolMetadata]) -> None:
        """
        建立搜索索引

        Args:
            tools: 工具元数据列表
        """
        self._tools = tools
        self._tools_hash = self._compute_tools_hash(tools)
        self._indexed = True

    def index_layered(
        self,
        hot_tools: list[ToolMetadata],
        warm_tools: list[ToolMetadata],
        cold_tools: list[ToolMetadata] | None = None,
    ) -> None:
        """
        建立分层搜索索引 (TASK-802)

        优先索引热工具和温工具，冷工具可选索引。
        默认实现合并所有工具并建立索引，子类可覆盖实现更优化的分层索引。

        Args:
            hot_tools: 热工具列表（必须索引）
            warm_tools: 温工具列表（必须索引）
            cold_tools: 冷工具列表（可选索引，默认不索引）

        Examples:
            >>> searcher = BM25Search()
            >>> hot = [tool1, tool2]  # 热工具
            >>> warm = [tool3, tool4]  # 温工具
            >>> cold = [tool5, tool6]  # 冷工具
            >>> # 只索引热+温工具，冷工具延迟加载
            >>> searcher.index_layered(hot, warm)
        """
        # 合并热工具和温工具
        all_indexed = hot_tools + warm_tools

        # 如果提供冷工具，也包含在索引中
        if cold_tools:
            all_indexed += cold_tools

        # 建立索引
        self.index(all_indexed)

    @abstractmethod
    def search(self, query: str, tools: list[ToolMetadata], limit: int) -> list[ToolSearchResult]:
        """
        执行搜索

        Args:
            query: 搜索查询字符串
            tools: 工具元数据列表
            limit: 返回结果数量限制

        Returns:
            搜索结果列表，按相关度降序排列
        """
        pass

    def is_indexed(self) -> bool:
        """
        检查是否已建立索引

        Returns:
            True 如果已建立索引，否则 False
        """
        return self._indexed

    def _compute_tools_hash(self, tools: list[ToolMetadata]) -> str:
        """
        计算工具列表的哈希值

        用于检测工具列表是否发生变化，避免不必要的索引重建。

        Args:
            tools: 工具元数据列表

        Returns:
            SHA256 哈希值（十六进制字符串）
        """
        # 序列化工具列表为稳定格式
        tools_data = sorted(
            [
                {
                    "name": t.name,
                    "description": t.description,
                    "tags": sorted(t.tags),
                    "category": t.category or "",
                }
                for t in tools
            ],
            key=lambda x: x["name"],
        )

        # 计算哈希值
        data_str = json.dumps(tools_data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def _should_rebuild_index(self, tools: list[ToolMetadata]) -> bool:
        """
        检查是否需要重建索引

        Args:
            tools: 工具元数据列表

        Returns:
            True 如果需要重建索引，否则 False
        """
        current_hash = self._compute_tools_hash(tools)
        return current_hash != self._tools_hash

    def _filter_by_score(
        self, results: list[tuple[ToolMetadata, float]], limit: int
    ) -> list[ToolSearchResult]:
        """
        过滤并转换搜索结果

        Args:
            results: (工具, 分数) 元组列表
            limit: 返回结果数量限制

        Returns:
            搜索结果列表
        """
        if not results:
            return []

        # 按分数降序排序
        sorted_results = sorted(results, key=lambda x: -x[1])

        # 归一化分数到 [0, 1] 范围
        max_score = max(score for _, score in sorted_results)
        min_score = min(score for _, score in sorted_results)
        score_range = max_score - min_score

        # 转换为 ToolSearchResult 并限制数量
        output = []
        for tool, score in sorted_results[:limit]:
            # 归一化分数到 [0, 1]
            if score_range > 0:
                normalized_score = (score - min_score) / score_range
            else:
                # 只有一个结果或所有分数相同，直接设为 1.0
                normalized_score = 1.0

            # 添加结果（即使原始分数为负数或0，只要归一化后有意义）
            output.append(
                ToolSearchResult(
                    tool_name=tool.name,
                    description=tool.description,
                    score=normalized_score,
                    match_reason=self._get_match_reason(),
                )
            )

        return output

    def _get_match_reason(self) -> str:
        """
        获取匹配原因描述

        Returns:
            匹配原因字符串
        """
        return f"{self.method.value}_match"
