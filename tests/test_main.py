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


class TestMainHttpTransport:
    """测试 HTTP 传输协议支持"""

    def test_main_with_http_transport_default_params(self, tmp_path: Path) -> None:
        """测试 HTTP 传输使用默认参数"""
        with (
            patch("RegistryTools.server.create_server") as mock_create_server,
            patch(
                "sys.argv", ["registry-tools", "--transport", "http", "--data-path", str(tmp_path)]
            ),
        ):
            mock_app = Mock()
            mock_app.run = Mock()
            mock_create_server.return_value = mock_app

            main()

            # 验证 HTTP 传输被正确调用 (使用默认参数)
            mock_app.run.assert_called_once_with(
                transport="http", host="127.0.0.1", port=8000, path="/"
            )

    def test_main_with_http_transport_custom_params(self, tmp_path: Path) -> None:
        """测试 HTTP 传输使用自定义参数"""
        with (
            patch("RegistryTools.server.create_server") as mock_create_server,
            patch(
                "sys.argv",
                [
                    "registry-tools",
                    "--transport",
                    "http",
                    "--host",
                    "0.0.0.0",
                    "--port",
                    "9000",
                    "--path",
                    "/api/mcp",
                    "--data-path",
                    str(tmp_path),
                ],
            ),
        ):
            mock_app = Mock()
            mock_app.run = Mock()
            mock_create_server.return_value = mock_app

            main()

            # 验证 HTTP 传输被正确调用 (使用自定义参数)
            mock_app.run.assert_called_once_with(
                transport="http", host="0.0.0.0", port=9000, path="/api/mcp"
            )

    def test_main_with_stdio_transport(self, tmp_path: Path) -> None:
        """测试 STDIO 传输 (默认)"""
        with (
            patch("RegistryTools.server.create_server") as mock_create_server,
            patch(
                "sys.argv", ["registry-tools", "--transport", "stdio", "--data-path", str(tmp_path)]
            ),
        ):
            mock_app = Mock()
            mock_app.run = Mock()
            mock_create_server.return_value = mock_app

            main()

            # 验证 STDIO 传输被调用 (无参数)
            mock_app.run.assert_called_once_with()

    def test_main_without_transport_arg_uses_stdio(self, tmp_path: Path) -> None:
        """测试未指定传输时默认使用 STDIO"""
        with (
            patch("RegistryTools.server.create_server") as mock_create_server,
            patch("sys.argv", ["registry-tools", "--data-path", str(tmp_path)]),
        ):
            mock_app = Mock()
            mock_app.run = Mock()
            mock_create_server.return_value = mock_app

            main()

            # 验证默认使用 STDIO 传输
            mock_app.run.assert_called_once_with()

    def test_main_help_includes_transport_options(self, capsys: pytest.CaptureFixture[str]) -> None:
        """测试帮助信息包含传输协议说明"""
        with patch("sys.argv", ["registry-tools", "--help"]):
            with pytest.raises(SystemExit):
                main()

        captured = capsys.readouterr()
        # 验证帮助信息包含传输协议说明
        assert "传输协议" in captured.out or "transport" in captured.out
        assert "stdio" in captured.out
        assert "http" in captured.out
