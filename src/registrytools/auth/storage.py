"""
API Key 存储层

提供 API Key 持久化存储功能，使用 SQLite 数据库。

Copyright (c) 2026 Maric
License: MIT
"""

import sqlite3
from datetime import datetime
from pathlib import Path

from registrytools.auth.models import (
    APIKey,
    APIKeyMetadata,
    APIKeyPermission,
    APIKeyScope,
    APIKeyUpdateRequest,
)


class APIKeyStorage:
    """
    API Key 存储层

    使用 SQLite 数据库存储 API Key 信息。

    数据库表结构：
    ```sql
    CREATE TABLE api_keys (
        key_id TEXT PRIMARY KEY,
        api_key TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        permission TEXT NOT NULL,
        scope TEXT NOT NULL,
        is_active INTEGER DEFAULT 1,
        created_at TEXT NOT NULL,
        expires_at TEXT,
        last_used_at TEXT,
        usage_count INTEGER DEFAULT 0,
        owner TEXT,
        metadata TEXT
    )
    ```

    Attributes:
        _path: 数据库文件路径
    """

    # 数据库表名称
    _TABLE_NAME = "api_keys"

    def __init__(self, path: str | Path) -> None:
        """
        初始化 API Key 存储

        Args:
            path: 数据库文件路径
        """
        self._path = Path(path)
        # 确保是 .db 文件
        if self._path.suffix != ".db":
            self._path = self._path.with_suffix(".db")
        # 确保父目录存在
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """
        获取数据库连接

        Returns:
            sqlite3.Connection: 数据库连接
        """
        conn = sqlite3.connect(str(self._path))
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_initialized(self) -> None:
        """确保数据库表已创建"""
        table_name = self._TABLE_NAME
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            key_id TEXT PRIMARY KEY,
            api_key TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            permission TEXT NOT NULL,
            scope TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            expires_at TEXT,
            last_used_at TEXT,
            usage_count INTEGER DEFAULT 0,
            owner TEXT,
            metadata TEXT
        )
        """
        create_index_sql = f"""
        CREATE INDEX IF NOT EXISTS idx_api_key ON {table_name}(api_key)
        """
        create_owner_index_sql = f"""
        CREATE INDEX IF NOT EXISTS idx_owner ON {table_name}(owner)
        """

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(create_table_sql)
            cursor.execute(create_index_sql)
            cursor.execute(create_owner_index_sql)
            conn.commit()

    def _row_to_api_key(self, row: sqlite3.Row) -> APIKey:
        """
        将数据库行转换为 APIKey 对象

        Args:
            row: 数据库行

        Returns:
            APIKey: API Key 对象
        """
        import json

        metadata = None
        if row["metadata"]:
            try:
                metadata = json.loads(row["metadata"])
            except Exception:
                pass

        return APIKey(
            key_id=row["key_id"],
            api_key=row["api_key"],
            name=row["name"],
            permission=APIKeyPermission(row["permission"]),
            scope=APIKeyScope(row["scope"]),
            is_active=bool(row["is_active"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            expires_at=datetime.fromisoformat(row["expires_at"]) if row["expires_at"] else None,
            last_used_at=(
                datetime.fromisoformat(row["last_used_at"]) if row["last_used_at"] else None
            ),
            usage_count=row["usage_count"],
            owner=row["owner"],
            metadata=metadata,
        )

    def _api_key_to_row(self, api_key: APIKey) -> tuple:
        """
        将 APIKey 对象转换为数据库行数据

        Args:
            api_key: API Key 对象

        Returns:
            tuple: 数据库行数据
        """
        import json

        metadata_json = None
        if api_key.metadata:
            metadata_json = json.dumps(api_key.metadata)

        return (
            api_key.key_id,
            api_key.api_key,
            api_key.name,
            api_key.permission.value,
            api_key.scope.value,
            1 if api_key.is_active else 0,
            api_key.created_at.isoformat(),
            api_key.expires_at.isoformat() if api_key.expires_at else None,
            api_key.last_used_at.isoformat() if api_key.last_used_at else None,
            api_key.usage_count,
            api_key.owner,
            metadata_json,
        )

    # ============================================================
    # 核心方法
    # ============================================================

    def save(self, api_key: APIKey) -> None:
        """
        保存 API Key

        如果 API Key 已存在，则更新其信息。

        Args:
            api_key: API Key 对象

        Raises:
            IOError: 如果保存失败
        """
        self._ensure_initialized()

        try:
            table_name = self._TABLE_NAME
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"""
                    INSERT OR REPLACE INTO {table_name}
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    self._api_key_to_row(api_key),
                )
                conn.commit()
        except sqlite3.Error as e:
            raise OSError(f"保存 API Key 到数据库失败: {e}") from e

    def get_by_api_key(self, api_key: str) -> APIKey | None:
        """
        通过 API Key 值获取 API Key 对象

        Args:
            api_key: API Key 密钥值

        Returns:
            APIKey: API Key 对象，如果不存在则返回 None
        """
        self._ensure_initialized()

        try:
            table_name = self._TABLE_NAME
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"SELECT * FROM {table_name} WHERE api_key = ?",
                    (api_key,),
                )
                row = cursor.fetchone()

                if row:
                    return self._row_to_api_key(row)
                return None
        except sqlite3.Error as e:
            raise OSError(f"从数据库获取 API Key 失败: {e}") from e

    def get_by_key_id(self, key_id: str) -> APIKey | None:
        """
        通过 Key ID 获取 API Key 对象

        Args:
            key_id: API Key 唯一标识符

        Returns:
            APIKey: API Key 对象，如果不存在则返回 None
        """
        self._ensure_initialized()

        try:
            table_name = self._TABLE_NAME
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"SELECT * FROM {table_name} WHERE key_id = ?",
                    (key_id,),
                )
                row = cursor.fetchone()

                if row:
                    return self._row_to_api_key(row)
                return None
        except sqlite3.Error as e:
            raise OSError(f"从数据库获取 API Key 失败: {e}") from e

    def list_all(self, owner: str | None = None) -> list[APIKeyMetadata]:
        """
        列出所有 API Key 的元数据

        Args:
            owner: 所有者标识，如果指定则只返回该所有者的 API Key

        Returns:
            list[APIKeyMetadata]: API Key 元数据列表
        """
        self._ensure_initialized()

        try:
            table_name = self._TABLE_NAME
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if owner:
                    cursor.execute(
                        f"SELECT * FROM {table_name} WHERE owner = ?",
                        (owner,),
                    )
                else:
                    cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()

                return [APIKeyMetadata.from_api_key(self._row_to_api_key(row)) for row in rows]
        except sqlite3.Error as e:
            raise OSError(f"从数据库列出 API Key 失败: {e}") from e

    def delete(self, key_id: str) -> bool:
        """
        删除 API Key

        Args:
            key_id: API Key 唯一标识符

        Returns:
            bool: True 如果 API Key 存在并被删除，False 如果不存在
        """
        self._ensure_initialized()

        try:
            table_name = self._TABLE_NAME
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"DELETE FROM {table_name} WHERE key_id = ?",
                    (key_id,),
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            raise OSError(f"从数据库删除 API Key 失败: {e}") from e

    def update(self, key_id: str, request: APIKeyUpdateRequest) -> APIKey | None:
        """
        更新 API Key

        Args:
            key_id: API Key 唯一标识符
            request: 更新请求

        Returns:
            APIKey: 更新后的 API Key 对象，如果不存在则返回 None
        """
        self._ensure_initialized()

        # 先获取现有 API Key
        api_key = self.get_by_key_id(key_id)
        if not api_key:
            return None

        # 更新字段
        if request.name is not None:
            api_key.name = request.name
        if request.permission is not None:
            api_key.permission = request.permission
        if request.scope is not None:
            api_key.scope = request.scope
        if request.is_active is not None:
            api_key.is_active = request.is_active
        if request.metadata is not None:
            api_key.metadata = request.metadata

        # 保存更新
        self.save(api_key)
        return api_key

    def record_usage(self, api_key: str) -> None:
        """
        记录 API Key 使用

        更新最后使用时间和使用次数。

        Args:
            api_key: API Key 密钥值
        """
        self._ensure_initialized()

        try:
            table_name = self._TABLE_NAME
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"""
                    UPDATE {table_name}
                    SET last_used_at = ?, usage_count = usage_count + 1
                    WHERE api_key = ?
                    """,
                    (datetime.now().isoformat(), api_key),
                )
                conn.commit()
        except sqlite3.Error as e:
            raise OSError(f"记录 API Key 使用失败: {e}") from e

    def count(self, owner: str | None = None) -> int:
        """
        获取 API Key 数量

        Args:
            owner: 所有者标识，如果指定则只统计该所有者的 API Key

        Returns:
            int: API Key 数量
        """
        self._ensure_initialized()

        try:
            table_name = self._TABLE_NAME
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if owner:
                    cursor.execute(
                        f"SELECT COUNT(*) FROM {table_name} WHERE owner = ?",
                        (owner,),
                    )
                else:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row = cursor.fetchone()
                return row[0] if row else 0
        except sqlite3.Error as e:
            raise OSError(f"统计 API Key 数量失败: {e}") from e

    def cleanup_expired(self) -> int:
        """
        清理过期的 API Key

        删除所有已过期且超过 30 天的 API Key。

        Returns:
            int: 删除的 API Key 数量
        """
        self._ensure_initialized()

        try:
            table_name = self._TABLE_NAME
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # 删除过期的 API Key
                expiration_threshold = datetime.now().isoformat()
                cursor.execute(
                    f"""
                    DELETE FROM {table_name}
                    WHERE expires_at IS NOT NULL AND expires_at < ?
                    """,
                    (expiration_threshold,),
                )
                conn.commit()
                return cursor.rowcount
        except sqlite3.Error as e:
            raise OSError(f"清理过期 API Key 失败: {e}") from e
