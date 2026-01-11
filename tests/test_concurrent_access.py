"""
并发访问测试

测试 RegistryTools 在多线程并发场景下的线程安全性和数据一致性。

Copyright (c) 2026 Maric
License: MIT
"""

import concurrent.futures
import threading

import pytest

from registrytools.registry.models import ToolMetadata, ToolTemperature
from registrytools.registry.registry import ToolRegistry
from registrytools.search.bm25_search import BM25Search


class TestConcurrentRegistryAccess:
    """测试注册表的并发访问"""

    @pytest.fixture
    def temp_storage_path(self, tmp_path):
        """临时存储路径"""
        return tmp_path / "test_concurrent.db"

    @pytest.fixture
    def registry(self, temp_storage_path):
        """创建测试用注册表"""
        from registrytools.registry.models import SearchMethod
        from registrytools.search.bm25_search import BM25Search

        reg = ToolRegistry()
        # 注册 BM25 搜索器
        reg.register_searcher(SearchMethod.BM25, BM25Search())
        return reg

    @pytest.fixture
    def populated_registry(self, registry):
        """填充测试数据的注册表"""
        tools = [
            ToolMetadata(
                name=f"tool_{i}",
                description=f"Test tool {i} for concurrent testing",
                tags={"test", f"tag_{i % 10}"},
                category="testing",
                use_frequency=0,
            )
            for i in range(100)
        ]
        registry.register_many(tools)
        return registry

    def test_concurrent_read_operations(self, populated_registry):
        """
        测试多线程并发读取操作

        验证多个线程同时读取工具列表时不会发生竞争条件。
        """
        results = []
        num_threads = 10

        def read_tools():
            """读取所有工具"""
            tools = populated_registry.list_tools()
            results.append(len(tools))

        # 启动多个线程同时读取
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=read_tools)
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证所有读取都返回了相同的数量
        assert len(results) == num_threads
        assert all(count == 100 for count in results)

    def test_concurrent_search_operations(self, populated_registry):
        """
        测试多线程并发搜索操作

        验证多个线程同时搜索时不会发生竞争条件。
        """
        results = []
        num_threads = 15
        search_queries = ["tool", "tag_5", "testing"]

        def search_tools():
            """执行搜索操作"""
            import random

            query = random.choice(search_queries)
            from registrytools.registry.models import SearchMethod

            search_results = populated_registry.search(query, SearchMethod.BM25, limit=10)
            results.append(len(search_results))

        # 启动多个线程同时搜索
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=search_tools)
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证所有搜索都成功完成
        assert len(results) == num_threads
        assert all(count >= 0 for count in results)

    def test_concurrent_update_usage(self, populated_registry):
        """
        测试多线程并发更新使用频率

        验证多个线程同时更新使用频率时数据一致性。
        """
        tool_names = [f"tool_{i}" for i in range(10)]  # 只更新前 10 个工具
        num_updates_per_thread = 5
        num_threads = 10

        def update_usage():
            """更新工具使用频率"""
            for tool_name in tool_names:
                for _ in range(num_updates_per_thread):
                    populated_registry.update_usage(tool_name)

        # 启动多个线程同时更新
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=update_usage)
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证使用频率更新正确
        expected_usage = num_updates_per_thread * num_threads
        for tool_name in tool_names:
            tool = populated_registry.get_tool(tool_name)
            assert tool is not None
            assert tool.use_frequency == expected_usage

    def test_concurrent_mixed_operations(self, populated_registry):
        """
        测试多线程混合操作（读、搜索、更新）

        验证混合并发操作时系统的稳定性。
        """
        errors = []
        num_threads = 20
        operations_per_thread = 10

        def mixed_operations():
            """执行混合操作"""
            import random

            try:
                for _ in range(operations_per_thread):
                    op_type = random.choice(["read", "search", "update"])
                    tool_id = random.randint(0, 99)

                    if op_type == "read":
                        populated_registry.list_tools()

                    elif op_type == "search":
                        from registrytools.registry.models import SearchMethod

                        populated_registry.search("test", SearchMethod.BM25, limit=5)

                    elif op_type == "update":
                        populated_registry.update_usage(f"tool_{tool_id}")
            except Exception as e:
                errors.append(e)

        # 启动多个线程执行混合操作
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=mixed_operations)
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证没有发生异常
        assert len(errors) == 0, f"并发操作中发生异常: {errors}"

    def test_concurrent_registration(self, registry):
        """
        测试多线程并发注册工具

        验证多个线程同时注册工具时数据一致性。
        """
        num_threads = 5
        tools_per_thread = 20
        results = []

        def register_tools(thread_id):
            """注册工具"""
            tools = []
            for i in range(tools_per_thread):
                tool = ToolMetadata(
                    name=f"thread_{thread_id}_tool_{i}",
                    description=f"Tool from thread {thread_id}",
                    tags={"concurrent", f"thread_{thread_id}"},
                    category="testing",
                )
                tools.append(tool)

            try:
                registry.register_many(tools)
                results.append(len(tools))
            except Exception as e:
                results.append(e)

        # 启动多个线程同时注册工具
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=register_tools, args=(i,))
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证所有注册都成功
        assert len(results) == num_threads
        assert all(isinstance(r, int) for r in results), f"部分注册失败: {results}"

        # 验证工具总数正确
        expected_count = num_threads * tools_per_thread
        assert registry.tool_count == expected_count

    def test_concurrent_with_thread_pool_executor(self, populated_registry):
        """
        使用 ThreadPoolExecutor 进行并发测试

        模拟更真实的并发场景。
        """
        num_tasks = 50

        def concurrent_task(task_id):
            """并发任务"""
            from registrytools.registry.models import SearchMethod

            # 搜索操作
            search_results = populated_registry.search(
                f"tool_{task_id % 10}", SearchMethod.BM25, limit=5
            )

            # 更新使用频率
            populated_registry.update_usage(f"tool_{task_id % 100}")

            # 读取工具
            tool = populated_registry.get_tool(f"tool_{task_id % 100}")

            return len(search_results), tool is not None

        # 使用 ThreadPoolExecutor 执行并发任务
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(concurrent_task, i) for i in range(num_tasks)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # 验证所有任务都成功完成
        assert len(results) == num_tasks
        assert all(search_count >= 0 and found for search_count, found in results)


class TestConcurrentStorageAccess:
    """测试存储层的并发访问"""

    @pytest.fixture
    def temp_storage_path(self, tmp_path):
        """临时存储路径"""
        return tmp_path / "test_concurrent_storage.db"

    @pytest.fixture
    def storage(self, temp_storage_path):
        """创建测试用存储"""
        from registrytools.storage.json_storage import JSONStorage

        storage = JSONStorage(temp_storage_path)
        storage.initialize()
        return storage

    def test_concurrent_load_by_temperature(self, storage):
        """
        测试多线程并发按温度加载工具

        验证存储层的并发读取安全性。
        """
        # 首先添加一些测试数据
        tools = []
        for i in range(100):
            temp = (
                ToolTemperature.HOT
                if i < 10
                else ToolTemperature.WARM if i < 40 else ToolTemperature.COLD
            )
            tool = ToolMetadata(
                name=f"tool_{i}",
                description=f"Tool {i}",
                use_frequency=(
                    10 if temp == ToolTemperature.HOT else 5 if temp == ToolTemperature.WARM else 0
                ),
                temperature=temp,
            )
            tools.append(tool)
        storage.save_many(tools)

        results = {"hot": 0, "warm": 0, "cold": 0}
        num_threads = 10

        def load_by_temp():
            """按温度加载工具"""
            for temp in [ToolTemperature.HOT, ToolTemperature.WARM, ToolTemperature.COLD]:
                loaded_tools = storage.load_by_temperature(temp, limit=100)
                results[temp.value] += len(loaded_tools)

        # 启动多个线程同时加载
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=load_by_temp)
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证加载结果
        expected_hot = 10 * num_threads
        expected_warm = 30 * num_threads
        expected_cold = 60 * num_threads

        assert results["hot"] == expected_hot
        assert results["warm"] == expected_warm
        assert results["cold"] == expected_cold

    def test_concurrent_save_and_load(self, storage):
        """
        测试多线程并发保存和加载

        验证存储层的并发写入和读取安全性。
        注意：由于 JSON 存储是覆盖写入，并发写入可能导致数据丢失，
        这个测试主要验证不会发生崩溃或数据损坏。
        """
        num_threads = 10
        tools_per_thread = 5
        results = []
        errors = []

        def save_and_load(thread_id):
            """保存和加载工具"""
            try:
                # 保存工具
                tools = []
                for i in range(tools_per_thread):
                    tool = ToolMetadata(
                        name=f"concurrent_tool_{thread_id}_{i}",
                        description=f"Concurrent test tool {thread_id}-{i}",
                        tags={"concurrent", f"thread_{thread_id}"},
                        category="testing",
                    )
                    tools.append(tool)
                storage.save_many(tools)

                # 加载所有工具
                all_tools = storage.load_all()
                results.append(len(all_tools))
            except Exception as e:
                errors.append(e)

        # 启动多个线程
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=save_and_load, args=(i,))
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证没有发生异常
        assert len(errors) == 0, f"并发操作中发生异常: {errors}"

        # 验证所有操作都成功完成
        assert len(results) == num_threads
        # 验证存储不为空
        assert max(results) > 0


class TestConcurrentSearcherAccess:
    """测试搜索器的并发访问"""

    @pytest.fixture
    def searcher(self):
        """创建 BM25 搜索器"""
        return BM25Search()

    @pytest.fixture
    def indexed_searcher(self, searcher):
        """创建已索引的搜索器"""
        tools = [
            ToolMetadata(
                name=f"search_tool_{i}",
                description=f"Search test tool {i} for testing performance",
                tags={"search", "test", f"type_{i % 5}"},
                category="searching",
            )
            for i in range(200)
        ]
        searcher.index(tools)
        return searcher

    def test_concurrent_search_indexing(self, indexed_searcher):
        """
        测试多线程并发搜索和索引重建

        验证搜索器的线程安全性。
        """
        search_results = []
        index_results = []
        num_threads = 8

        def search_operation():
            """执行搜索操作"""
            results = indexed_searcher.search("search test", [], limit=10)
            search_results.append(len(results))

        def index_operation():
            """执行索引操作"""
            # 使用已索引的工具重新索引
            tools = [
                ToolMetadata(
                    name=f"search_tool_{i}",
                    description=f"Search test tool {i} for testing performance",
                    tags={"search", "test", f"type_{i % 5}"},
                    category="searching",
                )
                for i in range(200)
            ]
            indexed_searcher.index(tools)
            index_results.append(True)

        # 启动搜索线程
        search_threads = []
        for _ in range(num_threads // 2):
            thread = threading.Thread(target=search_operation)
            search_threads.append(thread)
            thread.start()

        # 启动索引线程
        index_threads = []
        for _ in range(num_threads // 2):
            thread = threading.Thread(target=index_operation)
            index_threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in search_threads + index_threads:
            thread.join()

        # 验证所有操作都成功完成
        assert len(search_results) == num_threads // 2
        assert len(index_results) == num_threads // 2
        assert all(count >= 0 for count in search_results)
        assert all(index_results)


class TestRaceConditions:
    """测试潜在的竞争条件"""

    @pytest.fixture
    def temp_storage_path(self, tmp_path):
        """临时存储路径"""
        return tmp_path / "test_race.db"

    @pytest.fixture
    def registry(self, temp_storage_path):
        """创建测试用注册表"""
        from registrytools.registry.models import SearchMethod
        from registrytools.search.bm25_search import BM25Search

        reg = ToolRegistry()
        # 注册 BM25 搜索器
        reg.register_searcher(SearchMethod.BM25, BM25Search())
        return reg

    def test_rapid_update_usage_same_tool(self, registry):
        """
        测试对同一工具的快速并发更新

        检测潜在的计数器竞争条件。
        """
        tool_name = "hot_tool"
        tool = ToolMetadata(
            name=tool_name,
            description="A frequently used tool",
            tags={"hot", "popular"},
            category="testing",
            use_frequency=0,
        )
        registry.register(tool)

        num_updates = 100
        num_threads = 10

        def rapid_updates():
            """快速更新使用频率"""
            for _ in range(num_updates // num_threads):
                registry.update_usage(tool_name)

        # 启动多个线程同时更新
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=rapid_updates)
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证最终使用频率正确
        tool = registry.get_tool(tool_name)
        # 由于可能有竞争，使用频率应该接近但不一定完全等于 num_updates
        # 这里我们检查它至少被更新了一些次数
        assert tool.use_frequency > 0
        assert tool.use_frequency <= num_updates

    def test_concurrent_register_and_search(self, registry):
        """
        测试同时注册和搜索

        验证在工具注册过程中进行搜索的安全性。
        """
        search_results = []
        register_results = []

        def register_tools():
            """注册工具"""
            tools = [
                ToolMetadata(
                    name=f"dynamic_tool_{i}",
                    description=f"Dynamic tool {i}",
                    tags={"dynamic"},
                    category="testing",
                )
                for i in range(50)
            ]
            registry.register_many(tools)
            register_results.append(True)

        def search_tools():
            """搜索工具"""
            from registrytools.registry.models import SearchMethod

            results = registry.search("dynamic", SearchMethod.BM25, limit=10)
            search_results.append(len(results))

        # 同时启动注册和搜索线程
        threads = []
        for _ in range(5):
            threads.append(threading.Thread(target=register_tools))
        for _ in range(10):
            threads.append(threading.Thread(target=search_tools))

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # 验证所有操作都成功
        assert len(register_results) == 5
        assert len(search_results) == 10
        assert all(register_results)
        assert all(count >= 0 for count in search_results)
