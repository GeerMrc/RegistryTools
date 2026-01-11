"""
Embedding 语义搜索算法

使用 sentence-transformers 进行向量嵌入，实现语义搜索。

Copyright (c) 2026 Maric
License: MIT
"""

import logging
import os
import threading
from typing import TYPE_CHECKING

import numpy as np

from registrytools.registry.models import SearchMethod, ToolMetadata, ToolSearchResult
from registrytools.search.base import SearchAlgorithm

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer


# ============================================================
# GPU 验证函数
# ============================================================


def _is_gpu_available() -> bool:
    """
    检查是否有可用的 GPU

    Returns:
        True 如果至少有一个 GPU 可用，否则 False
    """
    try:
        import torch

        return torch.cuda.is_available()
    except ImportError:
        return False


def _is_specific_gpu_available(device_id: int) -> bool:
    """
    检查指定的 GPU 是否可用

    Args:
        device_id: GPU 设备 ID (0, 1, 2, ...)

    Returns:
        True 如果指定的 GPU 可用，否则 False
    """
    try:
        import torch

        if not torch.cuda.is_available():
            return False
        # 检查设备 ID 是否在有效范围内
        return device_id < torch.cuda.device_count()
    except ImportError:
        return False


def _validate_and_get_device(device_config: str) -> tuple[str, bool, str]:
    """
    验证设备配置并返回实际可用设备

    区分 auto 和具体 GPU 配置的日志行为：
    - auto 模式：GPU 不可用时静默降级到 CPU
    - 具体 GPU 模式：GPU 不可用时记录警告并降级到 CPU

    Args:
        device_config: 设备配置字符串

    Returns:
        (actual_device, was_fallback, log_message)
        - actual_device: 实际使用的设备 (cpu/cuda:0/cuda:1)
        - was_fallback: 是否发生了降级 (True/False)
        - log_message: 日志消息 (仅在需要记录时非空)
    """
    device_config = device_config.strip().lower()

    # 默认 CPU
    if not device_config or device_config == "cpu":
        return "cpu", False, ""

    # auto 模式：自动检测
    if device_config == "auto":
        if _is_gpu_available():
            return "cuda:0", False, ""
        else:
            # 静默降级到 CPU，不记录日志
            return "cpu", True, ""

    # GPU 配置 (支持 gpu:0, gpu:1, cuda:0, cuda:1)
    if device_config.startswith(("gpu:", "cuda:")):
        parts = device_config.split(":")
        if len(parts) == 2:
            try:
                device_id = int(parts[1])
                # 验证指定 GPU 是否可用
                if _is_specific_gpu_available(device_id):
                    # 转换为 PyTorch 标准格式
                    return f"cuda:{device_id}", False, ""
                else:
                    # GPU 不可用，降级到 CPU 并记录警告
                    log_msg = f"配置的 GPU {device_config} 不可用，已降级到 CPU"
                    return "cpu", True, log_msg
            except ValueError:
                # 无效的 GPU ID，回退到 CPU
                log_msg = f"无效的 GPU 配置 '{device_config}'，已降级到 CPU"
                return "cpu", True, log_msg

    # 未知配置，回退到 CPU
    logger.warning(f"未知的设备配置 '{device_config}'，回退到 CPU 模式")
    return "cpu", True, f"未知的设备配置 '{device_config}'，已降级到 CPU"


# ============================================================
# 延迟加载器类
# ============================================================


class EmbeddingSearchLazyLoader(SearchAlgorithm):
    """
    EmbeddingSearch 延迟加载器

    实现延迟注册机制，只在首次使用时才初始化真实的 EmbeddingSearch 实例。

    优点：
    - 不使用 embedding 时不加载模型，节省内存和启动时间
    - GPU 验证延迟到实际使用时，避免启动时失败
    - 支持运行时降级策略

    Attributes:
        method: 搜索方法类型 (EMBEDDING)
        _real_searcher: 真实的 EmbeddingSearch 实例（延迟加载）
        _loader_lock: 加载锁（线程安全）
    """

    method = SearchMethod.EMBEDDING

    def __init__(self) -> None:
        """初始化延迟加载器"""
        super().__init__()
        # 注解延迟求值，无需字符串引号（Python 3.10+）
        self._real_searcher: EmbeddingSearch | None = None
        self._loader_lock = threading.Lock()

    def _load_real_searcher(self) -> "EmbeddingSearch":
        """
        延迟加载真实的 EmbeddingSearch 实例

        验证 GPU 可用性，处理降级逻辑，首次调用时执行。

        Returns:
            真实的 EmbeddingSearch 实例
        """
        if self._real_searcher is None:
            with self._loader_lock:
                # 双重检查锁定
                if self._real_searcher is None:
                    # 获取设备配置
                    device_config = os.getenv("REGISTRYTOOLS_DEVICE", "cpu")

                    # 验证设备并获取实际可用设备
                    actual_device, was_fallback, log_msg = _validate_and_get_device(device_config)

                    # 记录日志（根据配置类型）
                    if device_config == "auto":
                        if actual_device == "cuda:0":
                            logger.info(f"Embedding 搜索：自动检测到 GPU，使用 {actual_device}")
                        # 降级到 CPU 时不记录日志（静默）
                    elif was_fallback:
                        # 具体 GPU 配置降级，记录警告
                        logger.warning(f"Embedding 搜索：{log_msg}")
                    else:
                        logger.info(f"Embedding 搜索：使用设备 {actual_device}")

                    # 创建真实的 EmbeddingSearch 实例
                    # 传入验证后的实际设备
                    self._real_searcher = EmbeddingSearch(_validated_device=actual_device)

        return self._real_searcher

    def index(self, tools: list[ToolMetadata]) -> None:
        """建立搜索索引（委托给真实实例）"""
        searcher = self._load_real_searcher()
        searcher.index(tools)

    def search(self, query: str, tools: list[ToolMetadata], limit: int) -> list[ToolSearchResult]:
        """执行搜索（委托给真实实例）"""
        searcher = self._load_real_searcher()
        return searcher.search(query, tools, limit)

    def index_layered(
        self,
        hot_tools: list[ToolMetadata],
        warm_tools: list[ToolMetadata],
        cold_tools: list[ToolMetadata] | None = None,
    ) -> None:
        """建立分层搜索索引（委托给真实实例）"""
        searcher = self._load_real_searcher()
        searcher.index_layered(hot_tools, warm_tools, cold_tools)

    def unload_model(self) -> None:
        """卸载模型（委托给真实实例）"""
        if self._real_searcher is not None:
            self._real_searcher.unload_model()

    def is_indexed(self) -> bool:
        """检查是否已建立索引（委托给真实实例）"""
        if self._real_searcher is None:
            return False
        return self._real_searcher.is_indexed()


# ============================================================
# Embedding 搜索类
# ============================================================


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

    def __init__(self, model_name: str | None = None, _validated_device: str | None = None) -> None:
        """
        初始化 Embedding 搜索算法

        Args:
            model_name: sentence-transformers 模型名称，默认使用多语言模型
            _validated_device: 内部使用，已验证的设备标识（避免重复验证）

        Note:
            设备配置通过环境变量 REGISTRYTOOLS_DEVICE 控制：
            - 未设置或 "cpu": 使用 CPU（默认）
            - "gpu:N" 或 "cuda:N": 使用指定 GPU
            - "auto": 自动选择（有 GPU 时使用第一个）

            当通过 EmbeddingSearchLazyLoader 创建时，_validated_device 参数
            用于传递已验证的设备标识，避免重复验证。
        """
        super().__init__()
        self.model_name = model_name or self.DEFAULT_MODEL

        # 如果提供了已验证的设备，直接使用；否则解析环境变量
        if _validated_device is not None:
            self._device = _validated_device
        else:
            # 直接解析设备（不进行可用性验证，保持向后兼容）
            self._device = self._parse_device(os.getenv("REGISTRYTOOLS_DEVICE", "cpu"))

        self._model: "SentenceTransformer | None" = None  # noqa: UP037
        self._embeddings: np.ndarray | None = None
        self._model_lock = threading.Lock()

    def _parse_device(self, device_str: str) -> str:
        """
        解析设备配置字符串

        Args:
            device_str: 设备字符串（cpu/gpu:0/gpu:1/cuda:0/auto）

        Returns:
            标准化的设备标识（cpu/cuda:0/cuda:1）
        """
        device_str = device_str.strip().lower()

        # 默认 CPU
        if not device_str or device_str == "cpu":
            return "cpu"

        # 自动检测
        if device_str == "auto":
            try:
                import torch

                return "cuda:0" if torch.cuda.is_available() else "cpu"
            except ImportError:
                return "cpu"

        # GPU 配置（支持 gpu:0, gpu:1, cuda:0, cuda:1 格式）
        if device_str.startswith(("gpu:", "cuda:")):
            # 转换为 PyTorch 标准格式
            return device_str.replace("gpu:", "cuda:")

        # 未知配置，回退到 CPU
        logger.warning(f"未知的设备配置 '{device_str}'，回退到 CPU 模式")
        return "cpu"

    def _load_model(self) -> "SentenceTransformer":  # noqa: UP037
        """
        延迟加载 sentence-transformers 模型

        根据环境变量 REGISTRYTOOLS_DEVICE 选择设备：
        - 未设置或 "cpu": 使用 CPU
        - "gpu:N" 或 "cuda:N": 使用指定 GPU
        - "auto": 自动选择（有 GPU 时使用 cuda:0）

        Returns:
            SentenceTransformer 模型实例
        """
        if self._model is None:
            with self._model_lock:
                # 双重检查锁定
                if self._model is None:
                    from sentence_transformers import SentenceTransformer

                    logger.info(f"正在加载 Embedding 模型到设备: {self._device}")
                    self._model = SentenceTransformer(self.model_name, device=self._device)
                    logger.info(f"Embedding 模型已加载到: {self._model.device}")
        return self._model

    def unload_model(self) -> None:
        """
        卸载模型释放 GPU/CPU 内存

        卸载后，下次搜索时会重新加载模型。
        """
        with self._model_lock:
            if self._model is not None:
                logger.info(f"正在卸载 Embedding 模型（设备: {self._device}）")
                del self._model
                self._model = None
                self._embeddings = None
                logger.info("Embedding 模型已卸载")

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
