"""
测试服务器描述功能

测试 REGISTRYTOOLS_DESCRIPTION 环境变量的功能。

Copyright (c) 2026 Maric
License: MIT
"""

import pytest

from registrytools.server import get_server_description


class TestGetServerDescription:
    """测试 get_server_description() 函数"""

    def test_get_server_description_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试默认描述（环境变量未设置）"""
        # 确保环境变量未设置
        monkeypatch.delenv("REGISTRYTOOLS_DESCRIPTION", raising=False)

        result = get_server_description()

        assert "RegistryTools" in result
        assert "MCP 工具注册表服务器" in result
        assert "Regex" in result or "BM25" in result
        assert "工具注册与元数据管理" in result

    def test_get_server_description_custom(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试自定义描述"""
        monkeypatch.setenv("REGISTRYTOOLS_DESCRIPTION", "我的自定义工具服务器")

        result = get_server_description()

        assert result == "我的自定义工具服务器"

    def test_get_server_description_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试空字符串回退到默认"""
        monkeypatch.setenv("REGISTRYTOOLS_DESCRIPTION", "")

        result = get_server_description()

        assert "RegistryTools" in result
        assert "MCP 工具注册表服务器" in result

    def test_get_server_description_whitespace(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试纯空格回退到默认"""
        monkeypatch.setenv("REGISTRYTOOLS_DESCRIPTION", "   ")

        result = get_server_description()

        assert "RegistryTools" in result
        assert "MCP 工具注册表服务器" in result

    def test_get_server_description_with_leading_trailing_spaces(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """测试带前后空格的自定义描述会被修剪"""
        monkeypatch.setenv("REGISTRYTOOLS_DESCRIPTION", "  我的工具服务器  ")

        result = get_server_description()

        # 前后空格被修剪
        assert result == "我的工具服务器"

    def test_get_server_description_multiline(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试多行描述"""
        custom_desc = "第一行\n第二行\n第三行"
        monkeypatch.setenv("REGISTRYTOOLS_DESCRIPTION", custom_desc)

        result = get_server_description()

        assert result == custom_desc
        assert "\n" in result

    def test_get_server_description_default_has_all_features(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """测试默认描述包含所有核心功能"""
        monkeypatch.delenv("REGISTRYTOOLS_DESCRIPTION", raising=False)

        result = get_server_description()

        # 验证包含所有核心功能
        assert "工具注册与元数据管理" in result
        assert "多算法搜索" in result
        assert "分类浏览" in result
        assert "统计信息" in result
        assert "动态工具注册 API" in result
        # 验证包含搜索算法
        assert "Regex" in result
        assert "BM25" in result
        assert "Embedding" in result
        # 验证包含客户端示例
        assert "Claude Desktop" in result
        assert "Cursor" in result
        assert "DeepThinking Agent" in result
