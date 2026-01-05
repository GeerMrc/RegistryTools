"""
FastMCP 集成测试

测试 MCP 工具和资源的完整流程，覆盖 server.py 中的核心逻辑。

目的：提升 server.py 测试覆盖率从 46% 到 80%+

策略：直接测试 MCP 工具函数，通过创建测试服务器并调用其内部方法

Copyright (c) 2026 Maric
License: MIT
"""

import json

import pytest
from fastmcp import FastMCP

from RegistryTools.registry.models import SearchMethod, ToolMetadata
from RegistryTools.registry.registry import ToolRegistry
from RegistryTools.search.bm25_search import BM25Search
from RegistryTools.search.regex_search import RegexSearch
from RegistryTools.server import create_server, create_server_with_sqlite
from RegistryTools.storage.json_storage import JSONStorage

# ============================================================
# 测试 fixtures
# ============================================================


@pytest.fixture
def temp_data_dir(tmp_path):
    """创建临时数据目录"""
    return tmp_path / "test_data"


@pytest.fixture
def sample_registry():
    """创建包含示例工具的注册表"""
    registry = ToolRegistry()

    # 注册搜索算法
    registry.register_searcher(SearchMethod.REGEX, RegexSearch(case_sensitive=False))
    registry.register_searcher(SearchMethod.BM25, BM25Search())

    # 添加示例工具
    tools = [
        ToolMetadata(
            name="test_tool_1",
            description="测试工具1",
            category="testing",
            tags={"test", "example"},
        ),
        ToolMetadata(
            name="search_tool",
            description="搜索工具",
            category="utility",
            tags={"search", "find"},
        ),
        ToolMetadata(
            name="data_tool",
            description="数据处理工具",
            category="data",
            tags={"process", "transform"},
            use_frequency=15,  # 高频工具
        ),
    ]

    for tool in tools:
        registry.register(tool)

    registry.rebuild_indexes()
    return registry


@pytest.fixture
def test_server_with_tools(temp_data_dir, sample_registry):
    """创建包含工具的测试服务器"""
    # 先保存工具到存储（直接获取工具列表）
    tools = [sample_registry.get_tool(name) for name in ["test_tool_1", "search_tool", "data_tool"]]
    storage = JSONStorage(temp_data_dir / "tools.json")
    storage.save_many(tools)

    # 创建服务器
    mcp = create_server(temp_data_dir)
    return mcp


# ============================================================
# 直接测试 MCP 工具函数（通过内部调用）
# ============================================================


class TestSearchToolsFunction:
    """直接测试 search_tools 工具函数"""

    def test_search_tools_bm25_success(self, test_server_with_tools):
        """测试 BM25 搜索成功"""
        # 获取工具函数
        search_tools = None
        for tool in test_server_with_tools._tool_manager._tools.values():
            if tool.name == "search_tools":
                search_tools = tool
                break

        assert search_tools is not None

        # 调用函数
        result = search_tools.fn(query="搜索", search_method="bm25", limit=5)

        # 解析结果
        data = json.loads(result)

        # 验证
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["tool_name"] == "search_tool"
        assert data[0]["description"] == "搜索工具"
        assert "score" in data[0]
        assert "match_reason" in data[0]

    def test_search_tools_regex_success(self, test_server_with_tools):
        """测试 Regex 搜索成功"""
        search_tools = None
        for tool in test_server_with_tools._tool_manager._tools.values():
            if tool.name == "search_tools":
                search_tools = tool
                break

        assert search_tools is not None

        # 调用函数
        result = search_tools.fn(query="test", search_method="regex", limit=10)

        # 解析结果
        data = json.loads(result)

        # 验证
        assert isinstance(data, list)
        assert len(data) >= 1
        tool_names = [item["tool_name"] for item in data]
        assert "test_tool_1" in tool_names

    def test_search_tools_invalid_method(self, test_server_with_tools):
        """测试无效的搜索方法抛出 ValueError"""
        search_tools = None
        for tool in test_server_with_tools._tool_manager._tools.values():
            if tool.name == "search_tools":
                search_tools = tool
                break

        assert search_tools is not None

        # 调用函数并验证异常
        with pytest.raises(ValueError) as exc_info:
            search_tools.fn(query="test", search_method="invalid")

        # 验证错误消息
        assert "无效的搜索方法" in str(exc_info.value)

    def test_search_tools_empty_query(self, test_server_with_tools):
        """测试空查询字符串"""
        search_tools = None
        for tool in test_server_with_tools._tool_manager._tools.values():
            if tool.name == "search_tools":
                search_tools = tool
                break

        result = search_tools.fn(query="", search_method="bm25", limit=5)
        data = json.loads(result)
        assert isinstance(data, list)

    def test_search_tools_limit_parameter(self, test_server_with_tools):
        """测试 limit 参数生效"""
        search_tools = None
        for tool in test_server_with_tools._tool_manager._tools.values():
            if tool.name == "search_tools":
                search_tools = tool
                break

        result = search_tools.fn(query="工具", search_method="bm25", limit=2)
        data = json.loads(result)
        assert len(data) <= 2


class TestGetToolDefinitionFunction:
    """直接测试 get_tool_definition 工具函数"""

    def test_get_tool_definition_success(self, test_server_with_tools):
        """测试获取工具定义成功"""
        get_tool_definition = None
        for tool in test_server_with_tools._tool_manager._tools.values():
            if tool.name == "get_tool_definition":
                get_tool_definition = tool
                break

        assert get_tool_definition is not None

        # 调用函数
        result = get_tool_definition.fn(tool_name="search_tool")

        # 解析结果
        data = json.loads(result)

        # 验证
        assert data["name"] == "search_tool"
        assert data["description"] == "搜索工具"
        assert data["category"] == "utility"
        assert "test" in data["tags"] or "search" in data["tags"]

    def test_get_tool_definition_not_found(self, test_server_with_tools):
        """测试获取不存在的工具抛出 ValueError"""
        get_tool_definition = None
        for tool in test_server_with_tools._tool_manager._tools.values():
            if tool.name == "get_tool_definition":
                get_tool_definition = tool
                break

        assert get_tool_definition is not None

        # 验证异常
        with pytest.raises(ValueError) as exc_info:
            get_tool_definition.fn(tool_name="nonexistent_tool")

        assert "工具不存在" in str(exc_info.value)

    def test_get_tool_definition_with_all_fields(self, test_server_with_tools):
        """测试获取包含所有字段的工具定义"""
        get_tool_definition = None
        for tool in test_server_with_tools._tool_manager._tools.values():
            if tool.name == "get_tool_definition":
                get_tool_definition = tool
                break

        result = get_tool_definition.fn(tool_name="data_tool")
        data = json.loads(result)

        # 验证所有字段存在
        assert "name" in data
        assert "description" in data
        assert "category" in data
        assert "tags" in data
        assert "use_frequency" in data
        assert data["use_frequency"] == 15


class TestListToolsByCategoryFunction:
    """直接测试 list_tools_by_category 工具函数"""

    def test_list_tools_by_specific_category(self, test_server_with_tools):
        """测试列出特定类别的工具"""
        list_tools = None
        for tool in test_server_with_tools._tool_manager._tools.values():
            if tool.name == "list_tools_by_category":
                list_tools = tool
                break

        assert list_tools is not None

        # 调用函数
        result = list_tools.fn(category="testing", limit=20)

        # 解析结果
        data = json.loads(result)

        # 验证
        assert data["category"] == "testing"
        assert data["count"] >= 1
        assert isinstance(data["tools"], list)
        assert data["tools"][0]["name"] == "test_tool_1"

    def test_list_tools_by_all_categories(self, test_server_with_tools):
        """测试列出所有类别"""
        list_tools = None
        for tool in test_server_with_tools._tool_manager._tools.values():
            if tool.name == "list_tools_by_category":
                list_tools = tool
                break

        assert list_tools is not None

        # 调用函数
        result = list_tools.fn(category="all", limit=20)

        # 解析结果
        data = json.loads(result)

        # 验证
        assert "categories" in data
        assert isinstance(data["categories"], list)
        assert "testing" in data["categories"]
        assert "utility" in data["categories"]
        assert "data" in data["categories"]

    def test_list_tools_by_category_limit(self, test_server_with_tools):
        """测试 limit 参数生效"""
        list_tools = None
        for tool in test_server_with_tools._tool_manager._tools.values():
            if tool.name == "list_tools_by_category":
                list_tools = tool
                break

        result = list_tools.fn(category="utility", limit=1)
        data = json.loads(result)

        # 验证 limit 生效
        assert data["count"] <= 1

    def test_list_tools_by_empty_category(self, test_server_with_tools):
        """测试列出空类别"""
        list_tools = None
        for tool in test_server_with_tools._tool_manager._tools.values():
            if tool.name == "list_tools_by_category":
                list_tools = tool
                break

        result = list_tools.fn(category="empty", limit=20)
        data = json.loads(result)

        # 验证空类别
        assert data["category"] == "empty"
        assert data["count"] == 0
        assert data["tools"] == []


class TestRegisterToolFunction:
    """直接测试 register_tool 工具函数"""

    def test_register_tool_success(self, test_server_with_tools, temp_data_dir):
        """测试注册新工具成功"""
        register_tool = None
        for tool in test_server_with_tools._tool_manager._tools.values():
            if tool.name == "register_tool":
                register_tool = tool
                break

        assert register_tool is not None

        # 调用函数
        result = register_tool.fn(
            name="new_tool",
            description="新注册的工具",
            category="new_category",
            tags=["new", "test"],
        )

        # 解析结果
        data = json.loads(result)

        # 验证返回结果
        assert data["success"] is True
        assert "工具已注册: new_tool" in data["message"]
        assert data["tool"]["name"] == "new_tool"
        assert data["tool"]["description"] == "新注册的工具"

    def test_register_tool_already_exists(self, test_server_with_tools):
        """测试注册已存在的工具抛出 ValueError"""
        register_tool = None
        for tool in test_server_with_tools._tool_manager._tools.values():
            if tool.name == "register_tool":
                register_tool = tool
                break

        assert register_tool is not None

        # 验证异常
        with pytest.raises(ValueError) as exc_info:
            register_tool.fn(
                name="test_tool_1",  # 已存在
                description="重复工具",
            )

        assert "工具已存在" in str(exc_info.value)

    def test_register_tool_minimal_parameters(self, test_server_with_tools):
        """测试仅使用必需参数注册工具"""
        register_tool = None
        for tool in test_server_with_tools._tool_manager._tools.values():
            if tool.name == "register_tool":
                register_tool = tool
                break

        result = register_tool.fn(
            name="minimal_tool",
            description="最小参数工具",
        )

        data = json.loads(result)

        # 验证
        assert data["success"] is True
        assert data["tool"]["name"] == "minimal_tool"

    def test_register_tool_with_empty_tags(self, test_server_with_tools):
        """测试使用空标签列表注册工具"""
        register_tool = None
        for tool in test_server_with_tools._tool_manager._tools.values():
            if tool.name == "register_tool":
                register_tool = tool
                break

        result = register_tool.fn(
            name="no_tags_tool",
            description="无标签工具",
            tags=[],
        )

        data = json.loads(result)

        # 验证
        assert data["success"] is True
        assert data["tool"]["tags"] == []


class TestStatsResource:
    """测试 registry://stats 资源"""

    def test_get_stats(self, test_server_with_tools):
        """测试获取统计信息"""
        # 直接从 _resources 字典获取资源
        get_stats = test_server_with_tools._resource_manager._resources.get("registry://stats")

        assert get_stats is not None

        # 调用资源函数
        result = get_stats.fn()

        # 解析结果
        data = json.loads(result)

        # 验证统计信息
        assert "total_tools" in data
        assert data["total_tools"] > 0
        assert "total_categories" in data
        assert "categories" in data
        assert isinstance(data["categories"], list)
        assert "most_used" in data
        assert isinstance(data["most_used"], list)

    def test_get_stats_includes_most_used(self, test_server_with_tools):
        """测试统计信息包含最常用工具"""
        get_stats = test_server_with_tools._resource_manager._resources.get("registry://stats")

        result = get_stats.fn()
        data = json.loads(result)

        # 验证最常用工具（data_tool 有 use_frequency=15）
        most_used = data["most_used"]
        assert len(most_used) > 0


class TestCategoriesResource:
    """测试 registry://categories 资源"""

    def test_get_categories(self, test_server_with_tools):
        """测试获取类别列表"""
        get_categories = test_server_with_tools._resource_manager._resources.get(
            "registry://categories"
        )

        assert get_categories is not None

        # 调用资源函数
        result = get_categories.fn()

        # 解析结果
        data = json.loads(result)

        # 验证
        assert "count" in data
        assert "categories" in data
        assert isinstance(data["categories"], list)
        assert data["count"] == len(data["categories"])

    def test_get_categories_content(self, test_server_with_tools):
        """测试类别列表内容正确"""
        get_categories = test_server_with_tools._resource_manager._resources.get(
            "registry://categories"
        )

        result = get_categories.fn()
        data = json.loads(result)

        # 验证预期的类别存在
        assert "testing" in data["categories"]
        assert "utility" in data["categories"]
        assert "data" in data["categories"]


class TestCreateServerWithSQLite:
    """测试 create_server_with_sqlite 函数"""

    def test_create_server_with_sqlite_basic(self, temp_data_dir):
        """测试创建 SQLite 服务器基本功能"""
        # 创建服务器
        mcp = create_server_with_sqlite(temp_data_dir)

        # 验证服务器创建成功
        assert isinstance(mcp, FastMCP)
        assert mcp.name == "RegistryTools"

    def test_create_server_with_sqlite_tools_loaded(self, temp_data_dir):
        """测试 SQLite 服务器加载默认工具"""
        # 创建服务器
        mcp = create_server_with_sqlite(temp_data_dir)

        # 验证工具已加载
        assert mcp is not None
        assert len(mcp._tool_manager._tools) > 0

    def test_create_server_with_sqlite_persistence(self, temp_data_dir):
        """测试 SQLite 存储持久化"""
        # 创建服务器
        create_server_with_sqlite(temp_data_dir)

        # 验证数据库文件创建
        db_path = temp_data_dir / "tools.db"
        assert db_path.exists()

    def test_create_server_with_sqlite_registers_searchers(self, temp_data_dir):
        """测试 SQLite 服务器注册搜索算法"""
        mcp = create_server_with_sqlite(temp_data_dir)

        # 验证服务器创建成功
        assert mcp is not None
        # 工具应该已注册
        assert len(mcp._tool_manager._tools) > 0


class TestCompleteWorkflow:
    """测试完整的 MCP 工具使用工作流"""

    def test_search_and_get_definition_workflow(self, test_server_with_tools):
        """测试搜索 → 获取定义的工作流"""
        # 获取工具函数
        search_tools = None
        get_tool_definition = None
        for tool in test_server_with_tools._tool_manager._tools.values():
            if tool.name == "search_tools":
                search_tools = tool
            elif tool.name == "get_tool_definition":
                get_tool_definition = tool

        # 步骤 1: 搜索工具
        search_result = search_tools.fn(query="数据", search_method="bm25")
        search_data = json.loads(search_result)

        # 验证搜索结果
        assert len(search_data) > 0
        tool_name = search_data[0]["tool_name"]

        # 步骤 2: 获取工具定义
        def_result = get_tool_definition.fn(tool_name=tool_name)
        def_data = json.loads(def_result)

        # 验证定义
        assert def_data["name"] == tool_name
        assert "description" in def_data

    def test_register_and_search_workflow(self, test_server_with_tools):
        """测试注册 → 搜索的工作流"""
        # 获取工具函数
        register_tool = None
        search_tools = None
        for tool in test_server_with_tools._tool_manager._tools.values():
            if tool.name == "register_tool":
                register_tool = tool
            elif tool.name == "search_tools":
                search_tools = tool

        # 步骤 1: 注册新工具
        register_tool.fn(
            name="workflow_test_tool",
            description="工作流测试工具",
            category="workflow",
            tags=["test"],
        )

        # 步骤 2: 搜索新注册的工具
        search_result = search_tools.fn(query="工作流", search_method="bm25")
        search_data = json.loads(search_result)

        # 验证能找到新工具
        tool_names = [item["tool_name"] for item in search_data]
        assert "workflow_test_tool" in tool_names

    def test_list_and_stats_workflow(self, test_server_with_tools):
        """测试列出工具 → 统计信息工作流"""
        # 获取工具和资源函数
        list_tools = None
        for tool in test_server_with_tools._tool_manager._tools.values():
            if tool.name == "list_tools_by_category":
                list_tools = tool

        get_stats = test_server_with_tools._resource_manager._resources.get("registry://stats")

        # 步骤 1: 列出所有类别
        list_result = list_tools.fn(category="all")
        list_data = json.loads(list_result)
        categories = list_data["categories"]

        # 步骤 2: 获取统计信息
        stats_result = get_stats.fn()
        stats_data = json.loads(stats_result)

        # 验证类别数量一致
        assert len(categories) == stats_data["total_categories"]
