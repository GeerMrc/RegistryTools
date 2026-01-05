"""
工具注册表单元测试

测试 ToolRegistry 的所有功能。

Copyright (c) 2026 Maric
License: MIT
"""

import pytest

from registrytools.registry.models import SearchMethod, ToolMetadata
from registrytools.registry.registry import ToolRegistry
from registrytools.search.bm25_search import BM25Search
from registrytools.search.regex_search import RegexSearch


class TestToolRegistry:
    """ToolRegistry 核心功能测试"""

    @pytest.fixture
    def sample_tools(self):
        """创建示例工具列表"""
        return [
            ToolMetadata(
                name="github.create_pr",
                description="Create a pull request in GitHub repository",
                tags={"github", "git", "pr", "code"},
                category="github",
            ),
            ToolMetadata(
                name="slack.send_message",
                description="Send message to Slack channel",
                tags={"slack", "message", "chat"},
                category="communication",
            ),
            ToolMetadata(
                name="gitlab.merge_request",
                description="Create merge request in GitLab",
                tags={"gitlab", "mr", "code"},
                category="gitlab",
            ),
            ToolMetadata(
                name="aws.s3.upload",
                description="Upload file to AWS S3 bucket",
                tags={"aws", "s3", "storage", "cloud"},
                category="aws",
            ),
        ]

    @pytest.fixture
    def registry(self, sample_tools):
        """创建预填充的注册表"""
        reg = ToolRegistry()
        for tool in sample_tools:
            reg.register(tool)
        return reg

    # ============================================================
    # 初始化测试
    # ============================================================

    def test_initialization(self):
        """测试初始化"""
        registry = ToolRegistry()
        assert registry.is_empty()
        assert registry.tool_count == 0
        assert registry.category_count == 0

    # ============================================================
    # 工具注册功能测试 (TASK-302)
    # ============================================================

    def test_register_single_tool(self):
        """测试注册单个工具"""
        registry = ToolRegistry()
        tool = ToolMetadata(
            name="test.tool",
            description="Test tool",
            tags={"test"},
        )
        registry.register(tool)

        assert registry.tool_count == 1
        assert not registry.is_empty()
        assert registry.get_tool("test.tool") is not None
        assert registry.get_tool("test.tool").name == "test.tool"

    def test_register_many_tools(self):
        """测试批量注册工具"""
        registry = ToolRegistry()
        tools = [
            ToolMetadata(name=f"tool{i}", description=f"Tool {i}", tags={"test"}) for i in range(5)
        ]
        registry.register_many(tools)

        assert registry.tool_count == 5

    def test_register_updates_existing_tool(self):
        """测试更新已存在的工具"""
        registry = ToolRegistry()
        tool1 = ToolMetadata(
            name="test.tool",
            description="Original description",
            tags={"old"},
        )
        tool2 = ToolMetadata(
            name="test.tool",
            description="Updated description",
            tags={"new"},
        )

        registry.register(tool1)
        assert registry.get_tool("test.tool").description == "Original description"

        registry.register(tool2)
        assert registry.get_tool("test.tool").description == "Updated description"
        assert registry.tool_count == 1  # 不增加数量

    def test_unregister_tool(self):
        """测试注销工具"""
        registry = ToolRegistry()
        tool = ToolMetadata(name="test.tool", description="Test", tags={"test"})
        registry.register(tool)

        assert registry.tool_count == 1
        assert registry.unregister("test.tool") is True
        assert registry.tool_count == 0
        assert registry.get_tool("test.tool") is None

    def test_unregister_nonexistent_tool(self):
        """测试注销不存在的工具"""
        registry = ToolRegistry()
        assert registry.unregister("nonexistent") is False

    # ============================================================
    # 工具查询功能测试
    # ============================================================

    def test_get_tool(self, registry):
        """测试获取工具"""
        tool = registry.get_tool("github.create_pr")
        assert tool is not None
        assert tool.name == "github.create_pr"
        assert tool.category == "github"

    def test_get_nonexistent_tool(self, registry):
        """测试获取不存在的工具"""
        tool = registry.get_tool("nonexistent")
        assert tool is None

    def test_list_all_tools(self, registry):
        """测试列出所有工具"""
        tools = registry.list_tools()
        assert len(tools) == 4

    def test_list_tools_by_category(self, registry):
        """测试按类别列出工具"""
        github_tools = registry.list_tools(category="github")
        assert len(github_tools) == 1
        assert github_tools[0].name == "github.create_pr"

    def test_list_categories(self, registry):
        """测试列出所有类别"""
        categories = registry.list_categories()
        assert len(categories) == 4
        assert "github" in categories
        assert "communication" in categories
        assert "gitlab" in categories
        assert "aws" in categories

    # ============================================================
    # 搜索器注册测试
    # ============================================================

    def test_register_searcher(self):
        """测试注册搜索器"""
        registry = ToolRegistry()
        regex_searcher = RegexSearch()
        registry.register_searcher(SearchMethod.REGEX, regex_searcher)

        assert registry.get_searcher(SearchMethod.REGEX) is regex_searcher

    def test_register_searcher_type_mismatch(self):
        """测试搜索器类型不匹配"""
        registry = ToolRegistry()
        regex_searcher = RegexSearch()

        with pytest.raises(ValueError, match="搜索器类型不匹配"):
            registry.register_searcher(SearchMethod.BM25, regex_searcher)

    # ============================================================
    # 工具搜索功能测试 (TASK-303)
    # ============================================================

    def test_search_without_registered_searcher(self, registry):
        """测试未注册搜索器时搜索"""
        with pytest.raises(ValueError, match="搜索方法.*未注册"):
            registry.search("github")

    def test_search_with_regex(self, registry):
        """测试使用正则搜索"""
        registry.register_searcher(SearchMethod.REGEX, RegexSearch())
        results = registry.search("github", method=SearchMethod.REGEX)

        assert len(results) >= 1
        assert any("github" in r.tool_name for r in results)

    def test_search_with_bm25(self, registry):
        """测试使用 BM25 搜索"""
        registry.register_searcher(SearchMethod.BM25, BM25Search())
        results = registry.search("github pull request", method=SearchMethod.BM25)

        assert len(results) >= 1
        assert "github.create_pr" in [r.tool_name for r in results]

    def test_search_empty_registry(self):
        """测试在空注册表中搜索"""
        registry = ToolRegistry()
        registry.register_searcher(SearchMethod.REGEX, RegexSearch())

        results = registry.search("test", method=SearchMethod.REGEX)
        assert len(results) == 0

    # ============================================================
    # 使用频率跟踪测试 (TASK-304)
    # ============================================================

    def test_update_usage(self):
        """测试更新使用频率"""
        registry = ToolRegistry()
        tool = ToolMetadata(name="test.tool", description="Test", tags={"test"})
        registry.register(tool)

        assert tool.use_frequency == 0

        registry.update_usage("test.tool")
        assert tool.use_frequency == 1

        registry.update_usage("test.tool")
        assert tool.use_frequency == 2

    def test_update_usage_updates_last_used(self):
        """测试更新最后使用时间"""
        registry = ToolRegistry()
        tool = ToolMetadata(name="test.tool", description="Test", tags={"test"})
        original_time = tool.last_used

        registry.register(tool)
        registry.update_usage("test.tool")

        assert tool.last_used is not None
        if original_time:
            assert tool.last_used >= original_time

    def test_update_usage_nonexistent_tool(self):
        """测试更新不存在的工具"""
        registry = ToolRegistry()
        assert registry.update_usage("nonexistent") is False

    def test_get_usage_stats(self, registry):
        """测试获取使用统计"""
        stats = registry.get_usage_stats()
        assert len(stats) == 4
        for _tool_name, count in stats.items():
            assert count == 0  # 初始使用频率为 0

    def test_get_most_used(self):
        """测试获取最常用工具"""
        registry = ToolRegistry()
        tools = [
            ToolMetadata(name="tool1", description="Tool 1", tags={"test"}),
            ToolMetadata(name="tool2", description="Tool 2", tags={"test"}),
            ToolMetadata(name="tool3", description="Tool 3", tags={"test"}),
        ]
        registry.register_many(tools)

        # 更新使用频率
        registry.update_usage("tool1")
        registry.update_usage("tool1")
        registry.update_usage("tool2")

        most_used = registry.get_most_used(limit=2)

        assert len(most_used) == 2
        assert most_used[0].name == "tool1"
        assert most_used[1].name == "tool2"

    # ============================================================
    # 索引管理测试
    # ============================================================

    def test_rebuild_indexes(self, registry):
        """测试重建索引"""
        registry.register_searcher(SearchMethod.BM25, BM25Search())

        # 重建索引
        registry.rebuild_indexes()

        searcher = registry.get_searcher(SearchMethod.BM25)
        assert searcher is not None
        assert searcher.is_indexed()

    # ============================================================
    # 清空测试
    # ============================================================

    def test_clear(self, registry):
        """测试清空注册表"""
        assert registry.tool_count == 4
        assert not registry.is_empty()

        registry.clear()

        assert registry.tool_count == 0
        assert registry.is_empty()
        assert registry.category_count == 0
