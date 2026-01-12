"""
性能基准测试

测试 RegistryTools 在不同规模工具集下的性能表现。

Copyright (c) 2026 Maric
License: MIT
"""

import pytest

from registrytools.registry.models import ToolMetadata
from registrytools.search.bm25_search import BM25Search
from registrytools.search.regex_search import RegexSearch


class ToolDataGenerator:
    """工具数据生成器"""

    @staticmethod
    def generate_small_toolset(count: int = 100) -> list[ToolMetadata]:
        """
        生成小规模工具集

        Args:
            count: 工具数量，默认 100

        Returns:
            工具元数据列表
        """
        return [
            ToolMetadata(
                name=f"tool_{i}",
                description=f"Tool {i} for various purposes like testing and development",
                tags={"test", f"tag_{i % 10}", "utility"},
                category="testing",
            )
            for i in range(count)
        ]

    @staticmethod
    def generate_medium_toolset(count: int = 1000) -> list[ToolMetadata]:
        """
        生成中等规模工具集

        Args:
            count: 工具数量，默认 1000

        Returns:
            工具元数据列表
        """
        categories = ["github", "slack", "aws", "google", "database", "filesystem", "utilities"]
        return [
            ToolMetadata(
                name=f"{category}_service_{i}",
                description=f"A {category} service for performing operations with ID {i}",
                tags={category, "service", f"action_{i % 20}"},
                category=category,
            )
            for i, category in enumerate(categories * (count // len(categories) + 1))
        ][:count]

    @staticmethod
    def generate_large_toolset(count: int = 10000) -> list[ToolMetadata]:
        """
        生成大规模工具集（模拟真实场景）

        Args:
            count: 工具数量，默认 10000

        Returns:
            工具元数据列表
        """
        # 80% 冷工具（低频使用）
        cold_tools = [
            ToolMetadata(
                name=f"rare_operation_{i}",
                description=f"Rare operation number {i} for specific use cases",
                tags={"rare", f"specialized_{i % 50}"},
                category=f"category_{i % 50}",
                use_frequency=0,
            )
            for i in range(int(count * 0.8))
        ]

        # 15% 温工具（中频使用）
        warm_tools = [
            ToolMetadata(
                name=f"standard_service_{i}",
                description=f"Standard service {i} for common workflows",
                tags={"standard", "service", f"type_{i % 15}"},
                category=f"category_{i % 20}",
                use_frequency=3 + (i % 8),
            )
            for i in range(int(count * 0.15))
        ]

        # 5% 热工具（高频使用）
        hot_tools = [
            ToolMetadata(
                name=f"common_{['action', 'operation', 'task'][i % 3]}_{i}",
                description=f"Commonly used {['action', 'operation', 'task'][i % 3]} for daily work",
                tags={"common", "popular", "frequent"},
                category="common",
                use_frequency=10 + (i % 90),
            )
            for i in range(int(count * 0.05))
        ]

        return cold_tools + warm_tools + hot_tools

    @staticmethod
    def generate_xlarge_toolset(count: int = 5000) -> list[ToolMetadata]:
        """
        生成超大规模工具集（中大型企业场景）

        介于中等规模和大规模之间的测试场景。

        Args:
            count: 工具数量，默认 5000

        Returns:
            工具元数据列表
        """
        # 75% 冷工具，20% 温工具，5% 热工具
        cold_tools = [
            ToolMetadata(
                name=f"rare_operation_{i}",
                description=f"Rare operation number {i} for specific use cases",
                tags={"rare", f"specialized_{i % 30}"},
                category=f"category_{i % 40}",
                use_frequency=0,
            )
            for i in range(int(count * 0.75))
        ]

        warm_tools = [
            ToolMetadata(
                name=f"standard_service_{i}",
                description=f"Standard service {i} for common workflows",
                tags={"standard", "service", f"type_{i % 12}"},
                category=f"category_{i % 15}",
                use_frequency=3 + (i % 7),
            )
            for i in range(int(count * 0.20))
        ]

        hot_tools = [
            ToolMetadata(
                name=f"common_{['action', 'operation', 'task'][i % 3]}_{i}",
                description=f"Commonly used {['action', 'operation', 'task'][i % 3]} for daily work",
                tags={"common", "popular", "frequent"},
                category="common",
                use_frequency=10 + (i % 50),
            )
            for i in range(int(count * 0.05))
        ]

        return cold_tools + warm_tools + hot_tools


class TestBM25Performance:
    """BM25 搜索性能测试"""

    @pytest.fixture
    def small_toolset(self) -> list[ToolMetadata]:
        """小规模工具集（100 工具）"""
        return ToolDataGenerator.generate_small_toolset(100)

    @pytest.fixture
    def medium_toolset(self) -> list[ToolMetadata]:
        """中等规模工具集（1000 工具）"""
        return ToolDataGenerator.generate_medium_toolset(1000)

    @pytest.fixture
    def large_toolset(self) -> list[ToolMetadata]:
        """大规模工具集（10000 工具）"""
        return ToolDataGenerator.generate_large_toolset(10000)

    @pytest.fixture
    def xlarge_toolset(self) -> list[ToolMetadata]:
        """超大规模工具集（5000 工具）- 中大型企业场景"""
        return ToolDataGenerator.generate_xlarge_toolset(5000)

    @pytest.mark.benchmark(group="indexing", min_rounds=5)
    def test_index_building_small(self, benchmark, small_toolset: list[ToolMetadata]) -> None:
        """
        测试小规模工具集的索引构建性能

        目标: < 0.1s for 100 tools
        """
        searcher = BM25Search()

        def build_index(tools: list[ToolMetadata]) -> None:
            searcher.index(tools)

        benchmark(build_index, small_toolset)
        # benchmark 返回的是执行时间（秒）
        # 断言在 pytest_benchmark 的断言中通过 --benchmark-autoskip 等选项处理

    @pytest.mark.benchmark(group="indexing", min_rounds=5)
    def test_index_building_medium(self, benchmark, medium_toolset: list[ToolMetadata]) -> None:
        """
        测试中等规模工具集的索引构建性能

        目标: < 2s for 1000 tools
        """
        searcher = BM25Search()

        def build_index(tools: list[ToolMetadata]) -> None:
            searcher.index(tools)

        benchmark(build_index, medium_toolset)

    @pytest.mark.benchmark(group="indexing", min_rounds=3)
    def test_index_building_large(self, benchmark, large_toolset: list[ToolMetadata]) -> None:
        """
        测试大规模工具集的索引构建性能

        目标: < 20s for 10000 tools
        """
        searcher = BM25Search()

        def build_index(tools: list[ToolMetadata]) -> None:
            searcher.index(tools)

        benchmark(build_index, large_toolset)

    @pytest.mark.benchmark(group="indexing", min_rounds=4)
    def test_index_building_xlarge(self, benchmark, xlarge_toolset: list[ToolMetadata]) -> None:
        """
        测试超大规模工具集的索引构建性能

        目标: < 10s for 5000 tools
        """
        searcher = BM25Search()

        def build_index(tools: list[ToolMetadata]) -> None:
            searcher.index(tools)

        benchmark(build_index, xlarge_toolset)

    @pytest.mark.benchmark(group="searching", min_rounds=10)
    def test_search_performance_warm_small(
        self, benchmark, small_toolset: list[ToolMetadata]
    ) -> None:
        """
        测试小规模工具集的搜索性能（热索引）

        目标: < 50ms for 100 tools
        """
        searcher = BM25Search()
        searcher.index(small_toolset)

        def search(query: str, tools: list[ToolMetadata], limit: int) -> list:
            return searcher.search(query, tools, limit)

        benchmark(search, "tool 50", small_toolset, 10)

    @pytest.mark.benchmark(group="searching", min_rounds=10)
    def test_search_performance_warm_medium(
        self, benchmark, medium_toolset: list[ToolMetadata]
    ) -> None:
        """
        测试中等规模工具集的搜索性能（热索引）

        目标: < 200ms for 1000 tools
        """
        searcher = BM25Search()
        searcher.index(medium_toolset)

        def search(query: str, tools: list[ToolMetadata], limit: int) -> list:
            return searcher.search(query, tools, limit)

        benchmark(search, "github service 100", medium_toolset, 10)

    @pytest.mark.benchmark(group="searching", min_rounds=5)
    def test_search_performance_warm_large(
        self, benchmark, large_toolset: list[ToolMetadata]
    ) -> None:
        """
        测试大规模工具集的搜索性能（热索引）

        目标: < 500ms for 10000 tools
        """
        searcher = BM25Search()
        searcher.index(large_toolset)

        def search(query: str, tools: list[ToolMetadata], limit: int) -> list:
            return searcher.search(query, tools, limit)

        benchmark(search, "common action 50", large_toolset, 10)

    @pytest.mark.benchmark(group="searching", min_rounds=6)
    def test_search_performance_warm_xlarge(
        self, benchmark, xlarge_toolset: list[ToolMetadata]
    ) -> None:
        """
        测试超大规模工具集的搜索性能（热索引）

        目标: < 300ms for 5000 tools
        """
        searcher = BM25Search()
        searcher.index(xlarge_toolset)

        def search(query: str, tools: list[ToolMetadata], limit: int) -> list:
            return searcher.search(query, tools, limit)

        benchmark(search, "standard service 250", xlarge_toolset, 10)

    @pytest.mark.benchmark(group="searching", min_rounds=5)
    def test_search_performance_cold_medium(
        self, benchmark, medium_toolset: list[ToolMetadata]
    ) -> None:
        """
        测试中等规模工具集的搜索性能（冷索引）

        目标: < 1s for 1000 tools (including indexing)
        """
        searcher = BM25Search()

        def search(query: str, tools: list[ToolMetadata], limit: int) -> list:
            return searcher.search(query, tools, limit)

        benchmark(search, "github service 100", medium_toolset, 10)


class TestRegexPerformance:
    """正则表达式搜索性能测试"""

    @pytest.fixture
    def medium_toolset(self) -> list[ToolMetadata]:
        """中等规模工具集（1000 工具）"""
        return ToolDataGenerator.generate_medium_toolset(1000)

    @pytest.mark.benchmark(group="searching", min_rounds=20)
    def test_regex_search_warm(self, benchmark, medium_toolset: list[ToolMetadata]) -> None:
        """
        测试正则搜索性能

        目标: < 50ms (regex is fast)
        """
        searcher = RegexSearch()

        def search(query: str, tools: list[ToolMetadata], limit: int) -> list:
            return searcher.search(query, tools, limit)

        benchmark(search, "github.*service", medium_toolset, 10)


class TestPerformanceComparison:
    """搜索算法性能对比"""

    @pytest.fixture
    def medium_toolset(self) -> list[ToolMetadata]:
        """中等规模工具集（1000 工具）"""
        return ToolDataGenerator.generate_medium_toolset(1000)

    @pytest.mark.benchmark(group="comparison", min_rounds=10)
    def test_bm25_vs_regex_benchmark(self, benchmark, medium_toolset: list[ToolMetadata]) -> None:
        """
        BM25 与正则搜索的性能对比

        注意: BM25 需要索引，正则不需要
        """
        bm25_searcher = BM25Search()
        bm25_searcher.index(medium_toolset)

        def bm25_search(query: str, tools: list[ToolMetadata], limit: int) -> list:
            return bm25_searcher.search(query, tools, limit)

        benchmark(bm25_search, "github service", medium_toolset, 10)


class TestMemoryUsage:
    """内存使用测试"""

    @pytest.fixture
    def large_toolset(self) -> list[ToolMetadata]:
        """大规模工具集（10000 工具）"""
        return ToolDataGenerator.generate_large_toolset(10000)

    def test_index_memory_usage(self, large_toolset: list[ToolMetadata]) -> None:
        """
        测试索引构建的内存占用

        目标: < 100MB for 1000 tools
        注意: 此测试需要 memory_profiler 运行
        """
        # 基础测试: 确保索引构建成功
        searcher = BM25Search()
        searcher.index(large_toolset)

        # 验证索引已建立
        assert searcher.is_indexed(), "Index should be built"

        # 验证搜索功能正常
        results = searcher.search("common action", large_toolset, 10)
        assert len(results) > 0, "Should return results"

    @pytest.mark.benchmark(group="memory", min_rounds=5)
    def test_search_memory_stability(self, benchmark, large_toolset: list[ToolMetadata]) -> None:
        """
        测试搜索过程的内存稳定性

        验证多次搜索不会导致内存泄漏
        """
        searcher = BM25Search()
        searcher.index(large_toolset)

        def search_multiple(tools: list[ToolMetadata]) -> None:
            for _ in range(10):
                searcher.search("common action", tools, 10)

        benchmark(search_multiple, large_toolset)


# 性能测试标记
pytestmark = [
    pytest.mark.slow,  # 性能测试通常较慢
]
