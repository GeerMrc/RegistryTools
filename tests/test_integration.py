"""
集成测试 - 端到端工作流测试

测试 RegistryTools 的完整使用场景和工作流。

Copyright (c) 2026 Maric
License: MIT
"""

import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from RegistryTools.registry.models import SearchMethod, ToolMetadata
from RegistryTools.registry.registry import ToolRegistry
from RegistryTools.search.bm25_search import BM25Search
from RegistryTools.search.regex_search import RegexSearch
from RegistryTools.storage.json_storage import JSONStorage
from RegistryTools.storage.sqlite_storage import SQLiteStorage

# ============================================================
# 测试标记
# ============================================================

pytestmark = pytest.mark.integration


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def temp_data_path(tmp_path: Path) -> Path:
    """创建临时数据目录"""
    data_dir = tmp_path / "registry_data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


@pytest.fixture
def sample_tools() -> list[ToolMetadata]:
    """创建示例工具列表"""
    return [
        ToolMetadata(
            name="github.create_pull_request",
            description="Create a new pull request in a GitHub repository",
            mcp_server="github",
            tags={"github", "git", "pr"},
            category="github",
        ),
        ToolMetadata(
            name="slack.send_message",
            description="Send message to Slack channel",
            mcp_server="slack",
            tags={"slack", "messaging"},
            category="slack",
        ),
        ToolMetadata(
            name="aws.s3.upload",
            description="Upload file to S3 bucket",
            mcp_server="aws",
            tags={"aws", "s3", "storage"},
            category="aws",
        ),
    ]


# ============================================================
# 场景 1: 服务器创建与初始化
# ============================================================


def test_server_creation_and_initialization(temp_data_path: Path) -> None:
    """测试服务器创建与初始化流程"""
    from RegistryTools.server import create_server

    # 创建服务器
    mcp_server = create_server(temp_data_path)

    # 验证服务器创建成功
    assert mcp_server is not None
    assert mcp_server.name == "RegistryTools"

    # 验证数据文件被创建
    data_file = temp_data_path / "tools.json"
    assert data_file.exists()

    # 验证默认工具已加载
    storage = JSONStorage(data_file)
    tools = storage.load_all()
    assert len(tools) > 0  # 应该有默认工具


# ============================================================
# 场景 2: 工具注册与持久化
# ============================================================


def test_tool_registration_and_persistence(temp_data_path: Path, sample_tools: list[ToolMetadata]) -> None:
    """测试工具注册与持久化流程"""
    storage_path = temp_data_path / "tools.json"
    storage = JSONStorage(storage_path)
    registry = ToolRegistry()

    # 注册搜索算法
    registry.register_searcher(SearchMethod.REGEX, RegexSearch(case_sensitive=False))
    registry.register_searcher(SearchMethod.BM25, BM25Search())

    # 注册工具
    for tool in sample_tools:
        registry.register(tool)
        storage.save(tool)

    # 验证工具已注册
    assert registry.tool_count == 3

    # 验证工具已持久化
    assert storage.exists(sample_tools[0].name)

    # 模拟重启：创建新的注册表和存储
    new_storage = JSONStorage(storage_path)
    new_registry = ToolRegistry()

    # 重新加载工具
    if new_storage.validate():
        loaded_tools = new_storage.load_all()
        new_registry.register_many(loaded_tools)

    # 验证工具被正确加载
    assert new_registry.tool_count == 3
    assert new_registry.get_tool("github.create_pull_request") is not None


# ============================================================
# 场景 3: 搜索工作流
# ============================================================


def test_search_workflow(temp_data_path: Path, sample_tools: list[ToolMetadata]) -> None:
    """测试完整的搜索工作流"""
    registry = ToolRegistry()

    # 注册搜索算法
    registry.register_searcher(SearchMethod.BM25, BM25Search())

    # 注册工具
    registry.register_many(sample_tools)

    # 重建搜索索引
    registry.rebuild_indexes()

    # 执行搜索
    results = registry.search("github pull request", SearchMethod.BM25, limit=5)

    # 验证搜索结果
    assert len(results) > 0
    # 验证 GitHub 工具在结果中
    result_names = [r.tool_name for r in results]
    assert "github.create_pull_request" in result_names

    # 测试部分匹配搜索
    slack_results = registry.search("slack message", SearchMethod.BM25)
    assert len(slack_results) > 0
    slack_names = [r.tool_name for r in slack_results]
    assert "slack.send_message" in slack_names


# ============================================================
# 场景 4: 使用频率跟踪
# ============================================================


def test_usage_frequency_tracking(temp_data_path: Path, sample_tools: list[ToolMetadata]) -> None:
    """测试使用频率跟踪功能"""
    registry = ToolRegistry()

    # 注册工具
    registry.register_many(sample_tools)

    # 更新使用频率
    registry.update_usage("github.create_pull_request")
    registry.update_usage("github.create_pull_request")
    registry.update_usage("slack.send_message")

    # 获取使用统计
    github_tool = registry.get_tool("github.create_pull_request")
    slack_tool = registry.get_tool("slack.send_message")

    assert github_tool.use_frequency == 2
    assert slack_tool.use_frequency == 1

    # 获取最常用工具
    most_used = registry.get_most_used(5)
    assert len(most_used) > 0
    assert most_used[0].name == "github.create_pull_request"


# ============================================================
# 场景 5: 存储切换 (JSON → SQLite)
# ============================================================


def test_storage_migration_json_to_sqlite(temp_data_path: Path, sample_tools: list[ToolMetadata]) -> None:
    """测试从 JSON 存储切换到 SQLite 存储"""
    json_path = temp_data_path / "tools.json"
    sqlite_path = temp_data_path / "tools.db"

    # 使用 JSON 存储保存工具
    json_storage = JSONStorage(json_path)
    json_storage.initialize()
    for tool in sample_tools:
        json_storage.save(tool)

    # 验证 JSON 存储
    assert json_storage.count() == 3

    # 迁移到 SQLite
    sqlite_storage = SQLiteStorage(sqlite_path)
    sqlite_storage.initialize()

    # 从 JSON 读取并写入 SQLite
    tools_from_json = json_storage.load_all()
    sqlite_storage.save_many(tools_from_json)

    # 验证 SQLite 存储
    assert sqlite_storage.count() == 3

    # 验证数据一致性
    json_tools = {t.name: t for t in json_storage.load_all()}
    sqlite_tools = {t.name: t for t in sqlite_storage.load_all()}

    assert set(json_tools.keys()) == set(sqlite_tools.keys())
    for name in json_tools:
        assert json_tools[name].description == sqlite_tools[name].description


# ============================================================
# 场景 6: 类别管理
# ============================================================


def test_category_management(temp_data_path: Path) -> None:
    """测试类别管理功能"""
    registry = ToolRegistry()

    # 注册不同类别的工具
    tools = [
        ToolMetadata(
            name="github.pr1",
            description="GitHub PR tool 1",
            category="github",
            tags={"git"},
        ),
        ToolMetadata(
            name="github.pr2",
            description="GitHub PR tool 2",
            category="github",
            tags={"git"},
        ),
        ToolMetadata(
            name="slack.msg1",
            description="Slack tool 1",
            category="slack",
            tags={"chat"},
        ),
    ]

    registry.register_many(tools)

    # 列出所有类别
    categories = registry.list_categories()
    assert "github" in categories
    assert "slack" in categories

    # 按类别列出工具
    github_tools = registry.list_tools(category="github")
    assert len(github_tools) == 2

    slack_tools = registry.list_tools(category="slack")
    assert len(slack_tools) == 1


# ============================================================
# 场景 7: MCP 工具调用
# ============================================================


def test_mcp_tools_integration(temp_data_path: Path) -> None:
    """测试 MCP 工具接口集成"""
    from RegistryTools.server import create_server

    # 创建服务器
    mcp_server = create_server(temp_data_path)

    # 验证服务器创建成功
    assert mcp_server is not None
    assert mcp_server.name == "RegistryTools"

    # 注册自定义工具
    registry = ToolRegistry()
    storage = JSONStorage(temp_data_path / "tools.json")

    custom_tool = ToolMetadata(
        name="custom.test_tool",
        description="A custom test tool",
        category="test",
        tags={"test", "custom"},
    )

    registry.register(custom_tool)
    storage.save(custom_tool)

    # 验证工具可检索
    retrieved = registry.get_tool("custom.test_tool")
    assert retrieved is not None
    assert retrieved.description == "A custom test tool"


# ============================================================
# 场景 8: MCP 资源访问
# ============================================================


def test_mcp_resources_integration(temp_data_path: Path) -> None:
    """测试 MCP 资源接口集成"""
    from RegistryTools.server import create_server

    # 创建服务器并添加工具
    mcp_server = create_server(temp_data_path)

    # 创建注册表用于验证
    registry = ToolRegistry()
    storage = JSONStorage(temp_data_path / "tools.json")

    # 加载现有工具
    if storage.validate():
        tools = storage.load_all()
        registry.register_many(tools)

    # 验证统计数据
    assert registry.tool_count > 0
    assert len(registry.list_categories()) > 0

    # 验证最常用工具列表可获取
    most_used = registry.get_most_used(5)
    assert isinstance(most_used, list)


# ============================================================
# 额外场景: 完整用户工作流
# ============================================================


def test_complete_user_workflow(temp_data_path: Path) -> None:
    """测试完整的用户使用工作流"""
    from RegistryTools.server import create_server

    # 步骤 1: 启动服务器
    mcp_server = create_server(temp_data_path)
    assert mcp_server is not None

    # 步骤 2: 创建新的注册表实例进行操作
    storage = JSONStorage(temp_data_path / "tools.json")
    registry = ToolRegistry()
    registry.register_searcher(SearchMethod.BM25, BM25Search())

    # 加载已有工具
    if storage.validate():
        tools = storage.load_all()
        registry.register_many(tools)

    initial_count = registry.tool_count

    # 步骤 3: 注册新工具
    new_tool = ToolMetadata(
        name="test.workflow.tool",
        description="Tool for workflow testing",
        category="test",
        tags={"workflow", "test"},
    )
    registry.register(new_tool)
    storage.save(new_tool)
    registry.rebuild_indexes()

    # 步骤 4: 搜索工具
    results = registry.search("workflow test", SearchMethod.BM25)
    assert len(results) > 0

    # 步骤 5: 更新使用频率
    registry.update_usage("test.workflow.tool")

    # 步骤 6: 获取统计信息
    assert registry.tool_count == initial_count + 1
    assert "test" in registry.list_categories()

    # 步骤 7: 按类别列出
    test_tools = registry.list_tools(category="test")
    assert len(test_tools) > 0
