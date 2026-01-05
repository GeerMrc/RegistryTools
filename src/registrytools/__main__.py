"""
RegistryTools MCP 服务器入口

用于启动 RegistryTools 的 FastMCP 服务器。

用法:
    # STDIO 传输 (默认,用于本地 CLI 集成)
    registry-tools [--data-path PATH]

    # Streamable HTTP 传输 (用于远程部署)
    registry-tools --transport http --host 0.0.0.0 --port 8000 [--path /mcp]

环境变量:
    REGISTRYTOOLS_DATA_PATH    数据目录路径 (默认: ~/.RegistryTools)
    REGISTRYTOOLS_TRANSPORT     传输协议 (stdio/http, 默认: stdio)
    REGISTRYTOOLS_LOG_LEVEL     日志级别 (DEBUG/INFO/WARNING/ERROR, 默认: INFO)
"""

import argparse
import logging
import os
from pathlib import Path

from registrytools import __version__


def _setup_logging(log_level_str: str) -> None:
    """
    配置日志系统 (Phase 14.2)

    Args:
        log_level_str: 日志级别字符串 (DEBUG/INFO/WARNING/ERROR)
    """
    # 转换为大写并映射到 logging 常量
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)

    # 配置根日志记录器
    # 使用 force=True 确保即使已有配置也会重新配置
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )

    # 获取根日志记录器
    logger = logging.getLogger(__name__)

    # 记录启动信息
    logger.debug(f"RegistryTools 版本: {__version__}")
    logger.debug(f"日志级别: {log_level_str.upper()}")


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        description="RegistryTools - MCP Tool Registry Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
传输协议说明:
  stdio    标准输入输出 (默认),用于本地 CLI 集成
  http     Streamable HTTP,用于远程服务部署

环境变量:
  REGISTRYTOOLS_DATA_PATH    数据目录路径 (默认: ~/.RegistryTools)
  REGISTRYTOOLS_TRANSPORT     传输协议 (stdio/http, 默认: stdio)
  REGISTRYTOOLS_LOG_LEVEL     日志级别 (DEBUG/INFO/WARNING/ERROR, 默认: INFO)

示例:
  # 本地 STDIO 模式 (默认)
  registry-tools

  # 远程 HTTP 模式
  registry-tools --transport http --host 0.0.0.0 --port 8000

  # 使用环境变量
  REGISTRYTOOLS_DATA_PATH=/custom/path registry-tools
        """,
    )
    parser.add_argument(
        "--data-path", type=str, default=None, help="数据目录路径 (默认: ~/.RegistryTools)"
    )
    parser.add_argument(
        "--transport",
        type=str,
        choices=["stdio", "http"],
        default=None,
        help="传输协议: stdio (默认) 或 http",
    )
    parser.add_argument(
        "--host", type=str, default="127.0.0.1", help="HTTP 主机地址 (默认: 127.0.0.1)"
    )
    parser.add_argument("--port", type=int, default=8000, help="HTTP 端口 (默认: 8000)")
    parser.add_argument("--path", type=str, default="/", help="HTTP 路径 (默认: /)")
    parser.add_argument("--version", action="version", version=f"RegistryTools {__version__}")

    args = parser.parse_args()

    # ========================================================
    # 环境变量支持 (Phase 14.1)
    # 优先级: 环境变量 > 命令行参数 > 默认值
    # ========================================================

    # 日志级别 (Phase 14.2 实现)
    log_level = os.getenv("REGISTRYTOOLS_LOG_LEVEL", "INFO")
    valid_log_levels = ("DEBUG", "INFO", "WARNING", "ERROR")
    if log_level.upper() not in valid_log_levels:
        raise ValueError(f"无效的日志级别: {log_level}. 支持: {', '.join(valid_log_levels)}")

    # 配置日志系统 (Phase 14.2)
    _setup_logging(log_level)

    # 获取日志记录器
    logger = logging.getLogger(__name__)

    # 数据路径
    data_path_str = os.getenv("REGISTRYTOOLS_DATA_PATH") or args.data_path
    if data_path_str:
        data_path = Path(data_path_str)
    else:
        data_path = Path.home() / ".RegistryTools"

    # 传输协议
    transport = os.getenv("REGISTRYTOOLS_TRANSPORT") or args.transport or "stdio"
    if transport not in ("stdio", "http"):
        raise ValueError(f"无效的传输协议: {transport}. 支持: stdio, http")

    # 确保数据目录存在
    data_path.mkdir(parents=True, exist_ok=True)

    # 记录配置信息
    logger.info(f"数据路径: {data_path}")
    logger.info(f"传输协议: {transport}")

    # 导入并启动服务器
    from registrytools.server import create_server

    logger.info("正在创建 MCP 服务器...")
    app = create_server(data_path)
    logger.info("MCP 服务器创建完成")

    # 根据传输协议启动服务器
    if transport == "http":
        # Streamable HTTP 传输 (推荐用于远程部署)
        logger.info(f"启动 HTTP 服务器: {args.host}:{args.port}{args.path}")
        app.run(transport="http", host=args.host, port=args.port, path=args.path)
    else:
        # STDIO 传输 (默认,用于本地 CLI 集成)
        logger.info("启动 STDIO 服务器")
        app.run()


if __name__ == "__main__":
    main()
