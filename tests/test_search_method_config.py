"""
测试搜索引擎配置功能

测试 REGISTRYTOOLS_SEARCH_METHOD 环境变量的功能。

Copyright (c) 2026 Maric
License: MIT
"""

import os

import pytest

from registrytools.registry.models import SearchMethod
from registrytools.server import get_default_search_method


class TestGetDefaultSearchMethod:
    """测试 get_default_search_method() 函数"""

    def test_default_when_not_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试环境变量未设置时使用默认值"""
        monkeypatch.delenv("REGISTRYTOOLS_SEARCH_METHOD", raising=False)

        result = get_default_search_method()

        assert result == SearchMethod.BM25

    def test_custom_valid_method_regex(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试设置有效的搜索方法 - regex"""
        monkeypatch.setenv("REGISTRYTOOLS_SEARCH_METHOD", "regex")

        result = get_default_search_method()

        assert result == SearchMethod.REGEX

    def test_custom_valid_method_bm25(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试设置有效的搜索方法 - bm25"""
        monkeypatch.setenv("REGISTRYTOOLS_SEARCH_METHOD", "bm25")

        result = get_default_search_method()

        assert result == SearchMethod.BM25

    def test_custom_valid_method_embedding(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试设置有效的搜索方法 - embedding"""
        monkeypatch.setenv("REGISTRYTOOLS_SEARCH_METHOD", "embedding")

        result = get_default_search_method()

        assert result == SearchMethod.EMBEDDING

    def test_custom_invalid_method_fallback(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """测试设置无效方法时回退到默认值"""
        monkeypatch.setenv("REGISTRYTOOLS_SEARCH_METHOD", "invalid_method")

        with caplog.at_level("WARNING"):
            result = get_default_search_method()

        assert result == SearchMethod.BM25
        assert "无效的搜索方法" in caplog.text

    def test_case_insensitive(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试大小写不敏感"""
        monkeypatch.setenv("REGISTRYTOOLS_SEARCH_METHOD", "EMBEDDING")

        result = get_default_search_method()

        assert result == SearchMethod.EMBEDDING

    def test_whitespace_trimming(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试前后空格被修剪"""
        monkeypatch.setenv("REGISTRYTOOLS_SEARCH_METHOD", "  bm25  ")

        result = get_default_search_method()

        assert result == SearchMethod.BM25

    def test_mixed_case(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试混合大小写"""
        monkeypatch.setenv("REGISTRYTOOLS_SEARCH_METHOD", "ReGeX")

        result = get_default_search_method()

        assert result == SearchMethod.REGEX

    @pytest.mark.parametrize(
        "method",
        ["regex", "bm25", "embedding"],
    )
    def test_all_valid_methods(
        self, monkeypatch: pytest.MonkeyPatch, method: str
    ) -> None:
        """测试所有有效方法"""
        monkeypatch.setenv("REGISTRYTOOLS_SEARCH_METHOD", method)

        result = get_default_search_method()

        assert result.value == method

    def test_empty_string_uses_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """测试空字符串使用默认值"""
        monkeypatch.setenv("REGISTRYTOOLS_SEARCH_METHOD", "")

        result = get_default_search_method()

        assert result == SearchMethod.BM25

    def test_whitespace_only_uses_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """测试仅空格使用默认值"""
        monkeypatch.setenv("REGISTRYTOOLS_SEARCH_METHOD", "   ")

        result = get_default_search_method()

        assert result == SearchMethod.BM25
