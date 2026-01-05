"""
API Key 认证中间件

提供 API Key 认证和授权功能。

Copyright (c) 2026 Maric
License: MIT
"""

from registrytools.auth.models import (
    APIKeyAuthResult,
    APIKeyMetadata,
    APIKeyPermission,
)
from registrytools.auth.storage import APIKeyStorage


class APIKeyAuthRequired(Exception):
    """API Key 认证必需异常"""

    def __init__(self, message: str = "API Key is required") -> None:
        self.message = message
        super().__init__(self.message)


class APIKeyInvalid(Exception):
    """API Key 无效异常"""

    def __init__(self, message: str = "Invalid API Key") -> None:
        self.message = message
        super().__init__(self.message)


class APIKeyExpired(Exception):
    """API Key 过期异常"""

    def __init__(self, message: str = "API Key has expired") -> None:
        self.message = message
        super().__init__(self.message)


class APIKeyInsufficientPermission(Exception):
    """API Key 权限不足异常"""

    def __init__(self, message: str = "Insufficient permissions") -> None:
        self.message = message
        super().__init__(self.message)


class APIKeyAuthMiddleware:
    """
    API Key 认证中间件

    提供 API Key 认证和授权功能，支持从 HTTP 请求头中提取 API Key 并验证。

    Example:
        >>> storage = APIKeyStorage("~/.RegistryTools/api_keys.db")
        >>> middleware = APIKeyAuthMiddleware(storage)
        >>> result = middleware.authenticate_from_header("Authorization: Bearer rtk_xxx")
        >>> if result.success:
        ...     print(f"Authenticated as {result.key_metadata.name}")
    """

    # 默认 HTTP Header 名称
    DEFAULT_HEADER_NAME = "X-API-Key"
    """默认 API Key HTTP Header 名称"""

    # Bearer Token 格式前缀
    BEARER_PREFIX = "Bearer"
    """Bearer Token 前缀"""

    def __init__(self, storage: APIKeyStorage, header_name: str | None = None) -> None:
        """
        初始化认证中间件

        Args:
            storage: API Key 存储层
            header_name: API Key HTTP Header 名称，默认 X-API-Key
        """
        self._storage = storage
        self._header_name = header_name or self.DEFAULT_HEADER_NAME

    @property
    def header_name(self) -> str:
        """获取 HTTP Header 名称"""
        return self._header_name

    def authenticate(
        self, api_key: str, required_permission: APIKeyPermission | None = None
    ) -> APIKeyAuthResult:
        """
        验证 API Key

        Args:
            api_key: API Key 密钥值
            required_permission: 需要的权限级别（可选）

        Returns:
            APIKeyAuthResult: 认证结果

        Example:
            >>> result = middleware.authenticate("rtk_a1b2c3d4...")
            >>> if result.success:
            ...     print(f"Authenticated: {result.key_metadata.name}")
        """
        # 验证 API Key 格式
        from registrytools.auth.generator import validate_key_format

        if not validate_key_format(api_key):
            return APIKeyAuthResult(
                success=False,
                key_metadata=None,
                error="Invalid API Key format",
            )

        # 从存储中获取 API Key
        key_obj = self._storage.get_by_api_key(api_key)
        if not key_obj:
            return APIKeyAuthResult(
                success=False,
                key_metadata=None,
                error="API Key not found",
            )

        # 检查 API Key 是否有效
        if not key_obj.is_valid():
            if key_obj.is_expired():
                return APIKeyAuthResult(
                    success=False,
                    key_metadata=None,
                    error="API Key has expired",
                )
            if not key_obj.is_active:
                return APIKeyAuthResult(
                    success=False,
                    key_metadata=None,
                    error="API Key is inactive",
                )

        # 检查权限
        if required_permission is not None and not key_obj.has_permission(required_permission):
            return APIKeyAuthResult(
                success=False,
                key_metadata=None,
                error=f"Insufficient permissions (required: {required_permission.value})",
            )

        # 认证成功，记录使用
        self._storage.record_usage(api_key)

        return APIKeyAuthResult(
            success=True,
            key_metadata=APIKeyMetadata.from_api_key(key_obj),
            error=None,
        )

    def authenticate_or_raise(
        self,
        api_key: str,
        required_permission: APIKeyPermission | None = None,
    ) -> APIKeyMetadata:
        """
        验证 API Key，失败时抛出异常

        Args:
            api_key: API Key 密钥值
            required_permission: 需要的权限级别（可选）

        Returns:
            APIKeyMetadata: API Key 元数据

        Raises:
            APIKeyInvalid: API Key 无效
            APIKeyExpired: API Key 过期
            APIKeyInsufficientPermission: 权限不足
        """
        result = self.authenticate(api_key, required_permission)

        if not result.success:
            if result.error == "API Key not found" or "Invalid API Key format" in result.error:
                raise APIKeyInvalid(result.error or "Invalid API Key")
            elif "expired" in result.error:
                raise APIKeyExpired(result.error)
            elif "Insufficient permissions" in result.error:
                raise APIKeyInsufficientPermission(result.error)
            else:
                raise APIKeyInvalid(result.error or "Authentication failed")

        # result.success 为 True，key_metadata 不为 None
        return result.key_metadata  # type: ignore

    def authenticate_from_header(
        self,
        header_value: str | None,
        required_permission: APIKeyPermission | None = None,
    ) -> APIKeyAuthResult:
        """
        从 HTTP Header 值验证 API Key

        支持两种格式：
        1. 直接格式: `rtk_xxx`
        2. Bearer 格式: `Bearer rtk_xxx`

        Args:
            header_value: HTTP Header 值
            required_permission: 需要的权限级别（可选）

        Returns:
            APIKeyAuthResult: 认证结果

        Example:
            >>> result = middleware.authenticate_from_header("Bearer rtk_a1b2c3d4...")
            >>> if result.success:
            ...     print(f"Authenticated: {result.key_metadata.name}")
        """
        if not header_value:
            return APIKeyAuthResult(
                success=False,
                key_metadata=None,
                error="API Key is required",
            )

        # 提取 API Key 值
        api_key = header_value.strip()

        # 检查 Bearer 格式
        if api_key.startswith(f"{self.BEARER_PREFIX} "):
            api_key = api_key[len(self.BEARER_PREFIX) :].strip()

        return self.authenticate(api_key, required_permission)

    def authenticate_from_headers(
        self,
        headers: dict[str, str],
        required_permission: APIKeyPermission | None = None,
    ) -> APIKeyAuthResult:
        """
        从 HTTP Headers 字典验证 API Key

        Args:
            headers: HTTP Headers 字典
            required_permission: 需要的权限级别（可选）

        Returns:
            APIKeyAuthResult: 认证结果

        Example:
            >>> headers = {"X-API-Key": "rtk_a1b2c3d4..."}
            >>> result = middleware.authenticate_from_headers(headers)
            >>> if result.success:
            ...     print(f"Authenticated: {result.key_metadata.name}")
        """
        header_value = headers.get(self._header_name)
        return self.authenticate_from_header(header_value, required_permission)

    def require_permission(
        self,
        api_key: str,
        required_permission: APIKeyPermission,
    ) -> APIKeyMetadata:
        """
        要求指定权限级别的认证

        Args:
            api_key: API Key 密钥值
            required_permission: 需要的权限级别

        Returns:
            APIKeyMetadata: API Key 元数据

        Raises:
            APIKeyInvalid: API Key 无效
            APIKeyExpired: API Key 过期
            APIKeyInsufficientPermission: 权限不足
        """
        return self.authenticate_or_raise(api_key, required_permission)

    def is_read_operation(self, operation: str) -> bool:
        """
        判断是否为只读操作

        Args:
            operation: 操作名称

        Returns:
            bool: 是否为只读操作
        """
        read_operations = [
            "search_tools",
            "get_tool_definition",
            "list_tools_by_category",
            "get_stats",
            "get_categories",
        ]
        return operation in read_operations

    def get_required_permission(self, operation: str) -> APIKeyPermission:
        """
        根据操作获取需要的权限级别

        Args:
            operation: 操作名称

        Returns:
            APIKeyPermission: 需要的权限级别
        """
        if self.is_read_operation(operation):
            return APIKeyPermission.READ
        else:
            return APIKeyPermission.WRITE


# 便捷函数


def create_auth_middleware(
    storage_path: str,
    header_name: str | None = None,
) -> APIKeyAuthMiddleware:
    """
    创建认证中间件的便捷函数

    Args:
        storage_path: API Key 存储路径
        header_name: HTTP Header 名称，默认 X-API-Key

    Returns:
        APIKeyAuthMiddleware: 认证中间件实例
    """
    storage = APIKeyStorage(storage_path)
    return APIKeyAuthMiddleware(storage, header_name)
