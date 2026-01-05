"""
BM25 搜索算法

使用 BM25 算法进行关键词搜索，支持中文分词。

Copyright (c) 2026 Maric
License: MIT
"""

import jieba
from rank_bm25 import BM25Okapi

from registrytools.registry.models import SearchMethod, ToolMetadata, ToolSearchResult
from registrytools.search.base import SearchAlgorithm


class BM25Search(SearchAlgorithm):
    """
    BM25 搜索算法

    使用 BM25 算法进行关键词搜索，支持中英文分词。
    适用于自然语言查询场景。

    Attributes:
        method: 搜索方法类型 (BMEX)
        k1: BM25 k1 参数（控制词频饱和度）
        b: BM25 b 参数（控制文档长度归一化）
        epsilon: BM25 epsilon 参数（平滑 IDF 下界）
    """

    method = SearchMethod.BM25
    """搜索方法类型"""

    def __init__(self, k1: float = 1.5, b: float = 0.75, epsilon: float = 0.25) -> None:
        """
        初始化 BM25 搜索算法

        Args:
            k1: BM25 k1 参数，默认 1.5
            b: BM25 b 参数，默认 0.75
            epsilon: BM25 epsilon 参数，默认 0.25
        """
        super().__init__()
        self.k1 = k1
        self.b = b
        self.epsilon = epsilon
        self._bm25: BM25Okapi | None = None
        self._tokenized_docs: list[list[str]] = []

    def index(self, tools: list[ToolMetadata]) -> None:
        """
        建立 BM25 搜索索引

        对工具的名称、描述和标签进行分词并建立索引。

        Args:
            tools: 工具元数据列表
        """
        super().index(tools)

        # 处理空列表情况
        if not tools:
            self._tokenized_docs = []
            self._bm25 = None
            return

        # 构建文档集合（名称 + 描述 + 标签）
        self._tokenized_docs = []
        for tool in tools:
            # 合并所有可搜索文本
            text = f"{tool.name} {tool.description} {' '.join(tool.tags)}"
            # 使用 jieba 分词
            tokens = list(jieba.cut(text))
            self._tokenized_docs.append(tokens)

        # 创建 BM25 索引
        self._bm25 = BM25Okapi(self._tokenized_docs, k1=self.k1, b=self.b, epsilon=self.epsilon)

    def index_layered(
        self,
        hot_tools: list[ToolMetadata],
        warm_tools: list[ToolMetadata],
        cold_tools: list[ToolMetadata] | None = None,
    ) -> None:
        """
        建立分层 BM25 搜索索引 (TASK-802)

        优化的分层索引实现：热工具和温工具优先索引，冷工具可选。
        热工具会被放置在索引的前部，提高搜索性能。

        Args:
            hot_tools: 热工具列表（必须索引，放在索引前部）
            warm_tools: 温工具列表（必须索引）
            cold_tools: 冷工具列表（可选索引，默认不索引）

        Examples:
            >>> searcher = BM25Search()
            >>> hot = [tool1, tool2]  # 热工具
            >>> warm = [tool3, tool4]  # 温工具
            >>> # 只索引热+温工具，冷工具延迟加载
            >>> searcher.index_layered(hot, warm)
        """
        # 合并热工具和温工具（热工具在前）
        all_indexed = hot_tools + warm_tools

        # 如果提供冷工具，也包含在索引中
        if cold_tools:
            all_indexed += cold_tools

        # 调用基类方法记录哈希值和标记
        super().index(all_indexed)

        # 处理空列表情况
        if not all_indexed:
            self._tokenized_docs = []
            self._bm25 = None
            return

        # 构建分层的文档集合（热工具优先）
        self._tokenized_docs = []
        for tool in all_indexed:
            # 合并所有可搜索文本
            text = f"{tool.name} {tool.description} {' '.join(tool.tags)}"
            # 使用 jieba 分词
            tokens = list(jieba.cut(text))
            self._tokenized_docs.append(tokens)

        # 创建 BM25 索引（热工具在索引前部，搜索更快）
        self._bm25 = BM25Okapi(self._tokenized_docs, k1=self.k1, b=self.b, epsilon=self.epsilon)

    def search(self, query: str, tools: list[ToolMetadata], limit: int) -> list[ToolSearchResult]:
        """
        执行 BM25 搜索

        Args:
            query: 搜索查询字符串
            tools: 工具元数据列表
            limit: 返回结果数量限制

        Returns:
            搜索结果列表，按 BM25 分数降序排列
        """
        # 使用哈希值检测是否需要重建索引（缓存优化）
        if self._should_rebuild_index(tools):
            with self._lock:
                # 双重检查：可能另一个线程已经重建了索引
                if self._should_rebuild_index(tools):
                    self.index(tools)

        # 获取索引状态的快照
        with self._lock:
            if self._bm25 is None or not self._indexed:
                return []
            bm25 = self._bm25
            indexed_tools = self._tools

        # 对查询进行分词（不需要锁）
        query_tokens = list(jieba.cut(query))

        # 获取 BM25 分数（不需要锁，因为我们有索引的快照）
        scores = bm25.get_scores(query_tokens)

        # 构建结果（不过滤分数，由 _filter_by_score 进行归一化）
        results = []
        for i, score in enumerate(scores):
            if i < len(indexed_tools):
                results.append((indexed_tools[i], score))

        # 转换并过滤结果
        return self._filter_by_score(results, limit)

    def _get_match_reason(self) -> str:
        """
        获取匹配原因描述

        Returns:
            匹配原因字符串
        """
        return "bm25_keyword_similarity"

    def get_index_size(self) -> int:
        """
        获取索引大小

        Returns:
            索引中的文档数量
        """
        return len(self._tokenized_docs)
