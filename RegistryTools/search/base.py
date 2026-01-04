"""
搜索算法基类

定义所有搜索算法的抽象接口。

Copyright (c) 2026 Maric
License: MIT
"""

from abc import ABC, abstractmethod

from RegistryTools.registry.models import SearchMethod, ToolMetadata, ToolSearchResult


class SearchAlgorithm(ABC):
    """
    搜索算法抽象基类

    所有搜索算法必须继承此类并实现核心方法。

    Attributes:
        method: 搜索方法类型
        indexed: 是否已建立索引
    """

    method: SearchMethod
    """搜索方法类型"""

    def __init__(self) -> None:
        """初始化搜索算法"""
        self._indexed = False
        self._tools: list[ToolMetadata] = []

    @abstractmethod
    def index(self, tools: list[ToolMetadata]) -> None:
        """
        建立搜索索引

        Args:
            tools: 工具元数据列表
        """
        self._tools = tools
        self._indexed = True

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
