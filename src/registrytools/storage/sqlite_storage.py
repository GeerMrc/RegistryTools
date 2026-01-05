"""
SQLite 存储实现

使用 SQLite 数据库持久化工具元数据。

Copyright (c) 2026 Maric
License: MIT
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from registrytools.defaults import HOT_TOOL_THRESHOLD, WARM_TOOL_THRESHOLD
from registrytools.registry.models import ToolMetadata
from registrytools.storage.base import ToolStorage

if TYPE_CHECKING:
    from registrytools.registry.models import ToolTemperature


class SQLiteStorage(ToolStorage):
    """
    SQLite 数据库存储实现

    将工具元数据存储到 SQLite 数据库。使用单表结构：
    ```sql
    CREATE TABLE tools (
        name TEXT PRIMARY KEY,
        description TEXT NOT NULL,
        mcp_server TEXT,
        defer_loading INTEGER DEFAULT 1,
        tags TEXT,
        category TEXT,
        use_frequency INTEGER DEFAULT 0,
        last_used TEXT,
        input_schema TEXT,
        output_schema TEXT
    )
    ```

    Attributes:
        _path: 数据库文件路径
    """

    # 数据库表结构
    _TABLE_NAME = "tools"
    _CREATE_TABLE_SQL = f"""
    CREATE TABLE IF NOT EXISTS {_TABLE_NAME} (
        name TEXT PRIMARY KEY,
        description TEXT NOT NULL,
        mcp_server TEXT,
        defer_loading INTEGER DEFAULT 1,
        tags TEXT,
        category TEXT,
        use_frequency INTEGER DEFAULT 0,
        last_used TEXT,
        temperature TEXT DEFAULT 'cold',
        input_schema TEXT,
        output_schema TEXT
    )
    """

    def __init__(self, path: str | Path) -> None:
        """
        初始化 SQLite 存储

        Args:
            path: 数据库文件路径（如 ~/.RegistryTools/tools.db）
        """
        super().__init__(path)
        # 确保是 .db 文件
        if self._path.suffix != ".db":
            self._path = self._path.with_suffix(".db")

    # ============================================================
    # 核心方法实现 (TASK-403)
    # ============================================================

    def load_all(self) -> list[ToolMetadata]:
        """
        加载所有工具元数据

        Returns:
            工具元数据列表

        Raises:
            IOError: 如果读取失败
        """
        self._ensure_initialized()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM {self._TABLE_NAME}")
                rows = cursor.fetchall()

            # 转换为 ToolMetadata 列表
            tools = []
            for row in rows:
                try:
                    tool = self._row_to_tool(row)
                    tools.append(tool)
                except Exception:
                    # 跳过无效的数据
                    continue

            return tools

        except sqlite3.Error as e:
            raise OSError(f"从数据库加载工具失败: {e}") from e

    def save(self, tool: ToolMetadata) -> None:
        """
        保存单个工具元数据

        如果工具已存在，则更新其元数据。

        Args:
            tool: 工具元数据

        Raises:
            IOError: 如果保存失败
        """
        self._ensure_initialized()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"""
                    INSERT OR REPLACE INTO {self._TABLE_NAME}
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    self._tool_to_row(tool),
                )
                conn.commit()

        except sqlite3.Error as e:
            raise OSError(f"保存工具到数据库失败: {e}") from e

    def save_many(self, tools: list[ToolMetadata]) -> None:
        """
        批量保存工具元数据

        使用事务确保原子性。

        Args:
            tools: 工具元数据列表

        Raises:
            IOError: 如果保存失败
        """
        if not tools:
            return

        self._ensure_initialized()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # 开始事务
                cursor.execute("BEGIN TRANSACTION")

                try:
                    # 批量插入
                    for tool in tools:
                        cursor.execute(
                            f"""
                            INSERT OR REPLACE INTO {self._TABLE_NAME}
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            self._tool_to_row(tool),
                        )
                    # 提交事务
                    conn.commit()
                except Exception:
                    # 回滚事务
                    conn.rollback()
                    raise

        except sqlite3.Error as e:
            raise OSError(f"批量保存工具到数据库失败: {e}") from e

    def delete(self, tool_name: str) -> bool:
        """
        删除工具元数据

        Args:
            tool_name: 工具名称

        Returns:
            True 如果工具存在并被删除，False 如果工具不存在

        Raises:
            IOError: 如果删除失败
        """
        self._ensure_initialized()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"DELETE FROM {self._TABLE_NAME} WHERE name = ?", (tool_name,))
                conn.commit()

                # 检查是否删除了行
                return cursor.rowcount > 0

        except sqlite3.Error as e:
            raise OSError(f"从数据库删除工具失败: {e}") from e

    def exists(self, tool_name: str) -> bool:
        """
        检查工具是否存在

        Args:
            tool_name: 工具名称

        Returns:
            True 如果工具存在，否则 False
        """
        self._ensure_initialized()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT 1 FROM {self._TABLE_NAME} WHERE name = ?", (tool_name,))
                return cursor.fetchone() is not None

        except sqlite3.Error:
            return False

    def load_by_temperature(
        self,
        temperature: "ToolTemperature",
        limit: int | None = None,
    ) -> list[ToolMetadata]:
        """
        按温度级别加载工具 (TASK-802)

        SQLite 优化版本：使用 WHERE 子句直接过滤。

        Args:
            temperature: 温度级别 (HOT/WARM/COLD)
            limit: 加载数量限制

        Returns:
            工具元数据列表
        """
        self._ensure_initialized()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # 根据温度构建 WHERE 子句
                if temperature.value == "hot":
                    where_clause = f"use_frequency >= {HOT_TOOL_THRESHOLD}"
                elif temperature.value == "warm":
                    where_clause = (
                        f"use_frequency >= {WARM_TOOL_THRESHOLD} "
                        f"AND use_frequency < {HOT_TOOL_THRESHOLD}"
                    )
                else:  # cold
                    where_clause = f"use_frequency < {WARM_TOOL_THRESHOLD}"

                # 构建 SQL 查询
                sql = f"SELECT * FROM {self._TABLE_NAME} WHERE {where_clause}"
                if limit:
                    sql += f" LIMIT {limit}"

                cursor.execute(sql)
                rows = cursor.fetchall()

            # 转换为 ToolMetadata 列表
            tools = []
            for row in rows:
                try:
                    tool = self._row_to_tool(row)
                    tools.append(tool)
                except Exception:
                    continue

            return tools

        except sqlite3.Error as e:
            raise OSError(f"按温度加载工具失败: {e}") from e

    # ============================================================
    # 优化的工具方法
    # ============================================================

    def count(self) -> int:
        """
        获取工具数量

        Returns:
            工具数量
        """
        self._ensure_initialized()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM {self._TABLE_NAME}")
                result = cursor.fetchone()
                return result[0] if result else 0

        except sqlite3.Error:
            return 0

    def is_empty(self) -> bool:
        """
        检查存储是否为空

        Returns:
            True 如果存储为空，否则 False
        """
        return self.count() == 0

    def get(self, tool_name: str) -> ToolMetadata | None:
        """
        获取指定工具的元数据

        Args:
            tool_name: 工具名称

        Returns:
            工具元数据，如果不存在则返回 None
        """
        self._ensure_initialized()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM {self._TABLE_NAME} WHERE name = ?", (tool_name,))
                row = cursor.fetchone()

                if row is None:
                    return None

                return self._row_to_tool(row)

        except sqlite3.Error:
            return None

    def clear(self) -> None:
        """
        清空所有工具元数据

        删除表中的所有数据。
        """
        self._ensure_initialized()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"DELETE FROM {self._TABLE_NAME}")
                conn.commit()

        except sqlite3.Error as e:
            raise OSError(f"清空数据库失败: {e}") from e

    def initialize(self) -> None:
        """
        初始化存储

        创建数据库文件和表结构。
        """
        super().initialize()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(self._CREATE_TABLE_SQL)
                conn.commit()

        except sqlite3.Error as e:
            raise OSError(f"初始化数据库失败: {e}") from e

    def validate(self) -> bool:
        """
        验证存储完整性

        Returns:
            True 如果存储有效，否则 False
        """
        try:
            if not self._path.exists():
                return False
            if not self._path.is_file():
                return False
            # 尝试连接数据库
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (self._TABLE_NAME,),
                )
                return cursor.fetchone() is not None
        except Exception:
            return False

    # ============================================================
    # 私有辅助方法
    # ============================================================

    def _get_connection(self) -> sqlite3.Connection:
        """
        获取数据库连接

        Returns:
            SQLite 连接对象
        """
        return sqlite3.connect(self._path, timeout=10.0)

    def _ensure_initialized(self) -> None:
        """确保数据库已初始化"""
        if not self._path.exists():
            self.initialize()

    def _tool_to_row(self, tool: ToolMetadata) -> tuple:
        """
        将 ToolMetadata 转换为数据库行

        Args:
            tool: 工具元数据

        Returns:
            数据库行元组
        """
        return (
            tool.name,
            tool.description,
            tool.mcp_server,
            1 if tool.defer_loading else 0,
            json.dumps(list(tool.tags), ensure_ascii=False),
            tool.category,
            tool.use_frequency,
            self._serialize_datetime(tool.last_used),
            tool.temperature.value,
            json.dumps(tool.input_schema) if tool.input_schema else None,
            json.dumps(tool.output_schema) if tool.output_schema else None,
        )

    def _row_to_tool(self, row: tuple) -> ToolMetadata:
        """
        将数据库行转换为 ToolMetadata

        Args:
            row: 数据库行元组

        Returns:
            工具元数据
        """
        from registrytools.registry.models import ToolTemperature

        # 处理旧数据：可能没有 temperature 字段
        if len(row) == 10:
            # 旧格式（无 temperature 字段）
            (
                name,
                description,
                mcp_server,
                defer_loading,
                tags,
                category,
                use_frequency,
                last_used,
                input_schema,
                output_schema,
            ) = row
            temperature = ToolTemperature.COLD
        else:
            # 新格式（有 temperature 字段）
            (
                name,
                description,
                mcp_server,
                defer_loading,
                tags,
                category,
                use_frequency,
                last_used,
                temperature,
                input_schema,
                output_schema,
            ) = row
            # 将字符串转换为 ToolTemperature 枚举
            if isinstance(temperature, str):
                try:
                    temperature = ToolTemperature(temperature)
                except ValueError:
                    temperature = ToolTemperature.COLD
            else:
                temperature = ToolTemperature.COLD

        return ToolMetadata(
            name=name,
            description=description,
            mcp_server=mcp_server,
            defer_loading=bool(defer_loading),
            tags=set(json.loads(tags) if tags else []),
            category=category,
            use_frequency=use_frequency,
            last_used=self._deserialize_datetime(last_used),
            temperature=temperature,
            input_schema=json.loads(input_schema) if input_schema else None,
            output_schema=json.loads(output_schema) if output_schema else None,
        )

    @staticmethod
    def _serialize_datetime(dt: datetime | None) -> str | None:
        """
        序列化 datetime 对象

        Args:
            dt: datetime 对象

        Returns:
            ISO 格式字符串
        """
        return dt.isoformat() if dt else None

    @staticmethod
    def _deserialize_datetime(s: str | None) -> datetime | None:
        """
        反序列化 datetime 对象

        Args:
            s: ISO 格式字符串

        Returns:
            datetime 对象
        """
        return datetime.fromisoformat(s) if s else None
