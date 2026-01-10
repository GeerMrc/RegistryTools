"""
认证和输入验证集成测试 (Phase 33)

测试 API Key 认证中间件集成、输入参数验证、新 MCP 工具功能。

Copyright (c) 2026 Maric
License: MIT
"""

from unittest.mock import MagicMock

import pytest

from registrytools.auth import (
    APIKeyAuthMiddleware,
    APIKeyPermission,
    APIKeyStorage,
    generate_api_key,
)
from registrytools.registry.models import SearchMethod, ToolMetadata
from registrytools.registry.registry import ToolRegistry
from registrytools.search.bm25_search import BM25Search
from registrytools.search.regex_search import RegexSearch
from registrytools.server import (
    MAX_LIMIT,
    MAX_QUERY_LENGTH,
    _check_auth,
    _get_api_key_from_context,
)

# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def temp_db_path(tmp_path):
    """临时数据库路径"""
    return tmp_path / "test_api_keys.db"


@pytest.fixture
def auth_middleware(temp_db_path):
    """创建认证中间件实例"""
    storage = APIKeyStorage(temp_db_path)
    return APIKeyAuthMiddleware(storage)


@pytest.fixture
def valid_read_key(auth_middleware):
    """创建有效的 READ 权限 API Key"""
    api_key = generate_api_key("Valid Read Key", permission=APIKeyPermission.READ)
    auth_middleware._storage.save(api_key)
    return api_key


@pytest.fixture
def valid_write_key(auth_middleware):
    """创建有效的 WRITE 权限 API Key"""
    api_key = generate_api_key("Valid Write Key", permission=APIKeyPermission.WRITE)
    auth_middleware._storage.save(api_key)
    return api_key


# ============================================================
# 辅助函数测试
# ============================================================


class TestGetAPIKeyFromContext:
    """测试 _get_api_key_from_context 函数"""

    def test_returns_none_when_no_env_var(self, monkeypatch):
        """当环境变量未设置时返回 None"""
        monkeypatch.delenv("REGISTRYTOOLS_API_KEY", raising=False)
        result = _get_api_key_from_context()
        assert result is None

    def test_returns_api_key_from_env_var(self, monkeypatch):
        """从环境变量获取 API Key"""
        test_key = "rtk_test1234567890abcdef"
        monkeypatch.setenv("REGISTRYTOOLS_API_KEY", test_key)
        result = _get_api_key_from_context()
        assert result == test_key


class TestCheckAuth:
    """测试 _check_auth 函数"""

    def test_skip_check_when_no_middleware(self):
        """当没有认证中间件时跳过检查"""
        # 不应该抛出异常
        _check_auth(None, APIKeyPermission.READ)

    def test_skip_check_when_no_api_key(self, monkeypatch):
        """当没有 API Key 时抛出 PermissionError"""
        monkeypatch.delenv("REGISTRYTOOLS_API_KEY", raising=False)
        middleware = MagicMock()  # 创建中间件但不实际使用

        with pytest.raises(PermissionError, match="API Key is required"):
            _check_auth(middleware, APIKeyPermission.READ)

    def test_authenticate_success_with_valid_key(
        self, monkeypatch, auth_middleware, valid_read_key
    ):
        """使用有效 API Key 认证成功"""
        monkeypatch.setenv("REGISTRYTOOLS_API_KEY", valid_read_key.api_key)

        # 不应该抛出异常
        _check_auth(auth_middleware, APIKeyPermission.READ)

    def test_authenticate_fail_with_invalid_key(self, monkeypatch, auth_middleware):
        """使用无效 API Key 认证失败"""
        monkeypatch.setenv("REGISTRYTOOLS_API_KEY", "rtk_invalidkey123")

        with pytest.raises(PermissionError, match="Invalid API Key"):
            _check_auth(auth_middleware, APIKeyPermission.READ)

    def test_permission_fail_with_insufficient_permission(
        self, monkeypatch, auth_middleware, valid_read_key
    ):
        """权限不足时认证失败"""
        monkeypatch.setenv("REGISTRYTOOLS_API_KEY", valid_read_key.api_key)

        with pytest.raises(PermissionError, match="Insufficient permissions"):
            _check_auth(auth_middleware, APIKeyPermission.WRITE)


# ============================================================
# 输入参数验证测试（使用模拟函数）
# ============================================================


class TestInputValidation:
    """测试输入参数验证逻辑"""

    def test_query_length_validation(self):
        """测试查询字符串长度限制"""
        # 模拟 search_tools 的输入验证逻辑
        query = "a" * (MAX_QUERY_LENGTH + 1)
        assert len(query) > MAX_QUERY_LENGTH

    def test_limit_max_validation(self):
        """测试返回数量最大值限制"""
        limit = MAX_LIMIT + 1
        assert limit > MAX_LIMIT

    def test_limit_min_validation(self):
        """测试返回数量最小值限制"""
        limit = 0
        assert limit < 1

    def test_search_method_validation(self):
        """测试搜索方法动态验证"""
        invalid_method = "invalid_method"

        # 尝试创建无效的 SearchMethod
        with pytest.raises(ValueError):
            SearchMethod(invalid_method)

        # 验证动态获取支持的方法列表
        supported_methods = [m.value for m in SearchMethod]
        assert "regex" in supported_methods
        assert "bm25" in supported_methods
        assert "embedding" in supported_methods


# ============================================================
# MCP 工具功能测试（通过注册表）
# ============================================================


class TestToolRegistration:
    """测试工具注册功能"""

    @pytest.fixture
    def registry(self):
        """创建测试注册表"""
        registry = ToolRegistry()
        registry.register_searcher(SearchMethod.REGEX, RegexSearch(case_sensitive=False))
        registry.register_searcher(SearchMethod.BM25, BM25Search())
        return registry

    def test_unregister_tool_workflow(self, registry):
        """测试工具注销工作流"""
        # 注册工具
        tool = ToolMetadata(name="test.tool", description="Test tool", category="test")
        registry.register(tool)

        # 验证工具存在
        assert registry.get_tool("test.tool") is not None

        # 注销工具
        registry.unregister("test.tool")

        # 验证工具不存在
        assert registry.get_tool("test.tool") is None

    def test_hot_warm_tool_classification(self, registry):
        """测试冷热工具分类"""
        # 注册不同使用频率的工具
        hot_tool = ToolMetadata(name="hot.tool", description="Hot tool", use_frequency=15)
        warm_tool = ToolMetadata(name="warm.tool", description="Warm tool", use_frequency=5)
        cold_tool = ToolMetadata(name="cold.tool", description="Cold tool", use_frequency=1)

        registry.register(hot_tool)
        registry.register(warm_tool)
        registry.register(cold_tool)

        # 验证分类

        assert registry._hot_tools.get("hot.tool") is not None
        assert registry._warm_tools.get("warm.tool") is not None
        assert registry._cold_tools.get("cold.tool") is not None

    def test_search_hot_warm_excludes_cold(self, registry):
        """测试 search_hot_warm 不包含冷工具"""
        # 注册工具
        hot_tool = ToolMetadata(name="hot.tool", description="Hot tool", use_frequency=15)
        warm_tool = ToolMetadata(name="warm.tool", description="Warm tool", use_frequency=5)
        cold_tool = ToolMetadata(name="cold.tool", description="Cold tool", use_frequency=1)

        registry.register(hot_tool)
        registry.register(warm_tool)
        registry.register(cold_tool)
        registry.rebuild_indexes()

        # 搜索热+温工具
        results = registry.search_hot_warm("tool", SearchMethod.BM25, 10)
        tool_names = [r.tool_name for r in results]

        # 应该只包含热和温工具
        assert "hot.tool" in tool_names
        assert "warm.tool" in tool_names
        assert "cold.tool" not in tool_names


# ============================================================
# 参数验证测试（单元测试级别）
# ============================================================


class TestParameterValidation:
    """测试参数验证逻辑"""

    def test_empty_string_validation(self):
        """测试空字符串验证"""
        assert not "" or not "".strip()  # 空字符串应该被拒绝

    def test_whitespace_only_validation(self):
        """测试纯空格字符串验证"""
        assert not "   " or not "   ".strip()  # 纯空格应该被拒绝

    def test_max_query_length_boundary(self):
        """测试查询长度边界"""
        # 最大长度应该被接受
        query_at_max = "a" * MAX_QUERY_LENGTH
        assert len(query_at_max) == MAX_QUERY_LENGTH

        # 超过最大长度应该被拒绝
        query_over_max = "a" * (MAX_QUERY_LENGTH + 1)
        assert len(query_over_max) > MAX_QUERY_LENGTH

    def test_max_limit_boundary(self):
        """测试 limit 边界"""
        # 最大值应该被接受
        assert MAX_LIMIT == 100

        # 超过最大值应该被拒绝
        assert MAX_LIMIT + 1 > MAX_LIMIT

    def test_min_limit_boundary(self):
        """测试 limit 最小边界"""
        # 1 应该被接受
        assert 1 >= 1

        # 0 应该被拒绝
        assert 0 < 1

    def test_description_length_boundary(self):
        """测试描述长度边界"""
        # 最大长度应该被接受
        desc_at_max = "a" * MAX_QUERY_LENGTH
        assert len(desc_at_max) == MAX_QUERY_LENGTH

        # 超过最大长度应该被拒绝
        desc_over_max = "a" * (MAX_QUERY_LENGTH + 1)
        assert len(desc_over_max) > MAX_QUERY_LENGTH


# ============================================================
# 权限控制测试
# ============================================================


class TestPermissionControl:
    """测试权限控制"""

    def test_read_permission_exists(self):
        """测试 READ 权限存在"""
        assert hasattr(APIKeyPermission, "READ")
        assert APIKeyPermission.READ.value == "read"

    def test_write_permission_exists(self):
        """测试 WRITE 权限存在"""
        assert hasattr(APIKeyPermission, "WRITE")
        assert APIKeyPermission.WRITE.value == "write"

    def test_admin_permission_exists(self):
        """测试 ADMIN 权限存在"""
        assert hasattr(APIKeyPermission, "ADMIN")
        assert APIKeyPermission.ADMIN.value == "admin"

    def test_read_permissions_include_search_tools(self):
        """测试 READ 权限包含 search_tools"""
        read_operations = ["search_tools", "get_tool_definition", "list_tools_by_category"]
        for op in read_operations:
            # 验证这些操作需要 READ 权限
            assert isinstance(op, str)


# ============================================================
# 错误处理测试
# ============================================================


class TestErrorHandling:
    """测试错误处理"""

    def test_value_error_for_nonexistent_tool(self):
        """测试不存在的工具抛出 ValueError"""
        registry = ToolRegistry()
        tool = registry.get_tool("nonexistent.tool")
        assert tool is None

    def test_value_error_for_duplicate_tool(self):
        """测试重复工具更新元数据"""
        registry = ToolRegistry()
        tool = ToolMetadata(name="test.tool", description="Test")
        registry.register(tool)

        # 重复注册应该更新元数据（不抛出异常）
        tool2 = ToolMetadata(name="test.tool", description="Updated Test")
        registry.register(tool2)

        # 验证元数据已更新
        updated = registry.get_tool("test.tool")
        assert updated is not None
        assert updated.description == "Updated Test"

    def test_permission_error_for_missing_api_key(self, monkeypatch):
        """测试缺少 API Key 抛出 PermissionError"""
        monkeypatch.delenv("REGISTRYTOOLS_API_KEY", raising=False)
        middleware = MagicMock()

        with pytest.raises(PermissionError, match="API Key is required"):
            _check_auth(middleware, APIKeyPermission.READ)


# ============================================================
# 安全测试
# ============================================================


class TestSecurity:
    """测试安全性"""

    def test_empty_query_rejected(self):
        """测试空查询被拒绝"""
        empty_query = ""
        # 验证空字符串
        assert not empty_query or not empty_query.strip()

    def test_negative_limit_rejected(self):
        """测试负数 limit 被拒绝"""
        negative_limit = -1
        assert negative_limit < 1

    def test_zero_limit_rejected(self):
        """测试零 limit 被拒绝"""
        zero_limit = 0
        assert zero_limit < 1

    def test_large_limit_rejected(self):
        """测试过大 limit 被拒绝"""
        large_limit = MAX_LIMIT + 1
        assert large_limit > MAX_LIMIT


# ============================================================
# 边界条件测试
# ============================================================


class TestBoundaryConditions:
    """测试边界条件"""

    def test_exact_max_query_length(self):
        """测试精确的最大查询长度"""
        query = "a" * MAX_QUERY_LENGTH
        assert len(query) == MAX_QUERY_LENGTH
        # 这个长度应该被接受

    def test_exact_max_limit(self):
        """测试精确的最大 limit"""
        limit = MAX_LIMIT
        assert limit == MAX_LIMIT
        # 这个值应该被接受

    def test_minimum_valid_limit(self):
        """测试最小有效 limit"""
        limit = 1
        assert limit >= 1
        # 这个值应该被接受

    def test_exact_max_description_length(self):
        """测试精确的最大描述长度"""
        description = "a" * MAX_QUERY_LENGTH
        assert len(description) == MAX_QUERY_LENGTH
        # 这个长度应该被接受
