"""
正则表达式搜索算法

使用正则表达式进行精确匹配搜索。

Copyright (c) 2026 Maric
License: MIT
"""

import re

from RegistryTools.registry.models import SearchMethod, ToolMetadata, ToolSearchResult
from RegistryTools.search.base import SearchAlgorithm


class RegexSearch(SearchAlgorithm):
    """
    正则表达式搜索算法

    使用正则表达式在工具名称和描述中进行匹配搜索。
    适用于精确名称匹配场景。

    Attributes:
        method: 搜索方法类型 (REGEX)
        case_sensitive: 是否区分大小写
    """

    method = SearchMethod.REGEX
    """搜索方法类型"""

    def __init__(self, case_sensitive: bool = False) -> None:
        """
        初始化正则搜索算法

        Args:
            case_sensitive: 是否区分大小写，默认 False
        """
        super().__init__()
        self.case_sensitive = case_sensitive

    def index(self, tools: list[ToolMetadata]) -> None:
        """
        建立搜索索引

        对于正则搜索，只需存储工具列表，无需额外预处理。

        Args:
            tools: 工具元数据列表
        """
        super().index(tools)

    def search(self, query: str, tools: list[ToolMetadata], limit: int) -> list[ToolSearchResult]:
        """
        执行正则表达式搜索

        在工具名称和描述中匹配正则表达式查询。

        Args:
            query: 搜索查询字符串（正则表达式）
            tools: 工具元数据列表
            limit: 返回结果数量限制

        Returns:
            搜索结果列表，按匹配精度降序排列
        """
        # 重建索引（如果需要）- 使用基类的哈希值检测
        if self._should_rebuild_index(tools):
            self.index(tools)

        # 编译正则表达式
        flags = 0 if self.case_sensitive else re.IGNORECASE
        try:
            pattern = re.compile(query, flags)
        except re.error:
            # 如果正则表达式无效，返回空结果
            return []

        # 计算每个工具的匹配分数
        results = []
        for tool in self._tools:
            score = self._calculate_score(tool, pattern)
            if score > 0:
                results.append((tool, score))

        # 转换并过滤结果
        return self._filter_by_score(results, limit)

    def _calculate_score(self, tool: ToolMetadata, pattern: re.Pattern) -> float:
        """
        计算工具的匹配分数

        匹配规则：
        - 完全匹配工具名称: 1.0
        - 工具名称包含查询: 0.8
        - 描述完全匹配: 0.6
        - 描述包含查询: 0.4

        Args:
            tool: 工具元数据
            pattern: 编译后的正则表达式

        Returns:
            匹配分数 (0-1)
        """
        score = 0.0

        # 检查工具名称匹配
        name_match = pattern.fullmatch(tool.name)
        if name_match:
            score = 1.0
        elif pattern.search(tool.name):
            score = max(score, 0.8)

        # 检查描述匹配
        desc_match = pattern.fullmatch(tool.description)
        if desc_match:
            score = max(score, 0.6)
        elif pattern.search(tool.description):
            score = max(score, 0.4)

        # 检查标签匹配
        for tag in tool.tags:
            if pattern.fullmatch(tag):
                score = max(score, 0.5)
            elif pattern.search(tag):
                score = max(score, 0.3)

        return score

    def _get_match_reason(self) -> str:
        """
        获取匹配原因描述

        Returns:
            匹配原因字符串
        """
        return "regex_pattern_match"
