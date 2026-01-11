"""
Embedding 语义搜索单元测试

测试 EmbeddingSearch 语义搜索算法的功能。

Copyright (c) 2026 Maric
License: MIT
"""

import os
import threading

import pytest

from registrytools.registry.models import SearchMethod, ToolMetadata
from registrytools.search.embedding_search import (
    EmbeddingSearch,
    EmbeddingSearchLazyLoader,
    _is_gpu_available,
    _is_specific_gpu_available,
    _validate_and_get_device,
)


class TestEmbeddingSearch:
    """EmbeddingSearch 语义搜索算法测试"""

    @pytest.fixture
    def sample_tools(self):
        """创建示例工具列表"""
        return [
            ToolMetadata(
                name="github.create_pr",
                description="Create a pull request in GitHub repository",
                tags={"github", "git", "pr", "code"},
            ),
            ToolMetadata(
                name="slack.send_message",
                description="Send message to Slack channel",
                tags={"slack", "message", "chat"},
            ),
            ToolMetadata(
                name="gitlab.merge_request",
                description="Create merge request in GitLab",
                tags={"gitlab", "mr", "code"},
            ),
            ToolMetadata(
                name="aws.s3.upload",
                description="Upload file to AWS S3 bucket",
                tags={"aws", "s3", "storage", "cloud"},
            ),
            ToolMetadata(
                name="database.query",
                description="Execute SQL query on database",
                tags={"database", "sql", "query"},
            ),
        ]

    def test_initialization(self):
        """测试初始化"""
        searcher = EmbeddingSearch()
        assert searcher.method == SearchMethod.EMBEDDING
        assert searcher.model_name == EmbeddingSearch.DEFAULT_MODEL
        assert searcher._model is None  # 模型应该延迟加载

    def test_custom_model(self):
        """测试自定义模型"""
        custom_model = "all-MiniLM-L6-v2"
        searcher = EmbeddingSearch(model_name=custom_model)
        assert searcher.model_name == custom_model

    def test_index_building(self, sample_tools):
        """测试索引建立"""
        searcher = EmbeddingSearch()
        searcher.index(sample_tools)
        assert searcher.is_indexed()
        assert searcher.get_index_size() == len(sample_tools)

    def test_embedding_dimension(self, sample_tools):
        """测试嵌入向量维度"""
        searcher = EmbeddingSearch()
        searcher.index(sample_tools)

        dimension = searcher.get_embedding_dimension()
        assert dimension is not None
        assert dimension > 0  # 应该有正的维度

    def test_semantic_search_english(self, sample_tools):
        """测试英文语义搜索"""
        searcher = EmbeddingSearch()
        results = searcher.search("code repository", sample_tools, 5)

        # 应该找到与代码仓库相关的工具
        assert len(results) >= 1
        tool_names = [r.tool_name for r in results]
        # github 或 gitlab 相关工具应该排名较高
        assert any("github" in name or "gitlab" in name for name in tool_names)

    def test_semantic_search_synonyms(self, sample_tools):
        """测试同义词语义搜索"""
        searcher = EmbeddingSearch()

        # "发送消息" 和 "send message" 语义相似
        results = searcher.search("send notification", sample_tools, 5)
        assert len(results) >= 1

        # slack.send_message 应该匹配（语义相似）
        tool_names = [r.tool_name for r in results]
        assert "slack.send_message" in tool_names

    def test_semantic_search_chinese(self):
        """测试中文语义搜索"""
        tools = [
            ToolMetadata(
                name="weather.query",
                description="查询天气信息",
                tags={"天气", "查询"},
            ),
            ToolMetadata(
                name="stock.price",
                description="股票价格查询",
                tags={"股票", "价格"},
            ),
            ToolMetadata(
                name="news.read",
                description="新闻阅读",
                tags={"新闻", "阅读"},
            ),
            ToolMetadata(
                name="calendar.event",
                description="创建日程事件",
                tags={"日历", "事件"},
            ),
        ]

        searcher = EmbeddingSearch()
        results = searcher.search("天气预报", tools, 5)

        # 应该找到天气相关的工具
        assert len(results) >= 1
        tool_names = [r.tool_name for r in results]
        assert "weather.query" in tool_names

    def test_semantic_search_mixed_language(self):
        """测试混合语言语义搜索"""
        tools = [
            ToolMetadata(
                name="translate.text",
                description="翻译文本到多种语言",
                tags={"翻译", "translate", "language"},
            ),
            ToolMetadata(
                name="email.send",
                description="发送电子邮件",
                tags={"邮件", "email", "send"},
            ),
            ToolMetadata(
                name="file.upload",
                description="上传文件到云端",
                tags={"文件", "upload", "cloud"},
            ),
        ]

        searcher = EmbeddingSearch()

        # 用英文搜索应该找到中文描述的工具
        results = searcher.search("send email", tools, 5)
        assert len(results) >= 1
        tool_names = [r.tool_name for r in results]
        assert "email.send" in tool_names

    def test_limit_results(self, sample_tools):
        """测试结果数量限制"""
        searcher = EmbeddingSearch()
        results = searcher.search("create", sample_tools, 2)

        assert len(results) <= 2

    def test_score_normalization(self, sample_tools):
        """测试分数归一化"""
        searcher = EmbeddingSearch()
        results = searcher.search("code", sample_tools, 5)

        # 验证所有分数在 [0, 1] 范围内
        for result in results:
            assert 0.0 <= result.score <= 1.0

    def test_relevance_ordering(self, sample_tools):
        """测试相关性排序"""
        searcher = EmbeddingSearch()
        results = searcher.search("storage", sample_tools, 5)

        # 验证分数是降序排列的
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_reindex_on_tool_change(self, sample_tools):
        """测试工具变化时重新索引"""
        searcher = EmbeddingSearch()
        searcher.index(sample_tools)

        # 添加新工具
        new_tools = sample_tools + [
            ToolMetadata(
                name="jira.create_issue",
                description="Create issue in Jira",
                tags={"jira", "issue", "bug"},
            )
        ]

        results = searcher.search("bug tracking", new_tools, 5)
        assert len(results) >= 1
        tool_names = [r.tool_name for r in results]
        assert "jira.create_issue" in tool_names

    def test_empty_tools_list(self):
        """测试空工具列表"""
        searcher = EmbeddingSearch()
        searcher.index([])

        assert searcher.is_indexed()
        assert searcher.get_index_size() == 0
        assert searcher.get_embedding_dimension() is None

    def test_search_with_empty_index(self):
        """测试在空索引中搜索"""
        searcher = EmbeddingSearch()
        searcher.index([])

        results = searcher.search("test", [], 5)
        assert len(results) == 0

    def test_model_lazy_loading(self):
        """测试模型延迟加载"""
        searcher = EmbeddingSearch()

        # 在索引之前，模型不应该加载
        assert searcher._model is None

        # 索引后，模型应该加载
        tools = [
            ToolMetadata(
                name="test.tool",
                description="Test tool",
                tags={"test"},
            )
        ]
        searcher.index(tools)
        assert searcher._model is not None

    def test_layered_indexing(self, sample_tools):
        """测试分层索引"""
        searcher = EmbeddingSearch()

        # 分层工具（模拟冷热分离）
        hot = sample_tools[:2]
        warm = sample_tools[2:4]
        cold = sample_tools[4:]

        searcher.index_layered(hot, warm, cold)

        assert searcher.is_indexed()
        assert searcher.get_index_size() == len(sample_tools)

    def test_layered_indexing_without_cold(self, sample_tools):
        """测试不包含冷工具的分层索引"""
        searcher = EmbeddingSearch()

        hot = sample_tools[:2]
        warm = sample_tools[2:4]

        searcher.index_layered(hot, warm)

        assert searcher.is_indexed()
        assert searcher.get_index_size() == len(hot) + len(warm)

    def test_cache_mechanism(self, sample_tools):
        """测试缓存机制"""
        searcher = EmbeddingSearch()
        searcher.index(sample_tools)

        # 第一次搜索
        results1 = searcher.search("code", sample_tools, 5)
        assert len(results1) >= 1

        # 第二次搜索相同内容（应该使用缓存）
        results2 = searcher.search("code", sample_tools, 5)
        assert len(results2) == len(results1)

    def test_match_reason(self, sample_tools):
        """测试匹配原因"""
        searcher = EmbeddingSearch()
        results = searcher.search("code", sample_tools, 5)

        for result in results:
            assert result.match_reason == "semantic_similarity"

    def test_abstract_methods(self):
        """测试抽象方法实现"""
        from registrytools.search.base import SearchAlgorithm

        # EmbeddingSearch 应该是 SearchAlgorithm 的实例
        searcher = EmbeddingSearch()
        assert isinstance(searcher, SearchAlgorithm)

        # 应该实现所有抽象方法
        assert hasattr(searcher, "index")
        assert hasattr(searcher, "search")
        assert callable(searcher.index)
        assert callable(searcher.search)


# ============================================================
# GPU 验证函数测试
# ============================================================


class TestGPUValidation:
    """GPU 可用性验证函数测试"""

    def test_is_gpu_available(self):
        """测试 GPU 可用性检查"""
        result = _is_gpu_available()
        # 应该返回布尔值
        assert isinstance(result, bool)

    def test_is_specific_gpu_available(self):
        """测试指定 GPU 可用性检查"""
        # 测试 GPU 0
        result = _is_gpu_available()
        if result:
            # 如果有 GPU，检查 GPU 0 应该可用
            assert _is_specific_gpu_available(0) is True
        else:
            # 如果没有 GPU，检查应该返回 False
            assert _is_specific_gpu_available(0) is False

        # 测试不存在的 GPU
        assert _is_specific_gpu_available(999) is False

    def test_validate_cpu_device(self):
        """测试 CPU 设备验证"""
        device, fallback, log_msg = _validate_and_get_device("cpu")
        assert device == "cpu"
        assert fallback is False
        assert log_msg == ""

    def test_validate_empty_device(self):
        """测试空设备配置（默认为 CPU）"""
        device, fallback, log_msg = _validate_and_get_device("")
        assert device == "cpu"
        assert fallback is False
        assert log_msg == ""

    def test_validate_auto_mode_with_gpu(self, monkeypatch):
        """测试 auto 模式（有 GPU）"""
        # 模拟 GPU 可用
        if _is_gpu_available():
            device, fallback, log_msg = _validate_and_get_device("auto")
            assert device == "cuda:0"
            assert fallback is False
            assert log_msg == ""

    def test_validate_auto_mode_without_gpu(self):
        """测试 auto 模式（无 GPU）静默降级"""
        device, fallback, log_msg = _validate_and_get_device("auto")
        # 无论是否有 GPU，都应该返回有效设备
        assert device in ("cpu", "cuda:0")
        # 如果是 CPU，应该是降级结果
        if device == "cpu":
            assert fallback is True
            assert log_msg == ""  # auto 模式静默降级

    def test_validate_specific_gpu_unavailable(self):
        """测试具体 GPU 不可用时警告并降级"""
        device, fallback, log_msg = _validate_and_get_device("gpu:999")
        assert device == "cpu"
        assert fallback is True
        assert "不可用" in log_msg

    def test_validate_gpu_format_conversion(self):
        """测试 GPU 格式转换"""
        if _is_gpu_available() and _is_specific_gpu_available(0):
            device, fallback, log_msg = _validate_and_get_device("gpu:0")
            assert device == "cuda:0"
            assert fallback is False
            assert log_msg == ""

            device, fallback, log_msg = _validate_and_get_device("cuda:0")
            assert device == "cuda:0"
            assert fallback is False
            assert log_msg == ""

    def test_validate_invalid_gpu_config(self):
        """测试无效 GPU 配置"""
        device, fallback, log_msg = _validate_and_get_device("gpu:invalid")
        assert device == "cpu"
        assert fallback is True
        assert "无效" in log_msg

    def test_validate_unknown_device_config(self):
        """测试未知设备配置"""
        device, fallback, log_msg = _validate_and_get_device("unknown_device")
        assert device == "cpu"
        assert fallback is True
        assert "未知" in log_msg


# ============================================================
# 延迟加载器测试
# ============================================================


class TestEmbeddingSearchLazyLoader:
    """EmbeddingSearchLazyLoader 延迟加载器测试"""

    @pytest.fixture
    def sample_tools(self):
        """创建示例工具列表"""
        return [
            ToolMetadata(
                name="test.tool1",
                description="Test tool 1",
                tags={"test", "tool1"},
            ),
            ToolMetadata(
                name="test.tool2",
                description="Test tool 2",
                tags={"test", "tool2"},
            ),
        ]

    def test_lazy_loader_initialization(self):
        """测试延迟加载器初始化"""
        loader = EmbeddingSearchLazyLoader()
        assert loader.method == SearchMethod.EMBEDDING
        assert loader._real_searcher is None

    def test_first_search_triggers_loading(self, sample_tools):
        """测试首次搜索触发模型加载"""
        loader = EmbeddingSearchLazyLoader()
        assert loader._real_searcher is None

        results = loader.search("test", sample_tools, 5)

        assert loader._real_searcher is not None
        assert len(results) >= 0

    def test_first_index_triggers_loading(self, sample_tools):
        """测试首次索引触发模型加载"""
        loader = EmbeddingSearchLazyLoader()
        assert loader._real_searcher is None

        loader.index(sample_tools)

        assert loader._real_searcher is not None
        assert loader.is_indexed()

    def test_lazy_loader_delegation(self, sample_tools):
        """测试延迟加载器委托行为"""
        loader = EmbeddingSearchLazyLoader()

        # 测试 search 方法
        results = loader.search("test", sample_tools, 5)
        assert loader._real_searcher is not None

        # 测试 index 方法
        loader.index(sample_tools)
        assert loader._real_searcher.is_indexed()

        # 测试 index_layered 方法
        hot = sample_tools[:1]
        warm = sample_tools[1:]
        loader.index_layered(hot, warm)
        assert loader._real_searcher.is_indexed()

    def test_unload_model_delegation(self, sample_tools):
        """测试 unload_model 委托"""
        loader = EmbeddingSearchLazyLoader()

        # 触发加载
        loader.index(sample_tools)
        assert loader._real_searcher is not None

        # 卸载模型
        loader.unload_model()

    def test_thread_safe_loading(self, sample_tools):
        """测试线程安全的加载"""
        loader = EmbeddingSearchLazyLoader()

        results_list = []
        exceptions = []

        def search_in_thread():
            try:
                results = loader.search("test", sample_tools, 5)
                results_list.append(results)
            except Exception as e:
                exceptions.append(e)

        # 创建多个线程同时搜索
        threads = [threading.Thread(target=search_in_thread) for _ in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 应该没有异常
        assert len(exceptions) == 0
        # 应该创建了搜索器实例
        assert loader._real_searcher is not None
        # 应该有结果
        assert len(results_list) == 10

    def test_gpu_validation_in_lazy_loader(self, sample_tools, monkeypatch):
        """测试延迟加载器中的 GPU 验证"""
        # 测试 auto 模式
        monkeypatch.setenv("REGISTRYTOOLS_DEVICE", "auto")
        loader = EmbeddingSearchLazyLoader()
        loader.index(sample_tools)

        # 验证搜索器已创建
        assert loader._real_searcher is not None

    def test_validated_device_parameter(self):
        """测试 EmbeddingSearch 的 _validated_device 参数"""
        # 直接创建 EmbeddingSearch 并传入已验证的设备
        searcher = EmbeddingSearch(_validated_device="cpu")
        assert searcher._device == "cpu"

        # 不传参数时，应该从环境变量读取
        searcher2 = EmbeddingSearch()
        assert searcher2._device in ("cpu", "cuda:0", "cuda:1")
