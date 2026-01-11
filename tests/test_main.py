"""
测试 __main__.py 模块

测试 RegistryTools 的 CLI 入口功能。

Copyright (c) 2026 Maric
License: MIT
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from registrytools.__main__ import main


class TestLogging:
    """测试日志功能 (Phase 14.2)"""

    def test_default_log_level_is_info(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """测试默认日志级别是 INFO"""
        with (
            patch("registrytools.server.create_server") as mock_create_server,
            patch("sys.argv", ["registry-tools", "--data-path", str(tmp_path)]),
        ):
            mock_app = Mock()
            mock_app.run = Mock()
            mock_create_server.return_value = mock_app

            main()

            # 验证日志输出包含配置信息
            captured = capsys.readouterr()
            assert "数据路径:" in captured.err
            assert "传输协议:" in captured.err

    def test_debug_log_level_from_env(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """测试从环境变量设置 DEBUG 日志级别"""
        with (
            patch("registrytools.server.create_server") as mock_create_server,
            patch("sys.argv", ["registry-tools", "--data-path", str(tmp_path)]),
        ):
            monkeypatch.setenv("REGISTRYTOOLS_LOG_LEVEL", "DEBUG")

            mock_app = Mock()
            mock_app.run = Mock()
            mock_create_server.return_value = mock_app

            main()

            # 验证日志级别被设置为 DEBUG
            import logging

            assert logging.getLogger().level == logging.DEBUG

    def test_warning_log_level_from_env(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """测试从环境变量设置 WARNING 日志级别"""
        with (
            patch("registrytools.server.create_server") as mock_create_server,
            patch("sys.argv", ["registry-tools", "--data-path", str(tmp_path)]),
        ):
            monkeypatch.setenv("REGISTRYTOOLS_LOG_LEVEL", "WARNING")

            mock_app = Mock()
            mock_app.run = Mock()
            mock_create_server.return_value = mock_app

            main()

            # 验证日志级别被设置为 WARNING
            import logging

            assert logging.getLogger().level == logging.WARNING

    def test_error_log_level_from_env(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """测试从环境变量设置 ERROR 日志级别"""
        with (
            patch("registrytools.server.create_server") as mock_create_server,
            patch("sys.argv", ["registry-tools", "--data-path", str(tmp_path)]),
        ):
            monkeypatch.setenv("REGISTRYTOOLS_LOG_LEVEL", "ERROR")

            mock_app = Mock()
            mock_app.run = Mock()
            mock_create_server.return_value = mock_app

            main()

            # 验证日志级别被设置为 ERROR
            import logging

            assert logging.getLogger().level == logging.ERROR

    def test_debug_log_shows_version(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """测试 DEBUG 级别显示版本信息"""
        with (
            patch("registrytools.server.create_server") as mock_create_server,
            patch("sys.argv", ["registry-tools", "--data-path", str(tmp_path)]),
        ):
            monkeypatch.setenv("REGISTRYTOOLS_LOG_LEVEL", "DEBUG")

            mock_app = Mock()
            mock_app.run = Mock()
            mock_create_server.return_value = mock_app

            main()

            # 验证 DEBUG 级别显示版本信息
            captured = capsys.readouterr()
            assert "RegistryTools 版本:" in captured.err


class TestMain:
    """测试 main() 函数"""

    def test_main_with_custom_data_path(self, tmp_path: Path) -> None:
        """测试使用自定义数据路径"""
        with (
            patch("registrytools.server.create_server") as mock_create_server,
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
            patch("registrytools.server.create_server") as mock_create_server,
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
            patch("registrytools.server.create_server") as mock_create_server,
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
            patch("registrytools.server.create_server") as mock_create_server,
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
            patch("registrytools.server.create_server") as mock_create_server,
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
            patch("registrytools.server.create_server") as mock_create_server,
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
            patch("registrytools.server.create_server") as mock_create_server,
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


class TestMainEnvironmentVariables:
    """测试环境变量支持 (Phase 14.1)"""

    def test_env_data_path_override(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试 REGISTRYTOOLS_DATA_PATH 环境变量"""
        custom_path = tmp_path / "env_data"

        with (
            patch("registrytools.server.create_server") as mock_create_server,
            patch("sys.argv", ["registry-tools"]),
        ):
            monkeypatch.setenv("REGISTRYTOOLS_DATA_PATH", str(custom_path))

            mock_app = Mock()
            mock_app.run = Mock()
            mock_create_server.return_value = mock_app

            main()

            # 验证使用了环境变量指定的路径
            mock_create_server.assert_called_once_with(custom_path)
            # 验证数据目录被创建
            assert custom_path.exists()

    def test_env_data_path_overrides_cli_arg(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """测试环境变量优先级高于命令行参数"""
        env_path = tmp_path / "from_env"
        cli_path = tmp_path / "from_cli"

        with (
            patch("registrytools.server.create_server") as mock_create_server,
            patch("sys.argv", ["registry-tools", "--data-path", str(cli_path)]),
        ):
            monkeypatch.setenv("REGISTRYTOOLS_DATA_PATH", str(env_path))

            mock_app = Mock()
            mock_app.run = Mock()
            mock_create_server.return_value = mock_app

            main()

            # 验证环境变量优先
            mock_create_server.assert_called_once_with(env_path)

    def test_env_transport_stdio(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试 REGISTRYTOOLS_TRANSPORT=stdio"""
        with (
            patch("registrytools.server.create_server") as mock_create_server,
            patch("sys.argv", ["registry-tools", "--data-path", str(tmp_path)]),
        ):
            monkeypatch.setenv("REGISTRYTOOLS_TRANSPORT", "stdio")

            mock_app = Mock()
            mock_app.run = Mock()
            mock_create_server.return_value = mock_app

            main()

            # 验证使用 STDIO 传输
            mock_app.run.assert_called_once_with()

    def test_env_transport_http(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试 REGISTRYTOOLS_TRANSPORT=http"""
        with (
            patch("registrytools.server.create_server") as mock_create_server,
            patch("sys.argv", ["registry-tools", "--data-path", str(tmp_path)]),
        ):
            monkeypatch.setenv("REGISTRYTOOLS_TRANSPORT", "http")

            mock_app = Mock()
            mock_app.run = Mock()
            mock_create_server.return_value = mock_app

            main()

            # 验证使用 HTTP 传输
            mock_app.run.assert_called_once_with(
                transport="http", host="127.0.0.1", port=8000, path="/"
            )

    def test_env_transport_overrides_cli_arg(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """测试传输环境变量优先级高于命令行参数"""
        with (
            patch("registrytools.server.create_server") as mock_create_server,
            patch(
                "sys.argv", ["registry-tools", "--transport", "stdio", "--data-path", str(tmp_path)]
            ),
        ):
            monkeypatch.setenv("REGISTRYTOOLS_TRANSPORT", "http")

            mock_app = Mock()
            mock_app.run = Mock()
            mock_create_server.return_value = mock_app

            main()

            # 验证环境变量优先
            mock_app.run.assert_called_once_with(
                transport="http", host="127.0.0.1", port=8000, path="/"
            )

    def test_env_invalid_transport_raises_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """测试无效的传输环境变量"""
        with (
            patch("registrytools.server.create_server"),
            patch("sys.argv", ["registry-tools", "--data-path", str(tmp_path)]),
        ):
            monkeypatch.setenv("REGISTRYTOOLS_TRANSPORT", "invalid")

            with pytest.raises(ValueError, match="无效的传输协议"):
                main()

    def test_env_log_level_valid(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试有效的日志级别环境变量"""
        for level in ("DEBUG", "INFO", "WARNING", "ERROR"):
            with (
                patch("registrytools.server.create_server"),
                patch("sys.argv", ["registry-tools", "--data-path", str(tmp_path)]),
            ):
                monkeypatch.setenv("REGISTRYTOOLS_LOG_LEVEL", level)

                mock_app = Mock()
                mock_app.run = Mock()

                # 不应该抛出异常
                main()

    def test_env_log_level_invalid(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试无效的日志级别环境变量"""
        with (
            patch("registrytools.server.create_server"),
            patch("sys.argv", ["registry-tools", "--data-path", str(tmp_path)]),
        ):
            monkeypatch.setenv("REGISTRYTOOLS_LOG_LEVEL", "INVALID")

            with pytest.raises(ValueError, match="无效的日志级别"):
                main()
