"""
搜索算法单元测试

测试 Regex 和 BM25 搜索算法的功能。

Copyright (c) 2026 Maric
License: MIT
"""

import pytest

from registrytools.registry.models import SearchMethod, ToolMetadata
from registrytools.search.base import SearchAlgorithm
from registrytools.search.bm25_search import BM25Search
from registrytools.search.regex_search import RegexSearch


class TestSearchAlgorithm:
    """SearchAlgorithm 基类测试"""

    def test_cannot_instantiate_abstract_class(self):
        """测试不能直接实例化抽象类"""
        with pytest.raises(TypeError):
            SearchAlgorithm()

    def test_abstract_methods(self):
        """测试抽象方法存在"""
        abstract_methods = SearchAlgorithm.__abstractmethods__
        assert "index" in abstract_methods
        assert "search" in abstract_methods


class TestRegexSearch:
    """RegexSearch 搜索算法测试"""

    @pytest.fixture
    def sample_tools(self):
        """创建示例工具列表"""
        return [
            ToolMetadata(
                name="github.create_pr",
                description="Create a pull request in GitHub",
                tags={"github", "git", "pr"},
            ),
            ToolMetadata(
                name="slack.send_message",
                description="Send message to Slack channel",
                tags={"slack", "message"},
            ),
            ToolMetadata(
                name="gitlab.merge_request",
                description="Create merge request in GitLab",
                tags={"gitlab", "mr"},
            ),
        ]

    def test_initialization(self):
        """测试初始化"""
        searcher = RegexSearch()
        assert searcher.method == SearchMethod.REGEX
        assert searcher.case_sensitive is False

    def test_case_sensitive_option(self):
        """测试大小写敏感选项"""
        searcher_sensitive = RegexSearch(case_sensitive=True)
        assert searcher_sensitive.case_sensitive is True

        searcher_insensitive = RegexSearch(case_sensitive=False)
        assert searcher_insensitive.case_sensitive is False

    def test_index_building(self, sample_tools):
        """测试索引建立"""
        searcher = RegexSearch()
        searcher.index(sample_tools)
        assert searcher.is_indexed()

    def test_exact_name_match(self, sample_tools):
        """测试精确名称匹配"""
        searcher = RegexSearch()
        results = searcher.search("github.create_pr", sample_tools, 5)

        assert len(results) >= 1
        assert results[0].tool_name == "github.create_pr"
        assert results[0].score == 1.0

    def test_partial_name_match(self, sample_tools):
        """测试部分名称匹配"""
        searcher = RegexSearch()
        results = searcher.search("github", sample_tools, 5)

        assert len(results) >= 1
        assert any("github" in r.tool_name for r in results)

    def test_description_match(self, sample_tools):
        """测试描述匹配"""
        searcher = RegexSearch()
        results = searcher.search("pull request", sample_tools, 5)

        assert len(results) >= 1
        assert any("pr" in r.tool_name or "merge" in r.tool_name for r in results)

    def test_tag_match(self, sample_tools):
        """测试标签匹配"""
        searcher = RegexSearch()
        results = searcher.search("slack", sample_tools, 5)

        assert len(results) >= 1
        assert any("slack" in r.tool_name for r in results)

    def test_case_insensitive_search(self, sample_tools):
        """测试大小写不敏感搜索"""
        searcher = RegexSearch(case_sensitive=False)
        results_lower = searcher.search("github", sample_tools, 5)
        results_upper = searcher.search("GITHUB", sample_tools, 5)

        assert len(results_lower) == len(results_upper)

    def test_limit_results(self, sample_tools):
        """测试结果数量限制"""
        searcher = RegexSearch()
        results = searcher.search("create", sample_tools, 2)

        assert len(results) <= 2

    def test_no_match(self, sample_tools):
        """测试无匹配结果"""
        searcher = RegexSearch()
        results = searcher.search("nonexistent_tool_xyz", sample_tools, 5)

        assert len(results) == 0

    def test_invalid_regex(self, sample_tools):
        """测试无效正则表达式"""
        searcher = RegexSearch()
        results = searcher.search("[invalid(", sample_tools, 5)

        assert len(results) == 0


class TestBM25Search:
    """BM25Search 搜索算法测试"""

    @pytest.fixture
    def sample_tools(self):
        """创建示例工具列表"""
        return [
            ToolMetadata(
                name="github.create_pr",
                description="Create a pull request in GitHub repository",
                tags={"github", "git", "pr", "code"},
            ),
            ToolMetadata(
                name="slack.send_message",
                description="Send message to Slack channel",
                tags={"slack", "message", "chat"},
            ),
            ToolMetadata(
                name="gitlab.merge_request",
                description="Create merge request in GitLab",
                tags={"gitlab", "mr", "code"},
            ),
            ToolMetadata(
                name="aws.s3.upload",
                description="Upload file to AWS S3 bucket",
                tags={"aws", "s3", "storage", "cloud"},
            ),
        ]

    def test_initialization(self):
        """测试初始化"""
        searcher = BM25Search()
        assert searcher.method == SearchMethod.BM25
        assert searcher.k1 == 1.5
        assert searcher.b == 0.75

    def test_custom_parameters(self):
        """测试自定义参数"""
        searcher = BM25Search(k1=2.0, b=0.5)
        assert searcher.k1 == 2.0
        assert searcher.b == 0.5

    def test_index_building(self, sample_tools):
        """测试索引建立"""
        searcher = BM25Search()
        searcher.index(sample_tools)
        assert searcher.is_indexed()
        assert searcher.get_index_size() == len(sample_tools)

    def test_keyword_search(self, sample_tools):
        """测试关键词搜索"""
        searcher = BM25Search()
        results = searcher.search("github pull request", sample_tools, 5)

        assert len(results) >= 1
        assert results[0].tool_name == "github.create_pr"

    def test_reindex_on_tool_change(self, sample_tools):
        """测试工具变化时重新索引"""
        searcher = BM25Search()
        searcher.index(sample_tools)

        # 添加新工具
        new_tools = sample_tools + [
            ToolMetadata(
                name="jira.create_issue",
                description="Create issue in Jira",
                tags={"jira", "issue"},
            )
        ]

        results = searcher.search("jira issue", new_tools, 5)
        assert len(results) >= 1
        assert results[0].tool_name == "jira.create_issue"

    def test_chinese_tokenization(self):
        """测试中文分词"""
        # 使用多个工具以获得更好的 BM25 分数分布
        tools = [
            ToolMetadata(
                name="weather.query",
                description="查询天气信息",
                tags={"天气", "查询"},
            ),
            ToolMetadata(
                name="stock.price",
                description="股票价格查询",
                tags={"股票", "价格"},
            ),
            ToolMetadata(
                name="news.read",
                description="新闻阅读",
                tags={"新闻", "阅读"},
            ),
        ]

        searcher = BM25Search()
        results = searcher.search("天气", tools, 5)

        # 应该找到天气相关的工具
        assert len(results) >= 1
        assert "weather.query" in [r.tool_name for r in results]

    def test_limit_results(self, sample_tools):
        """测试结果数量限制"""
        searcher = BM25Search()
        results = searcher.search("create", sample_tools, 2)

        assert len(results) <= 2

    def test_score_normalization(self, sample_tools):
        """测试分数归一化"""
        searcher = BM25Search()
        results = searcher.search("github pr code", sample_tools, 5)

        # 验证所有分数在 [0, 1] 范围内
        for result in results:
            assert 0.0 <= result.score <= 1.0

    def test_multiple_keywords(self, sample_tools):
        """测试多关键词搜索"""
        searcher = BM25Search()

        # 搜索包含多个关键词
        results = searcher.search("github code", sample_tools, 5)
        assert len(results) >= 1

        # 验证相关工具排名较高
        tool_names = [r.tool_name for r in results]
        assert "github.create_pr" in tool_names

    def test_relevance_ordering(self, sample_tools):
        """测试相关性排序"""
        searcher = BM25Search()
        results = searcher.search("pr", sample_tools, 5)

        # 验证分数是降序排列的
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)
