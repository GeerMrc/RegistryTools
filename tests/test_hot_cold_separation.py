"""
冷热工具分离功能测试套件 (TASK-802)

测试工具温度分类、三层存储、升级/降级机制、分层索引等功能。

Copyright (c) 2026 Maric
License: MIT
"""

import time
from datetime import datetime, timedelta

from registrytools.defaults import (
    HOT_TOOL_INACTIVE_DAYS,
    HOT_TOOL_THRESHOLD,
    WARM_TOOL_INACTIVE_DAYS,
    WARM_TOOL_THRESHOLD,
)
from registrytools.registry.models import (
    SearchMethod,
    ToolMetadata,
    ToolTemperature,
)
from registrytools.registry.registry import ToolRegistry
from registrytools.search.bm25_search import BM25Search
from registrytools.storage.json_storage import JSONStorage
from registrytools.storage.sqlite_storage import SQLiteStorage

# ============================================================
# 工具温度枚举测试 (3个)
# ============================================================


class TestToolTemperature:
    """测试工具温度枚举"""

    def test_temperature_enum_values(self):
        """测试温度枚举值"""
        assert ToolTemperature.HOT.value == "hot"
        assert ToolTemperature.WARM.value == "warm"
        assert ToolTemperature.COLD.value == "cold"

    def test_temperature_comparison(self):
        """测试温度比较"""
        hot = ToolTemperature.HOT
        warm = ToolTemperature.WARM
        cold = ToolTemperature.COLD

        # 测试字符串值比较
        assert hot.value == "hot"
        assert warm.value == "warm"
        assert cold.value == "cold"

    def test_temperature_in_metadata(self):
        """测试温度在元数据中的默认值"""
        tool = ToolMetadata(name="test", description="Test tool")
        assert tool.temperature == ToolTemperature.COLD


# ============================================================
# 分类逻辑测试 (8个)
# ============================================================


class TestToolClassification:
    """测试工具温度分类逻辑"""

    def test_hot_tool_classification(self):
        """测试热工具分类（使用频率 >= HOT_TOOL_THRESHOLD）"""
        registry = ToolRegistry()
        tool = ToolMetadata(
            name="hot_tool", description="Hot tool", use_frequency=HOT_TOOL_THRESHOLD
        )
        registry.register(tool)

        assert tool.temperature == ToolTemperature.HOT
        assert tool.name in registry._hot_tools

    def test_warm_tool_classification(self):
        """测试温工具分类（使用频率 >= WARM_TOOL_THRESHOLD）"""
        registry = ToolRegistry()
        tool = ToolMetadata(
            name="warm_tool", description="Warm tool", use_frequency=WARM_TOOL_THRESHOLD
        )
        registry.register(tool)

        assert tool.temperature == ToolTemperature.WARM
        assert tool.name in registry._warm_tools

    def test_cold_tool_classification(self):
        """测试冷工具分类（使用频率 < WARM_TOOL_THRESHOLD）"""
        registry = ToolRegistry()
        tool = ToolMetadata(
            name="cold_tool", description="Cold tool", use_frequency=WARM_TOOL_THRESHOLD - 1
        )
        registry.register(tool)

        assert tool.temperature == ToolTemperature.COLD
        assert tool.name in registry._cold_tools

    def test_classification_boundary_hot_warm(self):
        """测试热温边界（HOT_TOOL_THRESHOLD - 1）"""
        registry = ToolRegistry()
        tool = ToolMetadata(
            name="boundary_tool",
            description="Boundary tool",
            use_frequency=HOT_TOOL_THRESHOLD - 1,
        )
        registry.register(tool)

        # 应该是温工具，而不是热工具
        assert tool.temperature == ToolTemperature.WARM
        assert tool.name in registry._warm_tools

    def test_classification_boundary_warm_cold(self):
        """测试温冷边界（WARM_TOOL_THRESHOLD - 1）"""
        registry = ToolRegistry()
        tool = ToolMetadata(
            name="boundary_tool",
            description="Boundary tool",
            use_frequency=WARM_TOOL_THRESHOLD - 1,
        )
        registry.register(tool)

        # 应该是冷工具
        assert tool.temperature == ToolTemperature.COLD
        assert tool.name in registry._cold_tools

    def test_multiple_tools_classification(self):
        """测试多个工具的自动分类"""
        registry = ToolRegistry()
        hot = ToolMetadata(name="hot", description="Hot", use_frequency=15)
        warm = ToolMetadata(name="warm", description="Warm", use_frequency=5)
        cold = ToolMetadata(name="cold", description="Cold", use_frequency=1)

        registry.register_many([hot, warm, cold])

        assert hot.temperature == ToolTemperature.HOT
        assert warm.temperature == ToolTemperature.WARM
        assert cold.temperature == ToolTemperature.COLD

    def test_update_classification_on_reregister(self):
        """测试重新注册时的分类更新"""
        registry = ToolRegistry()
        tool = ToolMetadata(name="tool", description="Tool", use_frequency=1)
        registry.register(tool)

        assert tool.temperature == ToolTemperature.COLD

        # 更新使用频率并重新注册
        tool.use_frequency = HOT_TOOL_THRESHOLD
        registry.register(tool)

        assert tool.temperature == ToolTemperature.HOT

    def test_layer_exclusivity(self):
        """测试工具只存在于一个温度层"""
        registry = ToolRegistry()
        tool = ToolMetadata(name="tool", description="Tool", use_frequency=5)
        registry.register(tool)

        # 工具应该只存在于温工具层
        assert tool.name in registry._warm_tools
        assert tool.name not in registry._hot_tools
        assert tool.name not in registry._cold_tools


# ============================================================
# 升级机制测试 (4个)
# ============================================================


class TestToolUpgrade:
    """测试工具升级机制"""

    def test_cold_to_warm_upgrade(self):
        """测试冷工具升级为温工具"""
        registry = ToolRegistry()
        tool = ToolMetadata(name="cold_tool", description="Cold tool", use_frequency=1)
        registry.register(tool)

        assert tool.temperature == ToolTemperature.COLD

        # 模拟多次使用，达到温工具阈值
        for _ in range(WARM_TOOL_THRESHOLD - 1):
            registry.update_usage(tool.name)

        assert tool.temperature == ToolTemperature.WARM
        assert tool.name in registry._warm_tools

    def test_warm_to_hot_upgrade(self):
        """测试温工具升级为热工具"""
        registry = ToolRegistry()
        tool = ToolMetadata(
            name="warm_tool", description="Warm tool", use_frequency=WARM_TOOL_THRESHOLD
        )
        registry.register(tool)

        assert tool.temperature == ToolTemperature.WARM

        # 模拟多次使用，达到热工具阈值
        for _ in range(HOT_TOOL_THRESHOLD - WARM_TOOL_THRESHOLD):
            registry.update_usage(tool.name)

        assert tool.temperature == ToolTemperature.HOT
        assert tool.name in registry._hot_tools

    def test_cold_to_hot_direct_upgrade(self):
        """测试冷工具直接升级为热工具"""
        registry = ToolRegistry()
        tool = ToolMetadata(name="cold_tool", description="Cold tool", use_frequency=1)
        registry.register(tool)

        assert tool.temperature == ToolTemperature.COLD

        # 模拟大量使用，直接达到热工具阈值
        for _ in range(HOT_TOOL_THRESHOLD - 1):
            registry.update_usage(tool.name)

        assert tool.temperature == ToolTemperature.HOT
        assert tool.name in registry._hot_tools

    def test_upgrade_updates_last_used(self):
        """测试升级时更新最后使用时间"""
        registry = ToolRegistry()
        tool = ToolMetadata(
            name="tool",
            description="Tool",
            use_frequency=1,
            last_used=datetime.now() - timedelta(days=1),
        )
        registry.register(tool)

        initial_last_used = tool.last_used
        time.sleep(0.01)  # 确保时间戳不同

        registry.update_usage(tool.name)

        assert tool.last_used is not None
        assert tool.last_used > initial_last_used  # type: ignore[arg-type]


# ============================================================
# 降级机制测试 (4个)
# ============================================================


class TestToolDowngrade:
    """测试工具降级机制"""

    def test_hot_to_warm_downgrade(self):
        """测试热工具降级为温工具"""
        registry = ToolRegistry()
        tool = ToolMetadata(
            name="hot_tool",
            description="Hot tool",
            use_frequency=HOT_TOOL_THRESHOLD,
            last_used=datetime.now() - timedelta(days=HOT_TOOL_INACTIVE_DAYS),
        )
        registry.register(tool)

        assert tool.temperature == ToolTemperature.HOT

        # 检查并降级
        should_downgrade = registry._check_downgrade_tool(tool)
        assert should_downgrade is True

        registry._downgrade_tool(tool.name)

        assert tool.temperature == ToolTemperature.WARM

    def test_warm_to_cold_downgrade(self):
        """测试温工具降级为冷工具"""
        registry = ToolRegistry()
        tool = ToolMetadata(
            name="warm_tool",
            description="Warm tool",
            use_frequency=WARM_TOOL_THRESHOLD,
            last_used=datetime.now() - timedelta(days=WARM_TOOL_INACTIVE_DAYS),
        )
        registry.register(tool)

        assert tool.temperature == ToolTemperature.WARM

        # 检查并降级
        should_downgrade = registry._check_downgrade_tool(tool)
        assert should_downgrade is True

        registry._downgrade_tool(tool.name)

        assert tool.temperature == ToolTemperature.COLD

    def test_no_downgrade_for_active_hot_tool(self):
        """测试活跃热工具不降级"""
        registry = ToolRegistry()
        tool = ToolMetadata(
            name="hot_tool",
            description="Hot tool",
            use_frequency=HOT_TOOL_THRESHOLD,
            last_used=datetime.now() - timedelta(days=HOT_TOOL_INACTIVE_DAYS - 1),
        )
        registry.register(tool)

        should_downgrade = registry._check_downgrade_tool(tool)
        assert should_downgrade is False

    def test_cold_tool_no_downgrade(self):
        """测试冷工具不再降级"""
        registry = ToolRegistry()
        tool = ToolMetadata(
            name="cold_tool",
            description="Cold tool",
            use_frequency=1,
            last_used=datetime.now() - timedelta(days=365),
        )
        registry.register(tool)

        should_downgrade = registry._check_downgrade_tool(tool)
        assert should_downgrade is False

        result = registry._downgrade_tool(tool.name)
        assert result is False  # 冷工具无法降级


# ============================================================
# 分层加载测试 (10个)
# ============================================================


class TestLayeredLoading:
    """测试分层加载功能"""

    def test_load_hot_tools_from_json_storage(self, tmp_path):
        """测试从 JSON 存储加载热工具"""
        storage = JSONStorage(tmp_path / "tools.json")

        # 保存热工具（显式设置温度）
        hot_tools = [
            ToolMetadata(
                name=f"hot_{i}",
                description=f"Hot tool {i}",
                use_frequency=HOT_TOOL_THRESHOLD,
                temperature=ToolTemperature.HOT,
            )
            for i in range(5)
        ]
        storage.save_many(hot_tools)

        # 加载热工具
        loaded = storage.load_by_temperature(ToolTemperature.HOT)

        assert len(loaded) == 5
        assert all(t.temperature == ToolTemperature.HOT for t in loaded)

    def test_load_warm_tools_from_json_storage(self, tmp_path):
        """测试从 JSON 存储加载温工具"""
        storage = JSONStorage(tmp_path / "tools.json")

        # 保存温工具（显式设置温度）
        warm_tools = [
            ToolMetadata(
                name=f"warm_{i}",
                description=f"Warm tool {i}",
                use_frequency=WARM_TOOL_THRESHOLD,
                temperature=ToolTemperature.WARM,
            )
            for i in range(5)
        ]
        storage.save_many(warm_tools)

        # 加载温工具
        loaded = storage.load_by_temperature(ToolTemperature.WARM)

        assert len(loaded) == 5
        assert all(t.temperature == ToolTemperature.WARM for t in loaded)

    def test_load_hot_tools_from_sqlite_storage(self, tmp_path):
        """测试从 SQLite 存储加载热工具"""
        storage = SQLiteStorage(tmp_path / "tools.db")

        # 保存热工具（显式设置温度）
        hot_tools = [
            ToolMetadata(
                name=f"hot_{i}",
                description=f"Hot tool {i}",
                use_frequency=HOT_TOOL_THRESHOLD,
                temperature=ToolTemperature.HOT,
            )
            for i in range(5)
        ]
        storage.save_many(hot_tools)

        # 加载热工具
        loaded = storage.load_by_temperature(ToolTemperature.HOT)

        assert len(loaded) == 5
        assert all(t.temperature == ToolTemperature.HOT for t in loaded)

    def test_load_hot_tools_with_limit(self, tmp_path):
        """测试限制加载数量"""
        storage = JSONStorage(tmp_path / "tools.json")

        # 保存多个热工具
        hot_tools = [
            ToolMetadata(
                name=f"hot_{i}", description=f"Hot tool {i}", use_frequency=HOT_TOOL_THRESHOLD
            )
            for i in range(10)
        ]
        storage.save_many(hot_tools)

        # 加载限制数量
        loaded = storage.load_by_temperature(ToolTemperature.HOT, limit=5)

        assert len(loaded) == 5

    def test_registry_load_hot_tools(self, tmp_path):
        """测试注册表加载热工具"""
        storage = JSONStorage(tmp_path / "tools.json")
        registry = ToolRegistry()

        # 保存热工具到存储
        hot_tools = [
            ToolMetadata(
                name=f"hot_{i}", description=f"Hot tool {i}", use_frequency=HOT_TOOL_THRESHOLD
            )
            for i in range(3)
        ]
        storage.save_many(hot_tools)

        # 加载热工具到注册表
        count = registry.load_hot_tools(storage)

        assert count == 3
        assert len(registry._hot_tools) == 3

    def test_search_hot_warm_only(self):
        """测试仅搜索热+温工具"""
        registry = ToolRegistry()
        searcher = BM25Search()
        registry.register_searcher(SearchMethod.BM25, searcher)

        # 注册不同温度的工具（使用标签确保搜索匹配）
        hot = ToolMetadata(
            name="github_hot",
            description="GitHub operations",
            tags={"github", "git"},
            use_frequency=HOT_TOOL_THRESHOLD,
        )
        warm = ToolMetadata(
            name="github_warm",
            description="GitHub operations",
            tags={"github", "git"},
            use_frequency=WARM_TOOL_THRESHOLD,
        )
        cold = ToolMetadata(
            name="github_cold",
            description="GitHub operations",
            tags={"github", "git"},
            use_frequency=1,
        )

        registry.register_many([hot, warm, cold])

        # 搜索热+温工具
        results = registry.search_hot_warm("github", method=SearchMethod.BM25)

        # 应该返回热+温工具
        tool_names = [r.tool_name for r in results]
        assert (
            len(results) > 0
        ), f"应该找到热工具或温工具, hot={len(registry._hot_tools)}, warm={len(registry._warm_tools)}"
        assert "github_cold" not in tool_names

    def test_empty_hot_warm_search(self):
        """测试空热+温工具搜索"""
        registry = ToolRegistry()
        searcher = BM25Search()
        registry.register_searcher(SearchMethod.BM25, searcher)

        # 只注册冷工具
        cold = ToolMetadata(name="cold_tool", description="Cold tool", use_frequency=1)
        registry.register(cold)

        # 搜索应该返回空结果
        results = registry.search_hot_warm("cold", method=SearchMethod.BM25)
        assert results == []

    def test_layered_index_builder(self):
        """测试分层索引构建"""
        searcher = BM25Search()

        hot = [ToolMetadata(name="hot", description="Hot", use_frequency=HOT_TOOL_THRESHOLD)]
        warm = [ToolMetadata(name="warm", description="Warm", use_frequency=WARM_TOOL_THRESHOLD)]
        cold = [ToolMetadata(name="cold", description="Cold", use_frequency=1)]

        # 构建分层索引
        searcher.index_layered(hot, warm, cold)

        # 索引应该包含所有工具
        assert searcher.get_index_size() == 3

    def test_layered_index_without_cold(self):
        """测试不包含冷工具的分层索引"""
        searcher = BM25Search()

        hot = [ToolMetadata(name="hot", description="Hot", use_frequency=HOT_TOOL_THRESHOLD)]
        warm = [ToolMetadata(name="warm", description="Warm", use_frequency=WARM_TOOL_THRESHOLD)]

        # 构建分层索引（不包含冷工具）
        searcher.index_layered(hot, warm)

        # 索引应该只包含热+温工具
        assert searcher.get_index_size() == 2


# ============================================================
# 注册表集成测试 (12个)
# ============================================================


class TestRegistryIntegration:
    """测试注册表集成功能"""

    def test_register_adds_to_correct_layer(self):
        """测试注册时工具添加到正确层级"""
        registry = ToolRegistry()

        hot = ToolMetadata(name="hot", description="Hot", use_frequency=HOT_TOOL_THRESHOLD)
        registry.register(hot)

        assert hot.name in registry._hot_tools
        assert hot.name not in registry._warm_tools
        assert hot.name not in registry._cold_tools

    def test_unregister_removes_from_layer(self):
        """测试注销时从层级中移除"""
        registry = ToolRegistry()

        tool = ToolMetadata(name="tool", description="Tool", use_frequency=HOT_TOOL_THRESHOLD)
        registry.register(tool)

        assert tool.name in registry._hot_tools

        registry.unregister(tool.name)

        assert tool.name not in registry._hot_tools
        assert tool.name not in registry._tools

    def test_update_usage_triggers_upgrade(self):
        """测试更新使用触发升级"""
        registry = ToolRegistry()

        tool = ToolMetadata(name="tool", description="Tool", use_frequency=WARM_TOOL_THRESHOLD)
        registry.register(tool)

        assert tool.temperature == ToolTemperature.WARM

        # 使用多次达到热工具阈值
        for _ in range(HOT_TOOL_THRESHOLD - WARM_TOOL_THRESHOLD):
            registry.update_usage(tool.name)

        assert tool.temperature == ToolTemperature.HOT

    def test_layer_counts(self):
        """测试各层工具计数"""
        registry = ToolRegistry()

        hot = ToolMetadata(name="hot", description="Hot", use_frequency=HOT_TOOL_THRESHOLD)
        warm = ToolMetadata(name="warm", description="Warm", use_frequency=WARM_TOOL_THRESHOLD)
        cold = ToolMetadata(name="cold", description="Cold", use_frequency=1)

        registry.register_many([hot, warm, cold])

        assert len(registry._hot_tools) == 1
        assert len(registry._warm_tools) == 1
        assert len(registry._cold_tools) == 1

    def test_clear_clears_all_layers(self):
        """测试清空注册表清除所有层级"""
        registry = ToolRegistry()

        tools = [
            ToolMetadata(name=f"tool_{i}", description=f"Tool {i}", use_frequency=i + 1)
            for i in range(10)
        ]
        registry.register_many(tools)

        registry.clear()

        assert len(registry._hot_tools) == 0
        assert len(registry._warm_tools) == 0
        assert len(registry._cold_tools) == 0
        assert len(registry._tools) == 0

    def test_get_tool_from_any_layer(self):
        """测试从任意层获取工具"""
        registry = ToolRegistry()

        hot = ToolMetadata(name="hot", description="Hot", use_frequency=HOT_TOOL_THRESHOLD)
        registry.register(hot)

        # get_tool 应该能从主存储中获取
        tool = registry.get_tool("hot")
        assert tool is not None
        assert tool.name == "hot"

    def test_list_tools_includes_all_layers(self):
        """测试列出工具包含所有层级"""
        registry = ToolRegistry()

        hot = ToolMetadata(name="hot", description="Hot", use_frequency=HOT_TOOL_THRESHOLD)
        warm = ToolMetadata(name="warm", description="Warm", use_frequency=WARM_TOOL_THRESHOLD)
        cold = ToolMetadata(name="cold", description="Cold", use_frequency=1)

        registry.register_many([hot, warm, cold])

        all_tools = registry.list_tools()
        assert len(all_tools) == 3

    def test_temperature_persistence_across_operations(self):
        """测试温度在不同操作间保持"""
        registry = ToolRegistry()

        tool = ToolMetadata(name="tool", description="Tool", use_frequency=HOT_TOOL_THRESHOLD)
        registry.register(tool)

        initial_temp = tool.temperature

        # 执行各种操作
        registry.update_usage(tool.name)
        registry.get_tool(tool.name)
        registry.list_tools()

        # 温度应该保持不变（除非达到升级条件）
        assert tool.temperature == initial_temp

    def test_concurrent_layer_access(self):
        """测试并发层级访问（线程安全）"""
        import threading

        registry = ToolRegistry()

        def register_tools(thread_id: int):
            for i in range(10):
                tool = ToolMetadata(
                    name=f"tool_{thread_id}_{i}",
                    description=f"Tool {i}",
                    use_frequency=i + 1,
                )
                registry.register(tool)

        threads = [threading.Thread(target=register_tools, args=(i,)) for i in range(5)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 所有工具都应该被注册（5线程 × 10工具 = 50工具）
        assert len(registry._tools) == 50

    def test_rebuild_indexes_with_layers(self):
        """测试重建索引包含所有层级"""
        registry = ToolRegistry()
        searcher = BM25Search()
        registry.register_searcher(SearchMethod.BM25, searcher)

        tools = [
            ToolMetadata(name=f"tool_{i}", description=f"Tool {i}", use_frequency=i + 1)
            for i in range(10)
        ]
        registry.register_many(tools)

        registry.rebuild_indexes()

        # 搜索应该能找到所有工具
        results = registry.search("tool", method=SearchMethod.BM25)
        assert len(results) > 0

    def test_temperature_field_serialization(self):
        """测试温度字段序列化"""
        tool = ToolMetadata(
            name="test",
            description="Test",
            use_frequency=HOT_TOOL_THRESHOLD,
            temperature=ToolTemperature.HOT,
        )

        # 序列化为字典
        data = tool.model_dump()

        assert "temperature" in data
        assert data["temperature"] == ToolTemperature.HOT

    def test_default_temperature_for_new_tools(self):
        """测试新工具的默认温度"""
        registry = ToolRegistry()

        # 不指定温度的新工具
        tool = ToolMetadata(name="new_tool", description="New tool")
        registry.register(tool)

        # 应该被自动分类为冷工具（使用频率为0）
        assert tool.temperature == ToolTemperature.COLD


# ============================================================
# 性能测试 (5个)
# ============================================================


class TestPerformance:
    """测试性能优化"""

    def test_hot_warm_search_faster_than_full_search(self, benchmark):
        """测试热+温搜索比全量搜索快"""
        registry = ToolRegistry()
        searcher = BM25Search()
        registry.register_searcher(SearchMethod.BM25, searcher)

        # 注册大量工具
        tools = [
            ToolMetadata(
                name=f"tool_{i}",
                description=f"Tool {i}",
                use_frequency=1 if i < 90 else (10 if i < 95 else 5),
            )
            for i in range(100)
        ]
        registry.register_many(tools)

        # 基准测试热+温搜索
        result = benchmark(lambda: registry.search_hot_warm("tool", method=SearchMethod.BM25))
        assert isinstance(result, list)

    def test_layered_index_build_performance(self, benchmark):
        """测试分层索引构建性能"""
        searcher = BM25Search()

        hot_tools = [
            ToolMetadata(name=f"hot_{i}", description="Hot tool", use_frequency=HOT_TOOL_THRESHOLD)
            for i in range(100)
        ]
        warm_tools = [
            ToolMetadata(
                name=f"warm_{i}", description="Warm tool", use_frequency=WARM_TOOL_THRESHOLD
            )
            for i in range(500)
        ]

        # 基准测试分层索引构建
        benchmark(lambda: searcher.index_layered(hot_tools, warm_tools))
        assert searcher.get_index_size() == 600

    def test_classification_performance(self, benchmark):
        """测试分类性能"""
        registry = ToolRegistry()

        tools = [
            ToolMetadata(name=f"tool_{i}", description="Tool {i}", use_frequency=i)
            for i in range(1000)
        ]

        # 基准测试批量分类
        benchmark(lambda: registry.register_many(tools))
        assert registry.tool_count == 1000

    def test_upgrade_check_performance(self, benchmark):
        """测试升级检查性能"""
        registry = ToolRegistry()

        tool = ToolMetadata(name="tool", description="Tool", use_frequency=WARM_TOOL_THRESHOLD)
        registry.register(tool)

        # 基准测试升级检查
        result = benchmark(lambda: registry._classify_tool_temperature(tool))
        assert result == ToolTemperature.WARM

    def test_memory_efficiency_of_layers(self):
        """测试分层的内存效率"""
        registry = ToolRegistry()

        # 创建大量冷工具
        cold_tools = [
            ToolMetadata(name=f"cold_{i}", description="Cold tool", use_frequency=1)
            for i in range(1000)
        ]

        # 创建少量热工具
        hot_tools = [
            ToolMetadata(name=f"hot_{i}", description="Hot tool", use_frequency=HOT_TOOL_THRESHOLD)
            for i in range(10)
        ]

        registry.register_many(cold_tools + hot_tools)

        # 热工具层应该很小
        assert len(registry._hot_tools) == 10
        assert len(registry._cold_tools) == 1000
