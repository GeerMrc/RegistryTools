"""
Embedding 语义搜索算法

使用 sentence-transformers 进行向量嵌入，实现语义搜索。

Copyright (c) 2026 Maric
License: MIT
"""

import threading
from typing import TYPE_CHECKING

import numpy as np

from registrytools.registry.models import SearchMethod, ToolMetadata, ToolSearchResult
from registrytools.search.base import SearchAlgorithm

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer


class EmbeddingSearch(SearchAlgorithm):
    """
    Embedding 语义搜索算法

    使用 sentence-transformers 进行向量嵌入，实现真正的语义搜索。
    支持中英文语义查询，理解查询意图而非仅仅匹配关键词。

    Attributes:
        method: 搜索方法类型 (EMBEDDING)
        model_name: 使用的嵌入模型名称
        _model: sentence-transformers 模型实例（延迟加载）
        _embeddings: 工具向量嵌入矩阵
        _model_lock: 模型加载锁
    """

    method = SearchMethod.EMBEDDING
    """搜索方法类型"""

    # 默认使用支持中文的轻量级多语言模型
    DEFAULT_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

    def __init__(self, model_name: str | None = None) -> None:
        """
        初始化 Embedding 搜索算法

        Args:
            model_name: sentence-transformers 模型名称，默认使用多语言模型
        """
        super().__init__()
        self.model_name = model_name or self.DEFAULT_MODEL
        self._model: "SentenceTransformer | None" = None
        self._embeddings: np.ndarray | None = None
        self._model_lock = threading.Lock()

    def _load_model(self) -> "SentenceTransformer":
        """
        延迟加载 sentence-transformers 模型

        Returns:
            SentenceTransformer 模型实例
        """
        if self._model is None:
            with self._model_lock:
                # 双重检查锁定
                if self._model is None:
                    from sentence_transformers import SentenceTransformer

                    self._model = SentenceTransformer(self.model_name)
        return self._model

    def index(self, tools: list[ToolMetadata]) -> None:
        """
        建立 Embedding 搜索索引

        对工具的名称、描述和标签进行向量嵌入并建立索引。

        Args:
            tools: 工具元数据列表
        """
        super().index(tools)

        # 处理空列表情况
        if not tools:
            self._embeddings = None
            return

        # 加载模型
        model = self._load_model()

        # 构建文档集合（名称 + 描述 + 标签）
        texts = []
        for tool in tools:
            # 合并所有可搜索文本
            text = f"{tool.name} {tool.description} {' '.join(tool.tags)}"
            texts.append(text)

        # 生成向量嵌入
        self._embeddings = model.encode(texts, convert_to_numpy=True)

    def index_layered(
        self,
        hot_tools: list[ToolMetadata],
        warm_tools: list[ToolMetadata],
        cold_tools: list[ToolMetadata] | None = None,
    ) -> None:
        """
        建立分层 Embedding 搜索索引

        优化的分层索引实现：热工具和温工具优先索引，冷工具可选。

        Args:
            hot_tools: 热工具列表（必须索引，放在索引前部）
            warm_tools: 温工具列表（必须索引）
            cold_tools: 冷工具列表（可选索引，默认不索引）
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
            self._embeddings = None
            return

        # 加载模型
        model = self._load_model()

        # 构建分层的文档集合（热工具优先）
        texts = []
        for tool in all_indexed:
            text = f"{tool.name} {tool.description} {' '.join(tool.tags)}"
            texts.append(text)

        # 生成向量嵌入（热工具在索引前部）
        self._embeddings = model.encode(texts, convert_to_numpy=True)

    def search(self, query: str, tools: list[ToolMetadata], limit: int) -> list[ToolSearchResult]:
        """
        执行 Embedding 语义搜索

        使用余弦相似度计算查询与工具的语义相似度。

        Args:
            query: 搜索查询字符串
            tools: 工具元数据列表
            limit: 返回结果数量限制

        Returns:
            搜索结果列表，按语义相似度降序排列
        """
        # 使用哈希值检测是否需要重建索引（缓存优化）
        if self._should_rebuild_index(tools):
            with self._lock:
                # 双重检查：可能另一个线程已经重建了索引
                if self._should_rebuild_index(tools):
                    self.index(tools)

        # 获取索引状态的快照
        with self._lock:
            if self._embeddings is None or not self._indexed:
                return []
            embeddings = self._embeddings
            indexed_tools = self._tools

        # 加载模型（不需要锁，因为模型已加载或正在加载）
        model = self._load_model()

        # 生成查询向量嵌入
        query_embedding = model.encode([query], convert_to_numpy=True)

        # 计算余弦相似度
        # 相似度 = (A · B) / (||A|| * ||B||)
        # 对于归一化的向量，相似度 = A · B
        similarities = np.dot(embeddings, query_embedding.T).flatten()

        # 构建结果
        results = []
        for i, score in enumerate(similarities):
            if i < len(indexed_tools):
                results.append((indexed_tools[i], float(score)))

        # 转换并过滤结果
        return self._filter_by_score(results, limit)

    def _get_match_reason(self) -> str:
        """
        获取匹配原因描述

        Returns:
            匹配原因字符串
        """
        return "semantic_similarity"

    def get_index_size(self) -> int:
        """
        获取索引大小

        Returns:
            索引中的嵌入向量数量
        """
        if self._embeddings is None:
            return 0
        return len(self._embeddings)

    def get_embedding_dimension(self) -> int | None:
        """
        获取嵌入向量维度

        Returns:
            嵌入向量维度，如果未建立索引则返回 None
        """
        if self._embeddings is None:
            return None
        return self._embeddings.shape[1]
