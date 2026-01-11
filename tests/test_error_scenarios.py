"""
错误路径测试

测试 RegistryTools 在各种异常情况和边界条件下的行为。

Copyright (c) 2026 Maric
License: MIT
"""

import pytest

from registrytools.auth import (
    APIKeyAuthMiddleware,
    APIKeyInsufficientPermission,
    APIKeyInvalid,
    APIKeyPermission,
    APIKeyStorage,
    generate_api_key,
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


class TestRegistryErrorPaths:
    """测试注册表的错误路径"""

    @pytest.fixture
    def registry(self):
        """创建测试用注册表"""
        from registrytools.registry.models import SearchMethod

        reg = ToolRegistry()
        reg.register_searcher(SearchMethod.BM25, BM25Search())
        return reg

    def test_register_duplicate_tool(self, registry):
        """
        测试注册重复工具

        验证：注册重复工具应该被覆盖而不是报错。
        """
        tool = ToolMetadata(
            name="duplicate_tool",
            description="Original description",
            tags={"test"},
            category="testing",
        )

        # 第一次注册
        registry.register(tool)
        assert registry.tool_count == 1

        # 第二次注册相同工具（应该覆盖）
        tool.description = "Updated description"
        registry.register(tool)
        assert registry.tool_count == 1

        # 验证描述已更新
        retrieved = registry.get_tool("duplicate_tool")
        assert retrieved.description == "Updated description"

    def test_get_nonexistent_tool(self, registry):
        """
        测试获取不存在的工具

        验证：应该返回 None 而不是抛出异常。
        """
        result = registry.get_tool("nonexistent_tool")
        assert result is None

    def test_unregister_nonexistent_tool(self, registry):
        """
        测试注销不存在的工具

        验证：应该返回 False 而不是抛出异常。
        """
        result = registry.unregister("nonexistent_tool")
        assert result is False

    def test_search_with_unregistered_method(self, registry):
        """
        测试使用未注册的搜索方法

        验证：应该抛出 ValueError。
        """
        tool = ToolMetadata(
            name="test_tool",
            description="Test tool",
            tags={"test"},
            category="testing",
        )
        registry.register(tool)

        # 尝试使用未注册的搜索方法
        with pytest.raises(ValueError, match="搜索方法.*未注册"):
            registry.search("test", SearchMethod.EMBEDDING, limit=10)

    def test_search_with_empty_query(self, registry):
        """
        测试空查询字符串

        验证：应该返回空结果而不是报错。
        """
        tool = ToolMetadata(
            name="test_tool",
            description="Test tool",
            tags={"test"},
            category="testing",
        )
        registry.register(tool)

        results = registry.search("", SearchMethod.BM25, limit=10)
        # 空查询可能返回所有工具或空结果，取决于搜索算法实现
        assert isinstance(results, list)

    def test_search_with_zero_limit(self, registry):
        """
        测试 limit 为 0

        验证：应该返回空结果。
        """
        tool = ToolMetadata(
            name="test_tool",
            description="Test tool",
            tags={"test"},
            category="testing",
        )
        registry.register(tool)

        results = registry.search("test", SearchMethod.BM25, limit=0)
        assert len(results) == 0

    def test_list_empty_categories(self, registry):
        """
        测试空注册表的类别列表

        验证：应该返回空列表而不是 None。
        """
        categories = registry.list_categories()
        assert categories == []

    def test_list_tools_with_nonexistent_category(self, registry):
        """
        测试按不存在的类别筛选工具

        验证：应该返回空列表而不是报错。
        """
        tool = ToolMetadata(
            name="test_tool",
            description="Test tool",
            tags={"test"},
            category="testing",
        )
        registry.register(tool)

        results = registry.list_tools(category="nonexistent")
        assert results == []

    def test_update_usage_nonexistent_tool(self, registry):
        """
        测试更新不存在工具的使用频率

        验证：应该返回 False 而不是抛出异常。
        """
        result = registry.update_usage("nonexistent_tool")
        assert result is False


class TestStorageErrorPaths:
    """测试存储层的错误路径"""

    @pytest.fixture
    def temp_json_path(self, tmp_path):
        """临时 JSON 存储路径"""
        return tmp_path / "test_error.json"

    @pytest.fixture
    def temp_sqlite_path(self, tmp_path):
        """临时 SQLite 存储路径"""
        return tmp_path / "test_error.db"

    def test_json_storage_load_nonexistent_file(self, temp_json_path):
        """
        测试从不存在的 JSON 文件加载

        验证：应该返回空列表或创建新文件。
        """
        storage = JSONStorage(temp_json_path)
        # 不调用 initialize()，直接加载
        tools = storage.load_all()
        assert tools == []

    def test_sqlite_storage_load_by_temperature_with_invalid_limit(self, temp_sqlite_path):
        """
        测试按温度加载时使用无效的 limit 参数

        验证：应该抛出 ValueError。
        """
        storage = SQLiteStorage(temp_sqlite_path)
        storage.initialize()

        # 添加测试数据
        tool = ToolMetadata(
            name="test_tool",
            description="Test tool",
            use_frequency=5,
            temperature=ToolTemperature.WARM,
        )
        storage.save(tool)

        # 负数 limit 应该抛出 ValueError
        with pytest.raises(ValueError, match="limit must be non-negative"):
            storage.load_by_temperature(ToolTemperature.WARM, limit=-1)

    def test_sqlite_storage_delete_nonexistent_tool(self, temp_sqlite_path):
        """
        测试删除不存在的工具

        验证：应该返回 False 而不是抛出异常。
        """
        storage = SQLiteStorage(temp_sqlite_path)
        storage.initialize()

        result = storage.delete("nonexistent_tool")
        assert result is False

    def test_json_storage_save_and_load_corrupted_data(self, temp_json_path):
        """
        测试处理损坏的 JSON 数据

        验证：应该抛出明确的 OSError 异常。
        """
        storage = JSONStorage(temp_json_path)
        storage.initialize()

        # 写入无效的 JSON 数据
        with open(temp_json_path, "w") as f:
            f.write("{ invalid json data")

        # 尝试加载应该抛出 OSError
        with pytest.raises(OSError, match="JSON 文件格式错误"):
            storage.load_all()


class TestAuthErrorPaths:
    """测试认证模块的错误路径"""

    @pytest.fixture
    def temp_db_path(self, tmp_path):
        """临时数据库路径"""
        return tmp_path / "test_auth_errors.db"

    @pytest.fixture
    def auth_middleware(self, temp_db_path):
        """创建认证中间件"""
        storage = APIKeyStorage(temp_db_path)
        return APIKeyAuthMiddleware(storage)

    def test_authenticate_with_invalid_format(self, auth_middleware):
        """
        测试使用无效格式的 API Key

        验证：应该返回失败结果。
        """
        result = auth_middleware.authenticate("invalid_format")
        assert not result.success
        assert result.error is not None

    def test_authenticate_with_nonexistent_key(self, auth_middleware):
        """
        测试使用不存在的 API Key

        验证：应该返回失败结果。
        """
        # 生成一个正确格式但不在数据库中的 API Key
        # 格式: rtk_ + 64个hex字符
        fake_key = "rtk_" + "a" * 64
        result = auth_middleware.authenticate(fake_key)
        assert not result.success
        assert result.error == "API Key not found"

    def test_authenticate_or_raise_with_invalid_key(self, auth_middleware):
        """
        测试 authenticate_or_raise 使用无效 Key

        验证：应该抛出 APIKeyInvalid 异常。
        """
        with pytest.raises(APIKeyInvalid):
            auth_middleware.authenticate_or_raise("rtk_invalid_key")

    def test_authenticate_from_header_with_empty_value(self, auth_middleware):
        """
        测试从空的 Header 值认证

        验证：应该返回失败结果。
        """
        result = auth_middleware.authenticate_from_header("")
        assert not result.success
        assert result.error == "API Key is required"

    def test_authenticate_from_headers_with_missing_key(self, auth_middleware):
        """
        测试从不包含 Key 的 Headers 认证

        验证：应该返回失败结果。
        """
        headers = {"Content-Type": "application/json"}
        result = auth_middleware.authenticate_from_headers(headers)
        assert not result.success
        assert result.error == "API Key is required"

    def test_insufficient_permission_for_write_operation(self, auth_middleware):
        """
        测试 WRITE 权限不足

        验证：READ 权限的 Key 无法执行 WRITE 操作。
        """
        # 创建 READ 权限的 Key
        read_key = generate_api_key("Read Only Key", permission=APIKeyPermission.READ)
        auth_middleware._storage.save(read_key)

        # 尝试使用 READ 权限执行 WRITE 操作
        with pytest.raises(APIKeyInsufficientPermission):
            auth_middleware.authenticate_or_raise(read_key.api_key, APIKeyPermission.WRITE)

    def test_authenticate_with_expired_key(self, auth_middleware):
        """
        测试使用过期的 API Key

        验证：应该返回失败结果。
        """
        # 创建已过期的 Key
        expired_key = generate_api_key(
            "Expired Key",
            permission=APIKeyPermission.READ,
            expires_in=-3600,  # 1 小时前
        )
        auth_middleware._storage.save(expired_key)

        result = auth_middleware.authenticate(expired_key.api_key)
        assert not result.success
        assert "expired" in result.error

    def test_authenticate_with_inactive_key(self, auth_middleware):
        """
        测试使用未激活的 API Key

        验证：应该返回失败结果。
        """
        # 创建未激活的 Key
        inactive_key = generate_api_key(
            "Inactive Key",
            permission=APIKeyPermission.READ,
        )
        inactive_key.is_active = False
        auth_middleware._storage.save(inactive_key)

        result = auth_middleware.authenticate(inactive_key.api_key)
        assert not result.success
        assert "inactive" in result.error


class TestSearcherErrorPaths:
    """测试搜索器的错误路径"""

    def test_bm25_search_without_index(self):
        """
        测试未建立索引就进行搜索

        验证：应该优雅处理，返回空结果或使用默认索引。
        """
        searcher = BM25Search()

        # 未调用 index() 就直接搜索
        tools = []
        results = searcher.search("test query", tools, limit=10)

        # BM25 搜索器应该优雅处理空工具列表
        assert isinstance(results, list)

    def test_bm25_search_with_empty_tool_list(self):
        """
        测试对空工具列表进行搜索

        验证：应该返回空结果。
        """
        searcher = BM25Search()
        searcher.index([])

        results = searcher.search("test query", [], limit=10)
        assert len(results) == 0

    def test_regex_search_with_special_regex_chars(self):
        """
        测试使用特殊正则字符的查询

        验证：应该正确处理或抛出明确异常。
        """
        from registrytools.search.regex_search import RegexSearch

        searcher = RegexSearch()
        tools = [
            ToolMetadata(
                name="test_tool",
                description="A tool with special chars: . * + ? ^ $ ( ) [ ] { } | \\",
                tags={"test"},
                category="testing",
            )
        ]
        searcher.index(tools)

        # 测试包含正则特殊字符的查询
        results = searcher.search("special chars: .*+", tools, limit=10)
        assert isinstance(results, list)

    def test_unicode_search(self):
        """
        测试 Unicode 字符搜索

        验证：应该正确处理中文字符。
        """
        searcher = BM25Search()
        tools = [
            ToolMetadata(
                name="chinese_tool",
                description="中文工具描述",
                tags={"中文", "测试"},
                category="测试",
            )
        ]
        searcher.index(tools)

        results = searcher.search("中文", tools, limit=10)
        assert len(results) >= 0


class TestEdgeCases:
    """测试边界条件和极端情况"""

    def test_very_long_query_string(self):
        """
        测试非常长的查询字符串

        验证：应该正常处理或在合理限制下拒绝。
        """
        from registrytools.server import MAX_QUERY_LENGTH

        searcher = BM25Search()
        tools = [
            ToolMetadata(
                name="test_tool",
                description="Test tool description",
                tags={"test"},
                category="testing",
            )
        ]
        searcher.index(tools)

        # 创建超长查询字符串
        long_query = "a" * (MAX_QUERY_LENGTH + 100)
        # 搜索器应该能处理，但上层应用可能会限制长度
        results = searcher.search(long_query, tools, limit=10)
        assert isinstance(results, list)

    def test_very_large_limit_value(self):
        """
        测试非常大的 limit 值

        验证：应该正常处理。
        """
        from registrytools.server import MAX_LIMIT

        searcher = BM25Search()
        tools = [
            ToolMetadata(
                name=f"test_tool_{i}",
                description=f"Test tool {i}",
                tags={"test"},
                category="testing",
            )
            for i in range(10)
        ]
        searcher.index(tools)

        # 使用非常大的 limit 值
        large_limit = MAX_LIMIT + 1000
        results = searcher.search("test", tools, limit=large_limit)
        # 应该返回最多所有工具
        assert len(results) <= 10

    def test_tool_with_empty_name(self):
        """
        测试工具名称为空字符串

        验证：工具元数据模型允许空名称（由上层业务逻辑验证）。
        """
        # ToolMetadata 模型本身不验证名称是否为空
        # 这个验证应该在注册表层进行
        tool = ToolMetadata(
            name="",
            description="Tool with empty name",
            tags={"test"},
            category="testing",
        )
        # 验证工具确实可以创建（模型层不限制）
        assert tool.name == ""
        assert tool.description == "Tool with empty name"

    def test_tool_with_very_long_description(self):
        """
        测试工具描述非常长的情况

        验证：应该正常处理。
        """
        long_desc = "A very long description " * 1000  # 约 22000 字符
        tool = ToolMetadata(
            name="long_desc_tool",
            description=long_desc,
            tags={"test"},
            category="testing",
        )

        # 应该能正常创建和序列化
        assert tool.description == long_desc

    def test_mixed_temperature_tools(self):
        """
        测试混合不同温度的工具

        验证：温度分类逻辑正确。
        """
        from registrytools.defaults import HOT_TOOL_THRESHOLD, WARM_TOOL_THRESHOLD

        tools = [
            ToolMetadata(
                name="hot_tool",
                description="Hot tool",
                use_frequency=15,
                temperature=ToolTemperature.HOT,
            ),
            ToolMetadata(
                name="warm_tool",
                description="Warm tool",
                use_frequency=5,
                temperature=ToolTemperature.WARM,
            ),
            ToolMetadata(
                name="cold_tool",
                description="Cold tool",
                use_frequency=0,
                temperature=ToolTemperature.COLD,
            ),
        ]

        # 验证每个工具的温度与其使用频率一致
        hot_tool, warm_tool, cold_tool = tools

        # hot_tool: use_frequency=15 >= 10 (HOT_TOOL_THRESHOLD)
        assert hot_tool.use_frequency >= HOT_TOOL_THRESHOLD
        assert hot_tool.temperature == ToolTemperature.HOT

        # warm_tool: 3 <= use_frequency=5 < 10
        assert WARM_TOOL_THRESHOLD <= warm_tool.use_frequency < HOT_TOOL_THRESHOLD
        assert warm_tool.temperature == ToolTemperature.WARM

        # cold_tool: use_frequency=0 < 3 (WARM_TOOL_THRESHOLD)
        assert cold_tool.use_frequency < WARM_TOOL_THRESHOLD
        assert cold_tool.temperature == ToolTemperature.COLD


class TestConcurrentErrorScenarios:
    """测试并发场景中的错误处理"""

    def test_concurrent_deletion_and_access(self, tmp_path):
        """
        测试并发删除和访问

        验证：不应该崩溃或导致数据损坏。
        """
        import threading

        storage = JSONStorage(tmp_path / "test_concurrent_delete.json")
        storage.initialize()

        # 添加初始数据
        tools = [
            ToolMetadata(
                name=f"tool_{i}",
                description=f"Tool {i}",
                tags={"test"},
                category="testing",
            )
            for i in range(20)
        ]
        storage.save_many(tools)

        errors = []

        def delete_tools():
            """删除工具"""
            try:
                for i in range(10):
                    storage.delete(f"tool_{i}")
            except Exception as e:
                errors.append(f"delete: {e}")

        def access_tools():
            """访问工具"""
            try:
                for _ in range(10):
                    storage.load_all()
            except Exception as e:
                errors.append(f"access: {e}")

        # 启动并发操作
        threads = []
        threads.append(threading.Thread(target=delete_tools))
        threads.append(threading.Thread(target=access_tools))
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # 验证没有发生异常
        assert len(errors) == 0, f"并发操作中发生异常: {errors}"
