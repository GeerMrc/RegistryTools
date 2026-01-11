"""
API Key 认证模块单元测试 (Phase 15)

测试 API Key 生成、存储和认证功能。

Copyright (c) 2026 Maric
License: MIT
"""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from registrytools.auth import (
    APIKey,
    APIKeyAuthMiddleware,
    APIKeyGenerator,
    APIKeyMetadata,
    APIKeyPermission,
    APIKeyScope,
    APIKeyStorage,
    APIKeyUpdateRequest,
    generate_api_key,
    validate_key_format,
)
from registrytools.auth.middleware import (
    APIKeyExpired,
    APIKeyInsufficientPermission,
    APIKeyInvalid,
)

# ============================================================
# API Key 生成器测试
# ============================================================


class TestAPIKeyGenerator:
    """测试 API Key 生成器"""

    def test_generate_key_value_format(self):
        """测试生成的 API Key 格式正确"""
        generator = APIKeyGenerator()
        key_value = generator.generate_key_value()

        # 检查前缀
        assert key_value.startswith("rtk_")

        # 检查长度 (rtk_ + 64 个 hex 字符)
        assert len(key_value) == 4 + 64

        # 验证格式
        assert validate_key_format(key_value)

    def test_generate_key_id_unique(self):
        """测试生成的 Key ID 是唯一的"""
        generator = APIKeyGenerator()
        key_id_1 = generator.generate_key_id()
        key_id_2 = generator.generate_key_id()

        assert key_id_1 != key_id_2

    def test_create_api_key_default_values(self):
        """测试创建 API Key 的默认值"""
        generator = APIKeyGenerator()
        api_key = generator.create_api_key("Test Key")

        assert api_key.name == "Test Key"
        assert api_key.permission == APIKeyPermission.READ
        assert api_key.scope == APIKeyScope.ALL
        assert api_key.is_active is True
        assert api_key.usage_count == 0
        assert api_key.expires_at is None

    def test_create_api_key_with_expiration(self):
        """测试创建有过期时间的 API Key"""
        generator = APIKeyGenerator()
        expires_in = 3600  # 1 小时
        api_key = generator.create_api_key("Test Key", expires_in=expires_in)

        assert api_key.expires_at is not None
        expected_expiry = datetime.now() + timedelta(seconds=expires_in)
        # 允许 1 秒误差
        assert abs((api_key.expires_at - expected_expiry).total_seconds()) < 1

    def test_create_api_key_with_permission(self):
        """测试创建不同权限级别的 API Key"""
        generator = APIKeyGenerator()

        read_key = generator.create_api_key("Read Key", permission=APIKeyPermission.READ)
        write_key = generator.create_api_key("Write Key", permission=APIKeyPermission.WRITE)
        admin_key = generator.create_api_key("Admin Key", permission=APIKeyPermission.ADMIN)

        assert read_key.permission == APIKeyPermission.READ
        assert write_key.permission == APIKeyPermission.WRITE
        assert admin_key.permission == APIKeyPermission.ADMIN

    def test_validate_key_format_valid(self):
        """测试验证有效的 API Key 格式"""
        assert validate_key_format("rtk_" + "a" * 64)
        assert validate_key_format("rtk_" + "0" * 64)

    def test_validate_key_format_invalid_prefix(self):
        """测试验证无效前缀的 API Key"""
        assert not validate_key_format("invalid_" + "a" * 64)
        assert not validate_key_format("rtk" + "a" * 64)  # 缺少下划线

    def test_validate_key_format_invalid_length(self):
        """测试验证无效长度的 API Key"""
        assert not validate_key_format("rtk_" + "a" * 63)
        assert not validate_key_format("rtk_" + "a" * 65)

    def test_validate_key_format_invalid_hex(self):
        """测试验证无效十六进制的 API Key"""
        assert not validate_key_format("rtk_" + "g" * 64)  # g 不是有效的十六进制字符


class TestAPIKeyModel:
    """测试 API Key 数据模型"""

    def test_is_expired_no_expiry(self):
        """测试永不过期的 API Key"""
        api_key = APIKey(
            key_id="test-id",
            api_key="rtk_" + "a" * 64,
            name="Test",
            created_at=datetime.now(),
            expires_at=None,
        )
        assert not api_key.is_expired()

    def test_is_expired_not_expired(self):
        """测试未过期的 API Key"""
        api_key = APIKey(
            key_id="test-id",
            api_key="rtk_" + "a" * 64,
            name="Test",
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=1),
        )
        assert not api_key.is_expired()

    def test_is_expired_expired(self):
        """测试已过期的 API Key"""
        api_key = APIKey(
            key_id="test-id",
            api_key="rtk_" + "a" * 64,
            name="Test",
            created_at=datetime.now(),
            expires_at=datetime.now() - timedelta(hours=1),
        )
        assert api_key.is_expired()

    def test_is_valid_active_and_not_expired(self):
        """测试激活且未过期的 API Key"""
        api_key = APIKey(
            key_id="test-id",
            api_key="rtk_" + "a" * 64,
            name="Test",
            is_active=True,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=1),
        )
        assert api_key.is_valid()

    def test_is_valid_inactive(self):
        """测试未激活的 API Key"""
        api_key = APIKey(
            key_id="test-id",
            api_key="rtk_" + "a" * 64,
            name="Test",
            is_active=False,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=1),
        )
        assert not api_key.is_valid()

    def test_has_permission_read(self):
        """测试只读权限"""
        api_key = APIKey(
            key_id="test-id",
            api_key="rtk_" + "a" * 64,
            name="Test",
            permission=APIKeyPermission.READ,
            created_at=datetime.now(),
        )
        assert api_key.has_permission(APIKeyPermission.READ)
        assert not api_key.has_permission(APIKeyPermission.WRITE)
        assert not api_key.has_permission(APIKeyPermission.ADMIN)

    def test_has_permission_write(self):
        """测试读写权限"""
        api_key = APIKey(
            key_id="test-id",
            api_key="rtk_" + "a" * 64,
            name="Test",
            permission=APIKeyPermission.WRITE,
            created_at=datetime.now(),
        )
        assert api_key.has_permission(APIKeyPermission.READ)
        assert api_key.has_permission(APIKeyPermission.WRITE)
        assert not api_key.has_permission(APIKeyPermission.ADMIN)

    def test_has_permission_admin(self):
        """测试管理员权限"""
        api_key = APIKey(
            key_id="test-id",
            api_key="rtk_" + "a" * 64,
            name="Test",
            permission=APIKeyPermission.ADMIN,
            created_at=datetime.now(),
        )
        assert api_key.has_permission(APIKeyPermission.READ)
        assert api_key.has_permission(APIKeyPermission.WRITE)
        assert api_key.has_permission(APIKeyPermission.ADMIN)

    def test_metadata_from_api_key(self):
        """测试从 API Key 创建元数据"""
        api_key = APIKey(
            key_id="test-id",
            api_key="rtk_" + "a" * 64,
            name="Test",
            permission=APIKeyPermission.WRITE,
            created_at=datetime.now(),
        )
        metadata = APIKeyMetadata.from_api_key(api_key)

        assert metadata.key_id == api_key.key_id
        assert metadata.name == api_key.name
        assert metadata.permission == api_key.permission
        # 元数据不应包含实际的 api_key 值
        assert not hasattr(metadata, "api_key") or not getattr(metadata, "api_key", None)


# ============================================================
# API Key 存储测试
# ============================================================


class TestAPIKeyStorage:
    """测试 API Key 存储层"""

    @pytest.fixture
    def temp_db_path(self):
        """创建临时数据库文件路径"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            yield Path(f.name)

    @pytest.fixture
    def storage(self, temp_db_path):
        """创建存储实例"""
        return APIKeyStorage(temp_db_path)

    def test_save_and_get_by_api_key(self, storage):
        """测试保存和通过 API Key 获取"""
        api_key = generate_api_key("Test Key")
        storage.save(api_key)

        retrieved = storage.get_by_api_key(api_key.api_key)
        assert retrieved is not None
        assert retrieved.key_id == api_key.key_id
        assert retrieved.api_key == api_key.api_key
        assert retrieved.name == api_key.name

    def test_get_by_api_key_not_found(self, storage):
        """测试获取不存在的 API Key"""
        retrieved = storage.get_by_api_key("rtk_" + "a" * 64)
        assert retrieved is None

    def test_save_and_get_by_key_id(self, storage):
        """测试保存和通过 Key ID 获取"""
        api_key = generate_api_key("Test Key")
        storage.save(api_key)

        retrieved = storage.get_by_key_id(api_key.key_id)
        assert retrieved is not None
        assert retrieved.key_id == api_key.key_id

    def test_list_all(self, storage):
        """测试列出所有 API Key"""
        api_key_1 = generate_api_key("Key 1")
        api_key_2 = generate_api_key("Key 2")
        storage.save(api_key_1)
        storage.save(api_key_2)

        all_keys = storage.list_all()
        assert len(all_keys) == 2
        key_ids = [k.key_id for k in all_keys]
        assert api_key_1.key_id in key_ids
        assert api_key_2.key_id in key_ids

    def test_list_all_by_owner(self, storage):
        """测试按所有者列出 API Key"""
        api_key_1 = generate_api_key("Key 1", owner="user1")
        api_key_2 = generate_api_key("Key 2", owner="user2")
        storage.save(api_key_1)
        storage.save(api_key_2)

        user1_keys = storage.list_all(owner="user1")
        assert len(user1_keys) == 1
        assert user1_keys[0].key_id == api_key_1.key_id

    def test_delete(self, storage):
        """测试删除 API Key"""
        api_key = generate_api_key("Test Key")
        storage.save(api_key)

        deleted = storage.delete(api_key.key_id)
        assert deleted is True

        retrieved = storage.get_by_key_id(api_key.key_id)
        assert retrieved is None

    def test_delete_not_found(self, storage):
        """测试删除不存在的 API Key"""
        deleted = storage.delete("non-existent-id")
        assert deleted is False

    def test_update(self, storage):
        """测试更新 API Key"""
        api_key = generate_api_key("Test Key")
        storage.save(api_key)

        update_request = APIKeyUpdateRequest(
            name="Updated Name",
            permission=APIKeyPermission.WRITE,
        )
        updated = storage.update(api_key.key_id, update_request)

        assert updated is not None
        assert updated.name == "Updated Name"
        assert updated.permission == APIKeyPermission.WRITE

    def test_record_usage(self, storage):
        """测试记录使用"""
        api_key = generate_api_key("Test Key")
        storage.save(api_key)

        storage.record_usage(api_key.api_key)

        retrieved = storage.get_by_api_key(api_key.api_key)
        assert retrieved is not None
        assert retrieved.usage_count == 1
        assert retrieved.last_used_at is not None

    def test_count(self, storage):
        """测试统计 API Key 数量"""
        assert storage.count() == 0

        storage.save(generate_api_key("Key 1"))
        assert storage.count() == 1

        storage.save(generate_api_key("Key 2"))
        assert storage.count() == 2

    def test_count_by_owner(self, storage):
        """测试按所有者统计"""
        storage.save(generate_api_key("Key 1", owner="user1"))
        storage.save(generate_api_key("Key 2", owner="user1"))
        storage.save(generate_api_key("Key 3", owner="user2"))

        assert storage.count(owner="user1") == 2
        assert storage.count(owner="user2") == 1

    def test_cleanup_expired(self, storage):
        """测试清理过期的 API Key"""
        # 创建一个已过期的 API Key
        expired_key = generate_api_key("Expired Key")
        expired_key.expires_at = datetime.now() - timedelta(days=1)
        storage.save(expired_key)

        # 创建一个未过期的 API Key
        valid_key = generate_api_key("Valid Key")
        storage.save(valid_key)

        # 清理过期 Key
        deleted_count = storage.cleanup_expired()
        assert deleted_count == 1

        # 验证只有过期的被删除
        assert storage.get_by_key_id(expired_key.key_id) is None
        assert storage.get_by_key_id(valid_key.key_id) is not None


# ============================================================
# API Key 认证中间件测试
# ============================================================


class TestAPIKeyAuthMiddleware:
    """测试 API Key 认证中间件"""

    @pytest.fixture
    def temp_db_path(self):
        """创建临时数据库文件路径"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            yield Path(f.name)

    @pytest.fixture
    def middleware(self, temp_db_path):
        """创建认证中间件实例"""
        storage = APIKeyStorage(temp_db_path)
        return APIKeyAuthMiddleware(storage)

    @pytest.fixture
    def valid_api_key(self, middleware):
        """创建有效的 API Key"""
        api_key = generate_api_key("Valid Key", permission=APIKeyPermission.READ)
        middleware._storage.save(api_key)
        return api_key

    def test_authenticate_success(self, middleware, valid_api_key):
        """测试认证成功"""
        result = middleware.authenticate(valid_api_key.api_key)

        assert result.success is True
        assert result.key_metadata is not None
        assert result.key_metadata.key_id == valid_api_key.key_id
        assert result.error is None

    def test_authenticate_invalid_format(self, middleware):
        """测试认证失败 - 无效格式"""
        result = middleware.authenticate("invalid_key")

        assert result.success is False
        assert result.key_metadata is None
        assert "Invalid API Key format" in result.error

    def test_authenticate_not_found(self, middleware):
        """测试认证失败 - 不存在"""
        result = middleware.authenticate("rtk_" + "a" * 64)

        assert result.success is False
        assert result.key_metadata is None
        assert "not found" in result.error

    def test_authenticate_expired(self, middleware):
        """测试认证失败 - 已过期"""
        api_key = generate_api_key("Expired Key")
        api_key.expires_at = datetime.now() - timedelta(hours=1)
        middleware._storage.save(api_key)

        result = middleware.authenticate(api_key.api_key)

        assert result.success is False
        assert "expired" in result.error

    def test_authenticate_inactive(self, middleware):
        """测试认证失败 - 未激活"""
        api_key = generate_api_key("Inactive Key")
        api_key.is_active = False
        middleware._storage.save(api_key)

        result = middleware.authenticate(api_key.api_key)

        assert result.success is False
        assert "inactive" in result.error

    def test_authenticate_with_permission_success(self, middleware):
        """测试带权限检查的认证 - 成功"""
        api_key = generate_api_key("Write Key", permission=APIKeyPermission.WRITE)
        middleware._storage.save(api_key)

        result = middleware.authenticate(api_key.api_key, APIKeyPermission.READ)

        assert result.success is True

    def test_authenticate_with_permission_insufficient(self, middleware):
        """测试带权限检查的认证 - 权限不足"""
        api_key = generate_api_key("Read Key", permission=APIKeyPermission.READ)
        middleware._storage.save(api_key)

        result = middleware.authenticate(api_key.api_key, APIKeyPermission.WRITE)

        assert result.success is False
        assert "Insufficient permissions" in result.error

    def test_authenticate_or_raise_success(self, middleware, valid_api_key):
        """测试认证成功 - 抛出异常版本"""
        metadata = middleware.authenticate_or_raise(valid_api_key.api_key)

        assert metadata.key_id == valid_api_key.key_id

    def test_authenticate_or_raise_invalid(self, middleware):
        """测试认证失败 - 抛出异常版本"""
        with pytest.raises(APIKeyInvalid):
            middleware.authenticate_or_raise("invalid_key")

    def test_authenticate_or_raise_expired(self, middleware):
        """测试认证失败 - 已过期"""
        api_key = generate_api_key("Expired Key")
        api_key.expires_at = datetime.now() - timedelta(hours=1)
        middleware._storage.save(api_key)

        with pytest.raises(APIKeyExpired):
            middleware.authenticate_or_raise(api_key.api_key)

    def test_authenticate_or_raise_insufficient_permission(self, middleware):
        """测试认证失败 - 权限不足"""
        api_key = generate_api_key("Read Key", permission=APIKeyPermission.READ)
        middleware._storage.save(api_key)

        with pytest.raises(APIKeyInsufficientPermission):
            middleware.authenticate_or_raise(api_key.api_key, APIKeyPermission.WRITE)

    def test_authenticate_from_header_direct(self, middleware, valid_api_key):
        """测试从 Header 直接格式认证"""
        result = middleware.authenticate_from_header(valid_api_key.api_key)

        assert result.success is True

    def test_authenticate_from_header_bearer(self, middleware, valid_api_key):
        """测试从 Header Bearer 格式认证"""
        result = middleware.authenticate_from_header(f"Bearer {valid_api_key.api_key}")

        assert result.success is True

    def test_authenticate_from_header_missing(self, middleware):
        """测试从 Header 缺失认证"""
        result = middleware.authenticate_from_header(None)

        assert result.success is False
        assert "required" in result.error

    def test_authenticate_from_headers(self, middleware, valid_api_key):
        """测试从 Headers 字典认证"""
        headers = {"X-API-Key": valid_api_key.api_key}
        result = middleware.authenticate_from_headers(headers)

        assert result.success is True

    def test_header_name_property(self):
        """测试自定义 Header 名称"""
        storage = APIKeyStorage(":memory:")
        middleware = APIKeyAuthMiddleware(storage, header_name="Custom-Header")

        assert middleware.header_name == "Custom-Header"


# ============================================================
# 便捷函数测试
# ============================================================


class TestConvenienceFunctions:
    """测试便捷函数"""

    def test_generate_api_key(self):
        """测试生成 API Key 便捷函数"""
        api_key = generate_api_key("Test")

        assert api_key.name == "Test"
        assert api_key.permission == APIKeyPermission.READ
        assert validate_key_format(api_key.api_key)

    def test_generate_api_key_with_permission(self):
        """测试生成带权限的 API Key"""
        api_key = generate_api_key("Test", permission=APIKeyPermission.ADMIN)

        assert api_key.permission == APIKeyPermission.ADMIN

    def test_validate_key_format_convenience(self):
        """测试验证格式便捷函数"""
        assert validate_key_format("rtk_" + "a" * 64)
        assert not validate_key_format("invalid")
