"""
数据模型单元测试

测试 ToolMetadata、ToolSearchResult 和 SearchMethod 的功能。

Copyright (c) 2026 Maric
License: MIT
"""

from datetime import datetime

import pytest

from RegistryTools.registry.models import (
    SearchMethod,
    ToolMetadata,
    ToolSearchResult,
)


class TestSearchMethod:
    """SearchMethod 枚举测试"""

    def test_search_method_values(self):
        """测试搜索方法枚举值"""
        assert SearchMethod.REGEX.value == "regex"
        assert SearchMethod.BM25.value == "bm25"
        assert SearchMethod.EMBEDDING.value == "embedding"

    def test_search_method_count(self):
        """测试搜索方法数量"""
        assert len(SearchMethod) == 3

    def test_search_method_iteration(self):
        """测试搜索方法可迭代"""
        methods = list(SearchMethod)
        assert SearchMethod.REGEX in methods
        assert SearchMethod.BM25 in methods
        assert SearchMethod.EMBEDDING in methods


class TestToolMetadata:
    """ToolMetadata 数据模型测试"""

    def test_minimal_creation(self):
        """测试最小化创建"""
        tool = ToolMetadata(name="test.tool", description="Test tool")
        assert tool.name == "test.tool"
        assert tool.description == "Test tool"
        assert tool.defer_loading is True  # 默认值
        assert tool.tags == set()
        assert tool.use_frequency == 0

    def test_full_creation(self):
        """测试完整参数创建"""
        now = datetime.now()
        tool = ToolMetadata(
            name="github.create_pr",
            description="Create a pull request",
            mcp_server="github",
            defer_loading=False,
            tags={"github", "git", "pr"},
            category="github",
            use_frequency=5,
            last_used=now,
            input_schema={"type": "object"},
            output_schema={"type": "object"},
        )
        assert tool.name == "github.create_pr"
        assert tool.mcp_server == "github"
        assert tool.defer_loading is False
        assert tool.tags == {"github", "git", "pr"}
        assert tool.category == "github"
        assert tool.use_frequency == 5
        assert tool.last_used == now

    def test_tags_set_conversion(self):
        """测试标签集合转换"""
        tool = ToolMetadata(
            name="test.tool",
            description="Test tool",
            tags=["tag1", "tag2", "tag3"],
        )
        assert isinstance(tool.tags, set)
        assert tool.tags == {"tag1", "tag2", "tag3"}

    def test_score_validation(self):
        """测试分数验证（在 ToolSearchResult 中）"""
        # 有效分数
        result = ToolSearchResult(
            tool_name="test",
            description="test",
            score=0.5,
            match_reason="test",
        )
        assert result.score == 0.5

        # 边界值
        ToolSearchResult(tool_name="test", description="test", score=0.0, match_reason="test")
        ToolSearchResult(tool_name="test", description="test", score=1.0, match_reason="test")

        # 无效分数
        with pytest.raises(ValueError):
            ToolSearchResult(tool_name="test", description="test", score=1.5, match_reason="test")

        with pytest.raises(ValueError):
            ToolSearchResult(tool_name="test", description="test", score=-0.1, match_reason="test")

    def test_serialization(self):
        """测试 JSON 序列化"""
        tool = ToolMetadata(
            name="test.tool",
            description="Test tool",
            tags={"tag1", "tag2"},
            last_used=datetime(2026, 1, 4, 12, 0, 0),
        )
        data = tool.model_dump()
        assert data["name"] == "test.tool"
        assert isinstance(data["tags"], list)
        assert set(data["tags"]) == {"tag1", "tag2"}

    def test_json_schema(self):
        """测试 JSON Schema 生成"""
        schema = ToolMetadata.model_json_schema()
        assert "properties" in schema
        assert "name" in schema["properties"]
        assert "description" in schema["properties"]
        assert "tags" in schema["properties"]


class TestToolSearchResult:
    """ToolSearchResult 数据模型测试"""

    def test_creation(self):
        """测试创建"""
        result = ToolSearchResult(
            tool_name="github.create_pr",
            description="Create a pull request",
            score=0.85,
            match_reason="bm25_similarity",
        )
        assert result.tool_name == "github.create_pr"
        assert result.score == 0.85
        assert result.match_reason == "bm25_similarity"

    def test_score_range_validation(self):
        """测试分数范围验证"""
        # 有效范围
        ToolSearchResult(tool_name="test", description="test", score=0.0, match_reason="test")
        ToolSearchResult(tool_name="test", description="test", score=0.5, match_reason="test")
        ToolSearchResult(tool_name="test", description="test", score=1.0, match_reason="test")

        # 超出范围
        with pytest.raises(ValueError):
            ToolSearchResult(tool_name="test", description="test", score=-0.01, match_reason="test")

        with pytest.raises(ValueError):
            ToolSearchResult(tool_name="test", description="test", score=1.01, match_reason="test")

    def test_serialization(self):
        """测试序列化"""
        result = ToolSearchResult(
            tool_name="test.tool",
            description="Test tool",
            score=0.75,
            match_reason="regex_match",
        )
        data = result.model_dump()
        assert data["tool_name"] == "test.tool"
        assert data["score"] == 0.75
