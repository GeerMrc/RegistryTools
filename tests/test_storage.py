"""
存储层单元测试

测试 ToolStorage 基类、JSONStorage 和 SQLiteStorage 实现。

Copyright (c) 2026 Maric
License: MIT
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

import pytest

from RegistryTools.registry.models import ToolMetadata
from RegistryTools.storage.base import ToolStorage
from RegistryTools.storage.json_storage import JSONStorage
from RegistryTools.storage.sqlite_storage import SQLiteStorage

# ============================================================
# 测试数据
# ============================================================


@pytest.fixture
def sample_tools() -> list[ToolMetadata]:
    """返回示例工具列表"""
    return [
        ToolMetadata(
            name="github.create_pr",
            description="Create a pull request",
            mcp_server="github",
            tags={"github", "git", "pr"},
            category="github",
        ),
        ToolMetadata(
            name="aws.s3.upload",
            description="Upload file to S3",
            mcp_server="aws",
            tags={"aws", "s3", "storage"},
            category="aws",
            use_frequency=5,
            last_used=datetime(2026, 1, 1, 12, 0, 0),
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
def json_storage(tmp_path: Path) -> JSONStorage:
    """返回临时 JSONStorage 实例"""
    storage = JSONStorage(tmp_path / "test_tools.json")
    storage.initialize()
    return storage


@pytest.fixture
def sqlite_storage(tmp_path: Path) -> SQLiteStorage:
    """返回临时 SQLiteStorage 实例"""
    storage = SQLiteStorage(tmp_path / "test_tools.db")
    storage.initialize()
    return storage


# ============================================================
# ToolStorage 基类测试 (TASK-404)
# ============================================================


class TestToolStorage:
    """测试 ToolStorage 抽象基类"""

    def test_cannot_instantiate_abstract_class(self, tmp_path: Path) -> None:
        """测试不能直接实例化抽象基类"""
        with pytest.raises(TypeError):
            ToolStorage(tmp_path / "test.json")  # type: ignore

    def test_abstract_methods(self) -> None:
        """测试抽象方法定义"""
        abstract_methods = ToolStorage.__abstractmethods__
        assert "load_all" in abstract_methods
        assert "save" in abstract_methods
        assert "save_many" in abstract_methods
        assert "delete" in abstract_methods
        assert "exists" in abstract_methods


# ============================================================
# JSONStorage 测试
# ============================================================


class TestJSONStorage:
    """测试 JSONStorage 实现"""

    # ------------------------------------------------------------
    # 初始化测试
    # ------------------------------------------------------------

    def test_initialization(self, tmp_path: Path) -> None:
        """测试初始化"""
        storage = JSONStorage(tmp_path / "tools.json")
        assert storage.path.name == "tools.json"
        assert storage.path.parent == tmp_path

    def test_auto_add_json_extension(self, tmp_path: Path) -> None:
        """测试自动添加 .json 扩展名"""
        storage = JSONStorage(tmp_path / "tools")
        assert storage.path.suffix == ".json"

    def test_initialize_creates_file(self, tmp_path: Path) -> None:
        """测试 initialize 创建空 JSON 文件"""
        storage = JSONStorage(tmp_path / "tools.json")
        storage.initialize()
        assert storage.path.exists()
        assert storage.path.is_file()

    # ------------------------------------------------------------
    # load_all 测试
    # ------------------------------------------------------------

    def test_load_all_empty(self, json_storage: JSONStorage) -> None:
        """测试加载空的存储"""
        tools = json_storage.load_all()
        assert tools == []

    def test_load_all_returns_tools(
        self, json_storage: JSONStorage, sample_tools: list[ToolMetadata]
    ) -> None:
        """测试加载保存的工具"""
        json_storage.save_many(sample_tools)
        loaded_tools = json_storage.load_all()

        assert len(loaded_tools) == len(sample_tools)
        loaded_names = {t.name for t in loaded_tools}
        expected_names = {t.name for t in sample_tools}
        assert loaded_names == expected_names

    def test_load_all_nonexistent_file(self, tmp_path: Path) -> None:
        """测试加载不存在的文件返回空列表"""
        storage = JSONStorage(tmp_path / "nonexistent.json")
        tools = storage.load_all()
        assert tools == []

    # ------------------------------------------------------------
    # save 测试
    # ------------------------------------------------------------

    def test_save_single_tool(
        self, json_storage: JSONStorage, sample_tools: list[ToolMetadata]
    ) -> None:
        """测试保存单个工具"""
        tool = sample_tools[0]
        json_storage.save(tool)

        loaded = json_storage.get(tool.name)
        assert loaded is not None
        assert loaded.name == tool.name
        assert loaded.description == tool.description

    def test_save_updates_existing(
        self, json_storage: JSONStorage, sample_tools: list[ToolMetadata]
    ) -> None:
        """测试保存已存在的工具会更新"""
        tool = sample_tools[0]
        json_storage.save(tool)

        # 更新工具
        updated_tool = ToolMetadata(
            name=tool.name,
            description="Updated description",
            tags={"updated"},
        )
        json_storage.save(updated_tool)

        loaded = json_storage.get(tool.name)
        assert loaded is not None
        assert loaded.description == "Updated description"

    # ------------------------------------------------------------
    # save_many 测试
    # ------------------------------------------------------------

    def test_save_many_tools(
        self, json_storage: JSONStorage, sample_tools: list[ToolMetadata]
    ) -> None:
        """测试批量保存工具"""
        json_storage.save_many(sample_tools)

        assert json_storage.count() == len(sample_tools)

    def test_save_many_empty_list(self, json_storage: JSONStorage) -> None:
        """测试批量保存空列表"""
        json_storage.save_many([])
        assert json_storage.is_empty()

    # ------------------------------------------------------------
    # delete 测试
    # ------------------------------------------------------------

    def test_delete_existing_tool(
        self, json_storage: JSONStorage, sample_tools: list[ToolMetadata]
    ) -> None:
        """测试删除已存在的工具"""
        json_storage.save_many(sample_tools)

        result = json_storage.delete(sample_tools[0].name)
        assert result is True
        assert json_storage.count() == len(sample_tools) - 1

    def test_delete_nonexistent_tool(self, json_storage: JSONStorage) -> None:
        """测试删除不存在的工具"""
        result = json_storage.delete("nonexistent")
        assert result is False

    # ------------------------------------------------------------
    # exists 测试
    # ------------------------------------------------------------

    def test_exists_true(self, json_storage: JSONStorage, sample_tools: list[ToolMetadata]) -> None:
        """测试存在的工具"""
        json_storage.save_many(sample_tools)
        assert json_storage.exists(sample_tools[0].name) is True

    def test_exists_false(self, json_storage: JSONStorage) -> None:
        """测试不存在的工具"""
        assert json_storage.exists("nonexistent") is False

    # ------------------------------------------------------------
    # 工具方法测试
    # ------------------------------------------------------------

    def test_count(self, json_storage: JSONStorage, sample_tools: list[ToolMetadata]) -> None:
        """测试计数"""
        assert json_storage.count() == 0
        json_storage.save_many(sample_tools)
        assert json_storage.count() == len(sample_tools)

    def test_is_empty(self, json_storage: JSONStorage) -> None:
        """测试是否为空"""
        assert json_storage.is_empty() is True

    def test_get(self, json_storage: JSONStorage, sample_tools: list[ToolMetadata]) -> None:
        """测试获取工具"""
        json_storage.save_many(sample_tools)
        tool = json_storage.get(sample_tools[0].name)
        assert tool is not None
        assert tool.name == sample_tools[0].name

    def test_get_nonexistent(self, json_storage: JSONStorage) -> None:
        """测试获取不存在的工具"""
        tool = json_storage.get("nonexistent")
        assert tool is None

    def test_clear(self, json_storage: JSONStorage, sample_tools: list[ToolMetadata]) -> None:
        """测试清空存储"""
        json_storage.save_many(sample_tools)
        json_storage.clear()
        assert json_storage.is_empty()
        assert not json_storage.path.exists()

    # ------------------------------------------------------------
    # 数据完整性测试
    # ------------------------------------------------------------

    def test_persists_datetime(
        self, json_storage: JSONStorage, sample_tools: list[ToolMetadata]
    ) -> None:
        """测试 datetime 序列化"""
        tool_with_time = sample_tools[1]  # 包含 last_used
        json_storage.save(tool_with_time)

        loaded = json_storage.get(tool_with_time.name)
        assert loaded is not None
        assert loaded.last_used is not None
        assert loaded.last_used == tool_with_time.last_used

    def test_persists_tags(
        self, json_storage: JSONStorage, sample_tools: list[ToolMetadata]
    ) -> None:
        """测试 tags 序列化"""
        tool = sample_tools[0]
        json_storage.save(tool)

        loaded = json_storage.get(tool.name)
        assert loaded is not None
        assert loaded.tags == tool.tags

    def test_atomic_write(
        self, json_storage: JSONStorage, sample_tools: list[ToolMetadata]
    ) -> None:
        """测试原子写入"""
        json_storage.save_many(sample_tools)

        # 验证 JSON 文件格式正确
        with open(json_storage.path, encoding="utf-8") as f:
            data = json.load(f)

        assert isinstance(data, dict)
        assert len(data) == len(sample_tools)


# ============================================================
# SQLiteStorage 测试
# ============================================================


class TestSQLiteStorage:
    """测试 SQLiteStorage 实现"""

    # ------------------------------------------------------------
    # 初始化测试
    # ------------------------------------------------------------

    def test_initialization(self, tmp_path: Path) -> None:
        """测试初始化"""
        storage = SQLiteStorage(tmp_path / "tools.db")
        assert storage.path.name == "tools.db"

    def test_auto_add_db_extension(self, tmp_path: Path) -> None:
        """测试自动添加 .db 扩展名"""
        storage = SQLiteStorage(tmp_path / "tools")
        assert storage.path.suffix == ".db"

    def test_initialize_creates_table(self, sqlite_storage: SQLiteStorage) -> None:
        """测试 initialize 创建数据库表"""
        assert sqlite_storage.path.exists()

        # 验证表结构
        conn = sqlite3.connect(sqlite_storage.path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tools'")
        result = cursor.fetchone()
        conn.close()

        assert result is not None

    # ------------------------------------------------------------
    # load_all 测试
    # ------------------------------------------------------------

    def test_load_all_empty(self, sqlite_storage: SQLiteStorage) -> None:
        """测试加载空的存储"""
        tools = sqlite_storage.load_all()
        assert tools == []

    def test_load_all_returns_tools(
        self, sqlite_storage: SQLiteStorage, sample_tools: list[ToolMetadata]
    ) -> None:
        """测试加载保存的工具"""
        sqlite_storage.save_many(sample_tools)
        loaded_tools = sqlite_storage.load_all()

        assert len(loaded_tools) == len(sample_tools)
        loaded_names = {t.name for t in loaded_tools}
        expected_names = {t.name for t in sample_tools}
        assert loaded_names == expected_names

    # ------------------------------------------------------------
    # save 测试
    # ------------------------------------------------------------

    def test_save_single_tool(
        self, sqlite_storage: SQLiteStorage, sample_tools: list[ToolMetadata]
    ) -> None:
        """测试保存单个工具"""
        tool = sample_tools[0]
        sqlite_storage.save(tool)

        loaded = sqlite_storage.get(tool.name)
        assert loaded is not None
        assert loaded.name == tool.name
        assert loaded.description == tool.description

    def test_save_updates_existing(
        self, sqlite_storage: SQLiteStorage, sample_tools: list[ToolMetadata]
    ) -> None:
        """测试保存已存在的工具会更新"""
        tool = sample_tools[0]
        sqlite_storage.save(tool)

        # 更新工具
        updated_tool = ToolMetadata(
            name=tool.name,
            description="Updated description",
            tags={"updated"},
        )
        sqlite_storage.save(updated_tool)

        loaded = sqlite_storage.get(tool.name)
        assert loaded is not None
        assert loaded.description == "Updated description"

    # ------------------------------------------------------------
    # save_many 测试
    # ------------------------------------------------------------

    def test_save_many_tools(
        self, sqlite_storage: SQLiteStorage, sample_tools: list[ToolMetadata]
    ) -> None:
        """测试批量保存工具"""
        sqlite_storage.save_many(sample_tools)

        assert sqlite_storage.count() == len(sample_tools)

    def test_save_many_empty_list(self, sqlite_storage: SQLiteStorage) -> None:
        """测试批量保存空列表"""
        sqlite_storage.save_many([])
        assert sqlite_storage.is_empty()

    # ------------------------------------------------------------
    # delete 测试
    # ------------------------------------------------------------

    def test_delete_existing_tool(
        self, sqlite_storage: SQLiteStorage, sample_tools: list[ToolMetadata]
    ) -> None:
        """测试删除已存在的工具"""
        sqlite_storage.save_many(sample_tools)

        result = sqlite_storage.delete(sample_tools[0].name)
        assert result is True
        assert sqlite_storage.count() == len(sample_tools) - 1

    def test_delete_nonexistent_tool(self, sqlite_storage: SQLiteStorage) -> None:
        """测试删除不存在的工具"""
        result = sqlite_storage.delete("nonexistent")
        assert result is False

    # ------------------------------------------------------------
    # exists 测试
    # ------------------------------------------------------------

    def test_exists_true(
        self, sqlite_storage: SQLiteStorage, sample_tools: list[ToolMetadata]
    ) -> None:
        """测试存在的工具"""
        sqlite_storage.save_many(sample_tools)
        assert sqlite_storage.exists(sample_tools[0].name) is True

    def test_exists_false(self, sqlite_storage: SQLiteStorage) -> None:
        """测试不存在的工具"""
        assert sqlite_storage.exists("nonexistent") is False

    # ------------------------------------------------------------
    # 工具方法测试
    # ------------------------------------------------------------

    def test_count(self, sqlite_storage: SQLiteStorage, sample_tools: list[ToolMetadata]) -> None:
        """测试计数"""
        assert sqlite_storage.count() == 0
        sqlite_storage.save_many(sample_tools)
        assert sqlite_storage.count() == len(sample_tools)

    def test_is_empty(self, sqlite_storage: SQLiteStorage) -> None:
        """测试是否为空"""
        assert sqlite_storage.is_empty() is True

    def test_get(self, sqlite_storage: SQLiteStorage, sample_tools: list[ToolMetadata]) -> None:
        """测试获取工具"""
        sqlite_storage.save_many(sample_tools)
        tool = sqlite_storage.get(sample_tools[0].name)
        assert tool is not None
        assert tool.name == sample_tools[0].name

    def test_get_nonexistent(self, sqlite_storage: SQLiteStorage) -> None:
        """测试获取不存在的工具"""
        tool = sqlite_storage.get("nonexistent")
        assert tool is None

    def test_clear(self, sqlite_storage: SQLiteStorage, sample_tools: list[ToolMetadata]) -> None:
        """测试清空存储"""
        sqlite_storage.save_many(sample_tools)
        sqlite_storage.clear()
        assert sqlite_storage.is_empty()

    # ------------------------------------------------------------
    # 数据完整性测试
    # ------------------------------------------------------------

    def test_persists_datetime(
        self, sqlite_storage: SQLiteStorage, sample_tools: list[ToolMetadata]
    ) -> None:
        """测试 datetime 序列化"""
        tool_with_time = sample_tools[1]  # 包含 last_used
        sqlite_storage.save(tool_with_time)

        loaded = sqlite_storage.get(tool_with_time.name)
        assert loaded is not None
        assert loaded.last_used is not None
        assert loaded.last_used == tool_with_time.last_used

    def test_persists_tags(
        self, sqlite_storage: SQLiteStorage, sample_tools: list[ToolMetadata]
    ) -> None:
        """测试 tags 序列化"""
        tool = sample_tools[0]
        sqlite_storage.save(tool)

        loaded = sqlite_storage.get(tool.name)
        assert loaded is not None
        assert loaded.tags == tool.tags

    def test_persists_use_frequency(
        self, sqlite_storage: SQLiteStorage, sample_tools: list[ToolMetadata]
    ) -> None:
        """测试使用频率序列化"""
        tool = sample_tools[1]  # use_frequency=5
        sqlite_storage.save(tool)

        loaded = sqlite_storage.get(tool.name)
        assert loaded is not None
        assert loaded.use_frequency == 5

    def test_defer_loading_boolean(
        self, sqlite_storage: SQLiteStorage, sample_tools: list[ToolMetadata]
    ) -> None:
        """测试 defer_loading 布尔值序列化"""
        tool = sample_tools[0]
        sqlite_storage.save(tool)

        loaded = sqlite_storage.get(tool.name)
        assert loaded is not None
        assert loaded.defer_loading is True

    # ------------------------------------------------------------
    # 事务测试
    # ------------------------------------------------------------

    def test_save_many_atomicity(
        self, sqlite_storage: SQLiteStorage, sample_tools: list[ToolMetadata]
    ) -> None:
        """测试批量保存的原子性"""
        # 先保存一些工具
        sqlite_storage.save_many(sample_tools[:2])
        original_count = sqlite_storage.count()

        # 批量保存包含重复的工具（应该更新而不是新增）
        duplicate_tool = ToolMetadata(
            name=sample_tools[0].name,
            description="Updated description",
            tags={"updated"},
        )

        sqlite_storage.save_many([duplicate_tool])

        # 验证：工具数量不变，但内容已更新
        assert sqlite_storage.count() == original_count

        loaded = sqlite_storage.get(sample_tools[0].name)
        assert loaded is not None
        assert loaded.description == "Updated description"


# ============================================================
# 跨存储实现测试
# ============================================================


class TestStorageImplementations:
    """测试所有存储实现的通用行为"""

    @pytest.mark.parametrize(
        "storage_factory",
        [
            lambda tmp_path: JSONStorage(tmp_path / "test.json"),
            lambda tmp_path: SQLiteStorage(tmp_path / "test.db"),
        ],
    )
    def test_storage_workflow(
        self, storage_factory, sample_tools: list[ToolMetadata], tmp_path: Path
    ) -> None:
        """测试完整的存储工作流"""
        storage = storage_factory(tmp_path)
        storage.initialize()

        # 1. 初始状态为空
        assert storage.is_empty()

        # 2. 保存工具
        storage.save_many(sample_tools)
        assert storage.count() == len(sample_tools)

        # 3. 加载工具
        loaded_tools = storage.load_all()
        assert len(loaded_tools) == len(sample_tools)

        # 4. 检查工具存在
        for tool in sample_tools:
            assert storage.exists(tool.name)

        # 5. 删除工具
        storage.delete(sample_tools[0].name)
        assert storage.count() == len(sample_tools) - 1

        # 6. 清空存储
        storage.clear()
        assert storage.is_empty()

    @pytest.mark.parametrize(
        "storage_factory",
        [
            lambda tmp_path: JSONStorage(tmp_path / "test.json"),
            lambda tmp_path: SQLiteStorage(tmp_path / "test.db"),
        ],
    )
    def test_validate_method(self, storage_factory, tmp_path: Path) -> None:
        """测试 validate 方法"""
        storage = storage_factory(tmp_path)
        storage.initialize()

        assert storage.validate() is True

        # 删除文件
        storage.path.unlink()
        assert storage.validate() is False
