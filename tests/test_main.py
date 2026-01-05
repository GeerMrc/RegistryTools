"""
测试 __main__.py 模块

测试 RegistryTools 的 CLI 入口功能。

Copyright (c) 2026 Maric
License: MIT
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from RegistryTools.__main__ import main


class TestMain:
    """测试 main() 函数"""

    def test_main_with_custom_data_path(self, tmp_path: Path) -> None:
        """测试使用自定义数据路径"""
        with (
            patch("RegistryTools.server.create_server") as mock_create_server,
            patch("sys.argv", ["registry-tools", "--data-path", str(tmp_path)]),
        ):
            mock_app = Mock()
            mock_app.run = Mock()
            mock_create_server.return_value = mock_app

            main()

            # 验证 create_server 被调用
            mock_create_server.assert_called_once_with(tmp_path)
            # 验证 app.run 被调用
            mock_app.run.assert_called_once()

    def test_main_with_default_data_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """测试使用默认数据路径"""
        # 修改 HOME 环境变量到临时目录
        monkeypatch.setenv("HOME", str(tmp_path))

        with (
            patch("RegistryTools.server.create_server") as mock_create_server,
            patch("sys.argv", ["registry-tools"]),
        ):
            mock_app = Mock()
            mock_app.run = Mock()
            mock_create_server.return_value = mock_app

            main()

            # 验证使用了默认路径 ~/.RegistryTools
            expected_path = tmp_path / ".RegistryTools"
            mock_create_server.assert_called_once_with(expected_path)
            # 验证数据目录被创建
            assert expected_path.exists()

    def test_main_creates_data_directory(self, tmp_path: Path) -> None:
        """测试数据目录自动创建"""
        data_path = tmp_path / "custom_data"

        with (
            patch("RegistryTools.server.create_server") as mock_create_server,
            patch("sys.argv", ["registry-tools", "--data-path", str(data_path)]),
        ):
            mock_app = Mock()
            mock_app.run = Mock()
            mock_create_server.return_value = mock_app

            main()

            # 验证数据目录被创建
            assert data_path.exists()
            assert data_path.is_dir()

    def test_main_version_argument(self, capsys: pytest.CaptureFixture[str]) -> None:
        """测试 --version 参数"""
        with patch("sys.argv", ["registry-tools", "--version"]):
            with pytest.raises(SystemExit):
                main()

        captured = capsys.readouterr()
        assert "RegistryTools" in captured.out
