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

        assert "统一的 MCP 工具注册与搜索服务" in result
        assert "发现和筛选可用工具" in result
        assert "任务执行工具调用准确性" in result
        assert "复杂任务工具调用效率" in result

    def test_get_server_description_custom(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试自定义描述"""
        monkeypatch.setenv("REGISTRYTOOLS_DESCRIPTION", "我的自定义工具服务器")

        result = get_server_description()

        assert result == "我的自定义工具服务器"

    def test_get_server_description_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试空字符串回退到默认"""
        monkeypatch.setenv("REGISTRYTOOLS_DESCRIPTION", "")

        result = get_server_description()

        assert "统一的 MCP 工具注册与搜索服务" in result
        assert "发现和筛选可用工具" in result

    def test_get_server_description_whitespace(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试纯空格回退到默认"""
        monkeypatch.setenv("REGISTRYTOOLS_DESCRIPTION", "   ")

        result = get_server_description()

        assert "统一的 MCP 工具注册与搜索服务" in result
        assert "发现和筛选可用工具" in result

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

        # 验证包含新的默认描述的关键内容
        assert "统一的 MCP 工具注册与搜索服务" in result
        assert "发现和筛选可用工具" in result
        assert "任务执行工具调用准确性" in result
        assert "复杂任务工具调用效率" in result
