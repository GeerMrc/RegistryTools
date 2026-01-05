"""
API Key 生成器

提供安全的 API Key 生成功能。

Copyright (c) 2026 Maric
License: MIT
"""

import secrets
import uuid
from datetime import datetime, timedelta

from registrytools.auth.models import (
    APIKey,
    APIKeyCreateRequest,
    APIKeyPermission,
    APIKeyScope,
)


class APIKeyGenerator:
    """
    API Key 生成器

    提供安全的 API Key 生成功能，包括密钥值生成和完整 API Key 对象创建。

    Example:
        >>> generator = APIKeyGenerator()
        >>> api_key = generator.create_api_key("My API Key", APIKeyPermission.READ)
        >>> print(api_key.api_key)
        rtk_a1b2c3d4e5f6789012345678901234567
    """

    # API Key 前缀（RegistryTools Key）
    KEY_PREFIX = "rtk"
    """API Key 前缀"""

    # API Key 随机部分的字节长度（32 字节 = 64 个 hex 字符）
    KEY_BYTES = 32
    """API Key 随机部分的字节长度"""

    def generate_key_value(self) -> str:
        """
        生成 API Key 密钥值

        生成格式为 rtk_<64-char-hex> 的密钥值，包含：
        - rtk: RegistryTools Key 前缀
        - 64 个十六进制字符（32 字节随机数据）

        Returns:
            str: API Key 密钥值（格式: rtk_<64-char-hex>）

        Example:
            >>> generator = APIKeyGenerator()
            >>> key = generator.generate_key_value()
            >>> print(key)
            rtk_a1b2c3d4e5f6789012345678901234567890123456789012345678901234
        """
        # 生成 32 字节（256 位）的随机数据
        random_bytes = secrets.token_bytes(self.KEY_BYTES)
        # 转换为十六进制字符串（64 个字符）
        hex_string = random_bytes.hex()
        # 拼接前缀
        return f"{self.KEY_PREFIX}_{hex_string}"

    def generate_key_id(self) -> str:
        """
        生成 API Key 唯一标识符

        使用 UUID v4 生成唯一标识符。

        Returns:
            str: UUID 格式的唯一标识符

        Example:
            >>> generator = APIKeyGenerator()
            >>> key_id = generator.generate_key_id()
            >>> print(key_id)
            550e8400-e29b-41d4-a716-446655440000
        """
        return str(uuid.uuid4())

    def create_api_key(
        self,
        name: str,
        permission: APIKeyPermission = APIKeyPermission.READ,
        scope: APIKeyScope = APIKeyScope.ALL,
        expires_in: int | None = None,
        owner: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> APIKey:
        """
        创建完整的 API Key 对象

        Args:
            name: API Key 名称/描述
            permission: 权限级别，默认只读
            scope: 作用范围，默认所有操作
            expires_in: 过期时间（秒数），None 表示永不过期
            owner: 所有者标识（可选）
            metadata: 额外元数据（可选）

        Returns:
            APIKey: 完整的 API Key 对象

        Example:
            >>> generator = APIKeyGenerator()
            >>> api_key = generator.create_api_key(
            ...     name="生产环境只读 Key",
            ...     permission=APIKeyPermission.READ,
            ...     expires_in=31536000  # 1 年
            ... )
            >>> print(api_key.api_key)
            rtk_a1b2c3d4e5f6789012345678901234567890123456789012345678901234
        """
        # 计算过期时间
        expires_at = None
        if expires_in is not None:
            expires_at = datetime.now() + timedelta(seconds=expires_in)

        # 创建 API Key 对象
        return APIKey(
            key_id=self.generate_key_id(),
            api_key=self.generate_key_value(),
            name=name,
            permission=permission,
            scope=scope,
            is_active=True,
            created_at=datetime.now(),
            expires_at=expires_at,
            last_used_at=None,
            usage_count=0,
            owner=owner,
            metadata=metadata,
        )

    def create_api_key_from_request(self, request: APIKeyCreateRequest) -> APIKey:
        """
        从创建请求创建 API Key 对象

        Args:
            request: API Key 创建请求

        Returns:
            APIKey: 完整的 API Key 对象

        Example:
            >>> generator = APIKeyGenerator()
            >>> request = APIKeyCreateRequest(
            ...     name="生产环境只读 Key",
            ...     permission=APIKeyPermission.READ
            ... )
            >>> api_key = generator.create_api_key_from_request(request)
        """
        return self.create_api_key(
            name=request.name,
            permission=request.permission,
            scope=request.scope,
            expires_in=request.expires_in,
            owner=request.owner,
            metadata=request.metadata,
        )

    def validate_key_format(self, api_key: str) -> bool:
        """
        验证 API Key 格式

        检查 API Key 是否符合 rtk_<64-char-hex> 格式。

        Args:
            api_key: API Key 字符串

        Returns:
            bool: 格式是否有效

        Example:
            >>> generator = APIKeyGenerator()
            >>> generator.validate_key_format("rtk_a1b2c3d4...")
            True
            >>> generator.validate_key_format("invalid_key")
            False
        """
        # 检查前缀
        if not api_key.startswith(f"{self.KEY_PREFIX}_"):
            return False

        # 提取十六进制部分
        hex_part = api_key[len(self.KEY_PREFIX) + 1 :]

        # 检查长度（64 个 hex 字符 = 32 字节）
        if len(hex_part) != self.KEY_BYTES * 2:
            return False

        # 检查是否为有效的十六进制字符串
        try:
            bytes.fromhex(hex_part)
            return True
        except ValueError:
            return False


# 默认实例
_default_generator = APIKeyGenerator()


def generate_api_key(
    name: str,
    permission: APIKeyPermission = APIKeyPermission.READ,
    scope: APIKeyScope = APIKeyScope.ALL,
    expires_in: int | None = None,
    owner: str | None = None,
    metadata: dict[str, str] | None = None,
) -> APIKey:
    """
    生成 API Key 的便捷函数

    Args:
        name: API Key 名称/描述
        permission: 权限级别，默认只读
        scope: 作用范围，默认所有操作
        expires_in: 过期时间（秒数），None 表示永不过期
        owner: 所有者标识（可选）
        metadata: 额外元数据（可选）

    Returns:
        APIKey: 完整的 API Key 对象

    Example:
        >>> api_key = generate_api_key("My Key", APIKeyPermission.READ)
        >>> print(api_key.api_key)
        rtk_a1b2c3d4e5f6789012345678901234567890123456789012345678901234
    """
    return _default_generator.create_api_key(
        name=name,
        permission=permission,
        scope=scope,
        expires_in=expires_in,
        owner=owner,
        metadata=metadata,
    )


def validate_key_format(api_key: str) -> bool:
    """
    验证 API Key 格式的便捷函数

    Args:
        api_key: API Key 字符串

    Returns:
        bool: 格式是否有效
    """
    return _default_generator.validate_key_format(api_key)
