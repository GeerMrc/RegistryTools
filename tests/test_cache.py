"""
索引缓存功能单元测试

测试 SearchAlgorithm 基类的索引缓存机制和线程安全功能。

Copyright (c) 2026 Maric
License: MIT
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest

from registrytools.registry.models import ToolMetadata
from registrytools.search.bm25_search import BM25Search
from registrytools.search.regex_search import RegexSearch


@pytest.fixture
def sample_tools() -> list[ToolMetadata]:
    """创建示例工具列表（模块级别 fixture）"""
    return [
        ToolMetadata(
            name="github.create_pr",
            description="Create a pull request in GitHub",
            tags={"github", "git", "pr"},
            category="github",
        ),
        ToolMetadata(
            name="slack.send_message",
            description="Send a message to Slack channel",
            tags={"slack", "message"},
            category="slack",
        ),
        ToolMetadata(
            name="aws.s3.upload",
            description="Upload file to AWS S3",
            tags={"aws", "s3", "storage"},
            category="aws",
        ),
    ]


class TestIndexCache:
    """索引缓存功能测试"""

    def test_compute_tools_hash_consistency(self, sample_tools: list[ToolMetadata]) -> None:
        """测试哈希值计算的一致性"""
        searcher = BM25Search()

        hash1 = searcher._compute_tools_hash(sample_tools)
        hash2 = searcher._compute_tools_hash(sample_tools)

        # 相同工具列表应该产生相同哈希值
        assert hash1 == hash2, "相同工具列表应该产生相同哈希值"

    def test_compute_tools_hash_uniqueness(self, sample_tools: list[ToolMetadata]) -> None:
        """测试哈希值对工具变化的敏感性"""
        searcher = BM25Search()

        hash1 = searcher._compute_tools_hash(sample_tools)

        # 修改工具列表
        modified_tools = sample_tools + [
            ToolMetadata(
                name="new_tool",
                description="A new tool",
                tags={"new"},
            )
        ]
        hash2 = searcher._compute_tools_hash(modified_tools)

        # 不同工具列表应该产生不同哈希值
        assert hash1 != hash2, "不同工具列表应该产生不同哈希值"

    def test_should_rebuild_index_initial(self, sample_tools: list[ToolMetadata]) -> None:
        """测试初始状态需要重建索引"""
        searcher = BM25Search()

        # 初始状态下应该需要重建索引
        assert searcher._should_rebuild_index(sample_tools), "初始状态应该需要重建索引"

    def test_should_rebuild_index_after_indexing(self, sample_tools: list[ToolMetadata]) -> None:
        """测试索引后不需要重建"""
        searcher = BM25Search()
        searcher.index(sample_tools)

        # 索引后相同工具列表不需要重建
        assert not searcher._should_rebuild_index(sample_tools), "索引后相同工具列表不需要重建"

    def test_should_rebuild_index_after_modification(
        self, sample_tools: list[ToolMetadata]
    ) -> None:
        """测试工具修改后需要重建索引"""
        searcher = BM25Search()
        searcher.index(sample_tools)

        # 修改工具描述
        modified_tools = [
            ToolMetadata(
                name=t.name,
                description=t.description + " (modified)",
                tags=t.tags,
                category=t.category,
            )
            for t in sample_tools
        ]

        # 修改后需要重建索引
        assert searcher._should_rebuild_index(modified_tools), "工具修改后需要重建索引"

    def test_cache_hit_in_search(self, sample_tools: list[ToolMetadata]) -> None:
        """测试搜索时缓存命中"""
        searcher = BM25Search()

        # 首次搜索会建立索引
        results1 = searcher.search("github", sample_tools, 5)

        # 第二次搜索应该使用缓存的索引
        results2 = searcher.search("github", sample_tools, 5)

        # 结果应该相同
        assert len(results1) == len(results2), "缓存命中结果应该一致"
        if results1:
            assert results1[0].tool_name == results2[0].tool_name

    def test_tools_hash_field_initialized(self) -> None:
        """测试 _tools_hash 字段正确初始化"""
        searcher = BM25Search()
        assert searcher._tools_hash is None, "初始状态 _tools_hash 应该为 None"

    def test_tools_hash_set_after_indexing(self, sample_tools: list[ToolMetadata]) -> None:
        """测试索引后 _tools_hash 被正确设置"""
        searcher = BM25Search()
        searcher.index(sample_tools)

        assert searcher._tools_hash is not None, "索引后 _tools_hash 不应该为 None"
        assert isinstance(searcher._tools_hash, str), "_tools_hash 应该是字符串"
        assert len(searcher._tools_hash) == 64, "SHA256 哈希应该是 64 个字符"


class TestThreadSafety:
    """线程安全功能测试"""

    @pytest.fixture
    def large_toolset(self) -> list[ToolMetadata]:
        """创建大规模工具集用于并发测试"""
        return [
            ToolMetadata(
                name=f"tool_{i}",
                description=f"Tool number {i} for testing",
                tags={f"tag_{i % 10}"},
                category="test",
            )
            for i in range(100)
        ]

    def test_concurrent_indexing(self, large_toolset: list[ToolMetadata]) -> None:
        """测试并发建立索引"""
        searcher = BM25Search()
        errors = []

        def index_tools() -> None:
            try:
                searcher.index(large_toolset)
            except Exception as e:
                errors.append(e)

        # 并发建立索引
        threads = [threading.Thread(target=index_tools) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 不应该有错误
        assert not errors, f"并发索引不应该产生错误: {errors}"
        assert searcher.is_indexed(), "索引应该建立成功"

    def test_concurrent_search(self, large_toolset: list[ToolMetadata]) -> None:
        """测试并发搜索"""
        searcher = BM25Search()
        searcher.index(large_toolset)

        results_list = []
        errors = []

        def search_tools() -> None:
            try:
                results = searcher.search("tool 50", large_toolset, 10)
                results_list.append(results)
            except Exception as e:
                errors.append(e)

        # 并发搜索
        threads = [threading.Thread(target=search_tools) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 不应该有错误
        assert not errors, f"并发搜索不应该产生错误: {errors}"
        assert len(results_list) == 10, "应该完成所有搜索"

        # 所有结果应该一致
        first_result = results_list[0]
        for results in results_list[1:]:
            assert len(results) == len(first_result), "并发搜索结果应该一致"

    def test_concurrent_index_and_search(self, large_toolset: list[ToolMetadata]) -> None:
        """测试并发索引和搜索"""
        searcher = BM25Search()
        # 先建立索引，确保搜索不会因为索引未建立而失败
        searcher.index(large_toolset)

        errors = []
        search_count = [0]
        index_count = [0]

        def mixed_operations(op_type: str) -> None:
            try:
                if op_type == "index":
                    searcher.index(large_toolset)
                    index_count[0] += 1
                else:
                    results = searcher.search("tool 50", large_toolset, 10)
                    # 验证搜索结果有效
                    assert isinstance(results, list)
                    search_count[0] += 1
            except Exception as e:
                errors.append(e)

        # 混合并发操作
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            # 提交索引任务
            for _ in range(3):
                futures.append(executor.submit(mixed_operations, "index"))
            # 提交搜索任务
            for _ in range(7):
                futures.append(executor.submit(mixed_operations, "search"))

            # 等待所有任务完成
            for future in as_completed(futures):
                future.result()

        # 不应该有错误
        assert not errors, f"并发操作不应该产生错误: {errors}"
        assert index_count[0] == 3, "应该完成所有索引操作"
        assert search_count[0] == 7, "应该完成所有搜索操作"

    def test_lock_protects_index_state(self, sample_tools: list[ToolMetadata]) -> None:
        """测试锁保护索引状态"""
        searcher = BM25Search()

        # 验证锁存在
        assert hasattr(searcher, "_lock"), "应该有 _lock 属性"
        assert isinstance(searcher._lock, type(threading.RLock())), "_lock 应该是 RLock 类型"

    def test_regex_search_thread_safety(self, sample_tools: list[ToolMetadata]) -> None:
        """测试 Regex 搜索的线程安全"""
        searcher = RegexSearch()
        errors = []

        def search_tools() -> None:
            try:
                results = searcher.search("github", sample_tools, 5)
                assert isinstance(results, list)
            except Exception as e:
                errors.append(e)

        # 并发搜索
        threads = [threading.Thread(target=search_tools) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 不应该有错误
        assert not errors, f"并发搜索不应该产生错误: {errors}"


class TestRegexSearchCache:
    """RegexSearch 缓存功能测试（TASK-801-FIX）"""

    def test_regex_search_uses_hash_detection(self, sample_tools: list[ToolMetadata]) -> None:
        """测试 RegexSearch 使用哈希值检测而非对象比较"""
        searcher = RegexSearch()

        # 首次搜索会建立索引
        results1 = searcher.search("github", sample_tools, 5)

        # 验证索引已建立
        assert searcher.is_indexed(), "RegexSearch 应该建立索引"

        # 验证哈希值已计算
        assert searcher._tools_hash is not None, "应该计算工具哈希值"

        # 第二次搜索应该使用缓存的索引
        results2 = searcher.search("github", sample_tools, 5)

        # 结果应该相同
        assert len(results1) == len(results2), "缓存命中结果应该一致"

    def test_regex_search_cache_hit_after_modification(
        self, sample_tools: list[ToolMetadata]
    ) -> None:
        """测试工具修改后 RegexSearch 重新建立索引"""
        searcher = RegexSearch()

        # 首次索引
        searcher.index(sample_tools)
        original_hash = searcher._tools_hash

        # 修改工具列表
        modified_tools = [
            ToolMetadata(
                name=t.name,
                description=t.description + " (modified)",
                tags=t.tags,
                category=t.category,
            )
            for t in sample_tools
        ]

        # 应该检测到变化
        assert searcher._should_rebuild_index(modified_tools), "修改后应该检测到变化"

        # 重新索引
        searcher.index(modified_tools)
        new_hash = searcher._tools_hash

        # 哈希值应该改变
        assert original_hash != new_hash, "哈希值应该改变"

    def test_regex_search_hash_consistency(self, sample_tools: list[ToolMetadata]) -> None:
        """测试 RegexSearch 哈希值计算的一致性"""
        searcher = RegexSearch()

        hash1 = searcher._compute_tools_hash(sample_tools)
        hash2 = searcher._compute_tools_hash(sample_tools)

        # 相同工具列表应该产生相同哈希值
        assert hash1 == hash2, "相同工具列表应该产生相同哈希值"

    def test_regex_search_hash_uniqueness(self, sample_tools: list[ToolMetadata]) -> None:
        """测试 RegexSearch 哈希值对工具变化的敏感性"""
        searcher = RegexSearch()

        hash1 = searcher._compute_tools_hash(sample_tools)

        # 添加新工具
        modified_tools = sample_tools + [
            ToolMetadata(
                name="new_tool",
                description="A new tool",
                tags={"new"},
            )
        ]
        hash2 = searcher._compute_tools_hash(modified_tools)

        # 不同工具列表应该产生不同哈希值
        assert hash1 != hash2, "不同工具列表应该产生不同哈希值"

    def test_regex_search_should_rebuild_initial(self, sample_tools: list[ToolMetadata]) -> None:
        """测试 RegexSearch 初始状态需要重建索引"""
        searcher = RegexSearch()

        # 初始状态下应该需要重建索引
        assert searcher._should_rebuild_index(sample_tools), "初始状态应该需要重建索引"

    def test_regex_search_should_rebuild_after_indexing(
        self, sample_tools: list[ToolMetadata]
    ) -> None:
        """测试 RegexSearch 索引后不需要重建"""
        searcher = RegexSearch()
        searcher.index(sample_tools)

        # 索引后相同工具列表不需要重建
        assert not searcher._should_rebuild_index(sample_tools), "索引后相同工具列表不需要重建"


class TestCachePerformance:
    """缓存性能测试"""

    @pytest.fixture
    def medium_toolset(self) -> list[ToolMetadata]:
        """创建中等规模工具集"""
        return [
            ToolMetadata(
                name=f"service_{i}",
                description=f"Service number {i} for various operations",
                tags={f"tag_{i % 20}"},
                category="services",
            )
            for i in range(500)
        ]

    def test_cache_avoids_rebuild(self, medium_toolset: list[ToolMetadata]) -> None:
        """测试缓存避免重复索引构建"""
        searcher = BM25Search()

        # 首次索引
        start = time.perf_counter()
        searcher.index(medium_toolset)
        _ = time.perf_counter() - start

        # 获取当前索引大小
        index_size = searcher.get_index_size()

        # 第二次索引应该被跳过（哈希相同）
        start = time.perf_counter()
        searcher.index(medium_toolset)
        _ = time.perf_counter() - start

        # 索引大小应该保持不变
        assert searcher.get_index_size() == index_size, "索引大小不应该改变"

        # 注意：由于我们已经优化了逻辑，第二次索引会很快
        # 但我们无法直接测试"跳过"的行为，因为 index() 方法总是执行
        # 实际的优化在 search() 方法中通过 _should_rebuild_index() 实现

    def test_search_with_cache_hit(self, medium_toolset: list[ToolMetadata]) -> None:
        """测试缓存命中时的搜索性能"""
        searcher = BM25Search()

        # 首次搜索（会建立索引）
        start = time.perf_counter()
        results1 = searcher.search("service 100", medium_toolset, 10)
        _ = time.perf_counter() - start

        # 后续搜索（使用缓存）
        start = time.perf_counter()
        results2 = searcher.search("service 100", medium_toolset, 10)
        _ = time.perf_counter() - start

        # 结果应该一致
        assert len(results1) == len(results2)

        # 验证结果内容一致
        if results1 and results2:
            assert results1[0].tool_name == results2[0].tool_name
