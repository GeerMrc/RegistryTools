"""
API Key 认证数据模型

定义 API Key 认证相关的数据模型。

Copyright (c) 2026 Maric
License: MIT
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class APIKeyPermission(str, Enum):
    """API Key 权限级别枚举"""

    READ = "read"
    """只读权限: 可以搜索工具、获取定义"""

    WRITE = "write"
    """读写权限: 可以搜索、获取定义、注册/注销工具"""

    ADMIN = "admin"
    """管理员权限: 包含读写权限，还可以管理 API Key"""


class APIKeyScope(str, Enum):
    """API Key 作用范围枚举"""

    ALL = "all"
    """所有操作"""

    SEARCH_ONLY = "search_only"
    """仅搜索操作"""

    MANAGEMENT = "management"
    """工具管理操作"""


class APIKey(BaseModel):
    """
    API Key 完整模型

    存储 API Key 的完整信息，包括密钥值、权限、使用统计等。

    Attributes:
        key_id: API Key 唯一标识符（UUID）
        api_key: API Key 密钥值（格式: rtk_<32-char-hex>）
        name: API Key 名称/描述
        permission: 权限级别
        scope: 作用范围
        is_active: 是否激活
        created_at: 创建时间
        expires_at: 过期时间（可选，None 表示永不过期）
        last_used_at: 最后使用时间（可选）
        usage_count: 使用次数统计
        owner: 所有者标识（可选，用于多租户）
        metadata: 额外元数据（可选）
    """

    key_id: str
    """API Key 唯一标识符（UUID）"""

    api_key: str
    """API Key 密钥值（格式: rtk_<32-char-hex>）"""

    name: str
    """API Key 名称/描述"""

    permission: APIKeyPermission = APIKeyPermission.READ
    """权限级别，默认只读"""

    scope: APIKeyScope = APIKeyScope.ALL
    """作用范围，默认所有操作"""

    is_active: bool = True
    """是否激活"""

    created_at: datetime
    """创建时间"""

    expires_at: datetime | None = None
    """过期时间（可选，None 表示永不过期）"""

    last_used_at: datetime | None = None
    """最后使用时间（可选）"""

    usage_count: int = 0
    """使用次数统计"""

    owner: str | None = None
    """所有者标识（可选，用于多租户）"""

    metadata: dict[str, str] | None = None
    """额外元数据（可选）"""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "key_id": "550e8400-e29b-41d4-a716-446655440000",
                    "api_key": "rtk_a1b2c3d4e5f6789012345678901234567",
                    "name": "生产环境只读 Key",
                    "permission": "read",
                    "scope": "all",
                    "is_active": True,
                    "created_at": "2026-01-05T00:00:00",
                    "expires_at": None,
                    "last_used_at": None,
                    "usage_count": 0,
                    "owner": "user@example.com",
                    "metadata": {"environment": "production", "team": "data"},
                }
            ]
        },
    )

    @field_serializer("created_at", "expires_at", "last_used_at", when_used="json")
    def serialize_datetime(self, dt: datetime | None) -> str | None:
        """序列化 datetime 字段为 ISO 格式字符串"""
        return dt.isoformat() if dt else None

    def is_expired(self) -> bool:
        """检查 API Key 是否已过期"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def is_valid(self) -> bool:
        """检查 API Key 是否有效（激活且未过期）"""
        return self.is_active and not self.is_expired()

    def has_permission(self, required_permission: APIKeyPermission) -> bool:
        """检查是否有指定权限"""
        permission_order = [APIKeyPermission.READ, APIKeyPermission.WRITE, APIKeyPermission.ADMIN]
        current_level = permission_order.index(self.permission)
        required_level = permission_order.index(required_permission)
        return current_level >= required_level


class APIKeyMetadata(BaseModel):
    """
    API Key 元数据模型（不包含敏感信息）

    用于返回给客户端的 API Key 信息，不包含实际的 api_key 值。

    Attributes:
        key_id: API Key 唯一标识符
        name: API Key 名称/描述
        permission: 权限级别
        scope: 作用范围
        is_active: 是否激活
        created_at: 创建时间
        expires_at: 过期时间（可选）
        last_used_at: 最后使用时间（可选）
        usage_count: 使用次数统计
        owner: 所有者标识（可选）
        metadata: 额外元数据（可选）
    """

    key_id: str
    """API Key 唯一标识符"""

    name: str
    """API Key 名称/描述"""

    permission: APIKeyPermission
    """权限级别"""

    scope: APIKeyScope
    """作用范围"""

    is_active: bool
    """是否激活"""

    created_at: datetime
    """创建时间"""

    expires_at: datetime | None = None
    """过期时间（可选）"""

    last_used_at: datetime | None = None
    """最后使用时间（可选）"""

    usage_count: int = 0
    """使用次数统计"""

    owner: str | None = None
    """所有者标识（可选）"""

    metadata: dict[str, str] | None = None
    """额外元数据（可选）"""

    @field_serializer("created_at", "expires_at", "last_used_at", when_used="json")
    def serialize_datetime(self, dt: datetime | None) -> str | None:
        """序列化 datetime 字段为 ISO 格式字符串"""
        return dt.isoformat() if dt else None

    @classmethod
    def from_api_key(cls, api_key: APIKey) -> "APIKeyMetadata":
        """从 APIKey 创建元数据对象（移除敏感信息）"""
        return cls(
            key_id=api_key.key_id,
            name=api_key.name,
            permission=api_key.permission,
            scope=api_key.scope,
            is_active=api_key.is_active,
            created_at=api_key.created_at,
            expires_at=api_key.expires_at,
            last_used_at=api_key.last_used_at,
            usage_count=api_key.usage_count,
            owner=api_key.owner,
            metadata=api_key.metadata,
        )


class APIKeyCreateRequest(BaseModel):
    """
    创建 API Key 请求模型

    Attributes:
        name: API Key 名称/描述
        permission: 权限级别
        scope: 作用范围
        expires_in: 过期时间（秒数，可选）
        owner: 所有者标识（可选）
        metadata: 额外元数据（可选）
    """

    name: str = Field(..., min_length=1, max_length=255)
    """API Key 名称/描述"""

    permission: APIKeyPermission = APIKeyPermission.READ
    """权限级别，默认只读"""

    scope: APIKeyScope = APIKeyScope.ALL
    """作用范围，默认所有操作"""

    expires_in: int | None = Field(None, gt=0)
    """过期时间（秒数，可选），None 表示永不过期"""

    owner: str | None = Field(None, max_length=255)
    """所有者标识（可选）"""

    metadata: dict[str, str] | None = None
    """额外元数据（可选）"""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "生产环境只读 Key",
                    "permission": "read",
                    "scope": "all",
                    "expires_in": 31536000,  # 1 年
                    "owner": "user@example.com",
                    "metadata": {"environment": "production", "team": "data"},
                }
            ]
        },
    )


class APIKeyUpdateRequest(BaseModel):
    """
    更新 API Key 请求模型

    Attributes:
        name: API Key 名称/描述（可选）
        permission: 权限级别（可选）
        scope: 作用范围（可选）
        is_active: 是否激活（可选）
        metadata: 额外元数据（可选）
    """

    name: str | None = Field(None, min_length=1, max_length=255)
    """API Key 名称/描述"""

    permission: APIKeyPermission | None = None
    """权限级别"""

    scope: APIKeyScope | None = None
    """作用范围"""

    is_active: bool | None = None
    """是否激活"""

    metadata: dict[str, str] | None = None
    """额外元数据"""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "更新后的名称",
                    "permission": "write",
                    "is_active": True,
                }
            ]
        },
    )


class APIKeyAuthResult(BaseModel):
    """
    API Key 认证结果模型

    Attributes:
        success: 认证是否成功
        key_metadata: API Key 元数据（认证成功时）
        error: 错误信息（认证失败时）
    """

    success: bool
    """认证是否成功"""

    key_metadata: APIKeyMetadata | None = None
    """API Key 元数据（认证成功时）"""

    error: str | None = None
    """错误信息（认证失败时）"""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "key_metadata": {
                        "key_id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "生产环境只读 Key",
                        "permission": "read",
                        "scope": "all",
                        "is_active": True,
                        "created_at": "2026-01-05T00:00:00",
                        "expires_at": None,
                        "last_used_at": None,
                        "usage_count": 0,
                    },
                    "error": None,
                },
                {
                    "success": False,
                    "key_metadata": None,
                    "error": "Invalid API Key",
                },
            ]
        },
    )
