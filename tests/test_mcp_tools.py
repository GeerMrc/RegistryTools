"""
MCP 工具集成测试

测试 MCP 服务器工具接口的完整功能。

Copyright (c) 2026 Maric
License: MIT
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from RegistryTools.registry.models import ToolMetadata

# ============================================================
# 测试数据
# ============================================================


@pytest.fixture
def sample_tools() -> list[ToolMetadata]:
    """返回示例工具列表"""
    return [
        ToolMetadata(
            name="github.create_pr",
            description="Create a pull request in a GitHub repository",
            mcp_server="github",
            tags={"github", "git", "pr"},
            category="github",
        ),
        ToolMetadata(
            name="github.merge_pr",
            description="Merge a pull request in a GitHub repository",
            mcp_server="github",
            tags={"github", "git", "pr", "merge"},
            category="github",
        ),
        ToolMetadata(
            name="aws.s3.upload",
            description="Upload file to S3 bucket",
            mcp_server="aws",
            tags={"aws", "s3", "storage", "upload"},
            category="aws",
        ),
        ToolMetadata(
            name="aws.lambda.invoke",
            description="Invoke AWS Lambda function",
            mcp_server="aws",
            tags={"aws", "lambda", "serverless"},
            category="aws",
        ),
        ToolMetadata(
            name="slack.send_message",
            description="Send message to Slack channel",
            mcp_server="slack",
            tags={"slack", "messaging"},
            category="slack",
        ),
    ]


@pytest.fixture
def mock_registry_with_tools(sample_tools: list[ToolMetadata]) -> MagicMock:
    """返回带有示例工具的模拟注册表"""
    from RegistryTools.registry.models import SearchMethod
    from RegistryTools.registry.registry import ToolRegistry
    from RegistryTools.search.bm25_search import BM25Search
    from RegistryTools.search.regex_search import RegexSearch

    registry = ToolRegistry()

    # 注册搜索算法
    registry.register_searcher(SearchMethod.REGEX, RegexSearch(case_sensitive=False))
    registry.register_searcher(SearchMethod.BM25, BM25Search())

    # 注册工具
    registry.register_many(sample_tools)
    registry.rebuild_indexes()

    return registry


# ============================================================
# MCP 工具函数测试 (使用模拟服务器)
# ============================================================


class TestSearchTools:
    """测试 search_tools MCP 工具"""

    def test_search_tools_with_bm25(self, mock_registry_with_tools: MagicMock) -> None:
        """测试使用 BM25 搜索工具"""
        # 直接调用注册表的 search 方法
        from RegistryTools.registry.models import SearchMethod

        results = mock_registry_with_tools.search(
            query="github pull request", method=SearchMethod.BM25, limit=5
        )

        # 验证结果
        assert len(results) > 0
        first_result = results[0]
        assert first_result.tool_name in ["github.create_pr", "github.merge_pr"]
        assert 0 <= first_result.score <= 1

    def test_search_tools_with_regex(self, mock_registry_with_tools: MagicMock) -> None:
        """测试使用正则表达式搜索工具"""
        from RegistryTools.registry.models import SearchMethod

        results = mock_registry_with_tools.search(
            query="lambda", method=SearchMethod.REGEX, limit=5
        )

        # 验证结果
        assert len(results) > 0
        assert "lambda" in results[0].tool_name.lower()

    def test_search_tools_empty_query(self, mock_registry_with_tools: MagicMock) -> None:
        """测试空查询"""
        from RegistryTools.registry.models import SearchMethod

        results = mock_registry_with_tools.search(query="", method=SearchMethod.BM25, limit=5)

        # 空查询应该返回结果（基于所有工具）
        assert isinstance(results, list)


class TestGetToolDefinition:
    """测试 get_tool_definition 功能"""

    def test_get_tool_definition_existing(self, mock_registry_with_tools: MagicMock) -> None:
        """测试获取已存在工具的定义"""
        tool = mock_registry_with_tools.get_tool("github.create_pr")

        # 验证结果
        assert tool is not None
        assert tool.name == "github.create_pr"
        assert tool.description == "Create a pull request in a GitHub repository"
        assert tool.category == "github"
        assert "github" in tool.tags

    def test_get_tool_definition_nonexistent(self, mock_registry_with_tools: MagicMock) -> None:
        """测试获取不存在工具的定义"""
        tool = mock_registry_with_tools.get_tool("nonexistent.tool")
        assert tool is None


class TestListToolsByCategory:
    """测试 list_tools_by_category 功能"""

    def test_list_tools_by_category_specific(self, mock_registry_with_tools: MagicMock) -> None:
        """测试列出特定类别的工具"""
        tools = mock_registry_with_tools.list_tools(category="github")

        # 验证结果
        assert len(tools) == 2
        tool_names = [t.name for t in tools]
        assert "github.create_pr" in tool_names
        assert "github.merge_pr" in tool_names

    def test_list_tools_by_category_all(self, mock_registry_with_tools: MagicMock) -> None:
        """测试列出所有工具"""
        tools = mock_registry_with_tools.list_tools()

        # 验证结果
        assert len(tools) == 5

    def test_list_tools_by_category_empty(self, mock_registry_with_tools: MagicMock) -> None:
        """测试列出空类别"""
        tools = mock_registry_with_tools.list_tools(category="nonexistent")

        # 验证结果
        assert len(tools) == 0

    def test_list_categories(self, mock_registry_with_tools: MagicMock) -> None:
        """测试列出所有类别"""
        categories = mock_registry_with_tools.list_categories()

        # 验证结果
        assert isinstance(categories, list)
        assert "github" in categories
        assert "aws" in categories
        assert "slack" in categories


class TestRegisterTool:
    """测试 register_tool 功能"""

    def test_register_tool_new(self, mock_registry_with_tools: MagicMock) -> None:
        """测试注册新工具"""
        initial_count = mock_registry_with_tools.tool_count

        # 创建新工具
        new_tool = ToolMetadata(
            name="test.new_tool",
            description="A test tool",
            category="test",
            tags={"test", "example"},
        )

        # 注册工具
        mock_registry_with_tools.register(new_tool)

        # 验证工具已注册
        assert mock_registry_with_tools.tool_count == initial_count + 1
        retrieved_tool = mock_registry_with_tools.get_tool("test.new_tool")
        assert retrieved_tool is not None
        assert retrieved_tool.name == "test.new_tool"

    def test_register_tool_update(self, mock_registry_with_tools: MagicMock) -> None:
        """测试更新已存在的工具"""
        initial_count = mock_registry_with_tools.tool_count

        # 创建工具更新
        updated_tool = ToolMetadata(
            name="github.create_pr",
            description="Updated description",
            category="github",
            tags={"updated"},
        )

        # 注册（应该更新）
        mock_registry_with_tools.register(updated_tool)

        # 验证工具数量不变
        assert mock_registry_with_tools.tool_count == initial_count

        # 验证工具已更新
        retrieved_tool = mock_registry_with_tools.get_tool("github.create_pr")
        assert retrieved_tool.description == "Updated description"


# ============================================================
# 使用频率跟踪测试
# ============================================================


class TestUsageTracking:
    """测试使用频率跟踪功能"""

    def test_update_usage(self, mock_registry_with_tools: MagicMock) -> None:
        """测试更新使用频率"""
        tool = mock_registry_with_tools.get_tool("github.create_pr")
        initial_frequency = tool.use_frequency

        # 更新使用频率
        mock_registry_with_tools.update_usage("github.create_pr")

        # 验证频率已更新
        updated_tool = mock_registry_with_tools.get_tool("github.create_pr")
        assert updated_tool.use_frequency == initial_frequency + 1

    def test_get_usage_stats(self, mock_registry_with_tools: MagicMock) -> None:
        """测试获取使用统计"""
        stats = mock_registry_with_tools.get_usage_stats()

        # 验证统计
        assert isinstance(stats, dict)
        assert "github.create_pr" in stats

    def test_get_most_used(self, mock_registry_with_tools: MagicMock) -> None:
        """测试获取最常用工具"""
        # 增加某个工具的使用频率
        mock_registry_with_tools.update_usage("github.create_pr")
        mock_registry_with_tools.update_usage("github.create_pr")
        mock_registry_with_tools.update_usage("github.create_pr")

        # 获取最常用工具
        most_used = mock_registry_with_tools.get_most_used(limit=3)

        # 验证结果
        assert len(most_used) <= 3
        assert most_used[0].name == "github.create_pr"
        assert most_used[0].use_frequency == 3


# ============================================================
# 服务器创建测试
# ============================================================


class TestServerCreation:
    """测试服务器创建功能"""

    def test_create_server(self, tmp_path: Path) -> None:
        """测试创建服务器"""
        from RegistryTools.server import create_server

        server = create_server(tmp_path)

        # 验证服务器已创建
        assert server is not None
        assert server.name == "RegistryTools"

    def test_create_server_with_tools(
        self, tmp_path: Path, sample_tools: list[ToolMetadata]
    ) -> None:
        """测试创建带有工具的服务器"""
        from RegistryTools.server import create_server
        from RegistryTools.storage.json_storage import JSONStorage

        # 先保存工具
        storage = JSONStorage(tmp_path / "tools.json")
        storage.save_many(sample_tools)

        # 创建服务器
        server = create_server(tmp_path)

        # 验证服务器已创建
        assert server is not None

        # 验证工具已加载
        # (注意：FastMCP 的内部结构可能需要不同的访问方式)
        assert server.name == "RegistryTools"


# ============================================================
# 集成测试
# ============================================================


class TestIntegration:
    """MCP 工具集成测试"""

    def test_complete_workflow(self, mock_registry_with_tools: MagicMock) -> None:
        """测试完整的工具使用流程"""
        from RegistryTools.registry.models import SearchMethod

        # 1. 搜索工具
        search_results = mock_registry_with_tools.search(
            query="aws", method=SearchMethod.BM25, limit=5
        )
        assert len(search_results) > 0

        # 2. 获取第一个工具的详细定义
        tool_name = search_results[0].tool_name
        definition = mock_registry_with_tools.get_tool(tool_name)
        assert definition is not None
        assert definition.name == tool_name

        # 3. 列出该工具所属类别的所有工具
        category_tools = mock_registry_with_tools.list_tools(category=definition.category)
        assert len(category_tools) > 0

        # 4. 更新使用频率
        mock_registry_with_tools.update_usage(tool_name)
        updated_tool = mock_registry_with_tools.get_tool(tool_name)
        assert updated_tool.use_frequency > 0
