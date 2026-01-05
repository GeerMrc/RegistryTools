"""
API Key 认证模块

提供 API Key 生成、验证、存储和管理功能。

Copyright (c) 2026 Maric
License: MIT
"""

from registrytools.auth.generator import (
    APIKeyGenerator,
    generate_api_key,
    validate_key_format,
)
from registrytools.auth.middleware import (
    APIKeyAuthMiddleware,
    APIKeyAuthRequired,
    APIKeyExpired,
    APIKeyInsufficientPermission,
    APIKeyInvalid,
    create_auth_middleware,
)
from registrytools.auth.models import (
    APIKey,
    APIKeyAuthResult,
    APIKeyCreateRequest,
    APIKeyMetadata,
    APIKeyPermission,
    APIKeyScope,
    APIKeyUpdateRequest,
)
from registrytools.auth.storage import APIKeyStorage

__all__ = [
    # Models
    "APIKey",
    "APIKeyMetadata",
    "APIKeyPermission",
    "APIKeyScope",
    "APIKeyCreateRequest",
    "APIKeyUpdateRequest",
    "APIKeyAuthResult",
    # Generator
    "APIKeyGenerator",
    "generate_api_key",
    "validate_key_format",
    # Storage
    "APIKeyStorage",
    # Middleware
    "APIKeyAuthMiddleware",
    "APIKeyInvalid",
    "APIKeyExpired",
    "APIKeyInsufficientPermission",
    "APIKeyAuthRequired",
    "create_auth_middleware",
]
