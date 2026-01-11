"""
RegistryTools MCP 服务器入口

用于启动 RegistryTools 的 FastMCP 服务器。

用法:
    # STDIO 传输 (默认,用于本地 CLI 集成)
    registry-tools [--data-path PATH]

    # Streamable HTTP 传输 (用于远程部署)
    registry-tools --transport http --host 0.0.0.0 --port 8000 [--path /mcp] [--enable-auth]

    # API Key 管理 (Phase 15)
    registry-tools api-key create "My API Key" --permission read
    registry-tools api-key list
    registry-tools api-key delete <key-id>

环境变量:
    REGISTRYTOOLS_DATA_PATH      数据目录路径 (默认: ~/.RegistryTools)
    REGISTRYTOOLS_TRANSPORT       传输协议 (stdio/http, 默认: stdio)
    REGISTRYTOOLS_LOG_LEVEL       日志级别 (DEBUG/INFO/WARNING/ERROR, 默认: INFO)
    REGISTRYTOOLS_ENABLE_AUTH     启用 API Key 认证 (true/false, 默认: false, 仅 HTTP 模式)
    REGISTRYTOOLS_SEARCH_METHOD   默认搜索方法 (regex/bm25/embedding, 默认: bm25)
    REGISTRYTOOLS_DESCRIPTION     MCP 服务器描述 (可选, 默认: 统一的 MCP 工具注册与搜索服务，用于发现和筛选可用工具，提升任务执行工具调用准确性，复杂任务工具调用效率)
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


def main() -> None:
    """主入口"""
    parser = argparse.ArgumentParser(
        description="RegistryTools - MCP Tool Registry Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
传输协议说明:
  stdio    标准输入输出 (默认),用于本地 CLI 集成
  http     Streamable HTTP,用于远程服务部署

环境变量:
  REGISTRYTOOLS_DATA_PATH      数据目录路径 (默认: ~/.RegistryTools)
  REGISTRYTOOLS_TRANSPORT       传输协议 (stdio/http, 默认: stdio)
  REGISTRYTOOLS_LOG_LEVEL       日志级别 (DEBUG/INFO/WARNING/ERROR, 默认: INFO)
  REGISTRYTOOLS_ENABLE_AUTH     启用 API Key 认证 (true/false, 默认: false, 仅 HTTP 模式)
  REGISTRYTOOLS_SEARCH_METHOD    默认搜索方法 (regex/bm25/embedding, 默认: bm25)
  REGISTRYTOOLS_DESCRIPTION       MCP 服务器描述 (可选, 默认: 统一的 MCP 工具注册与搜索服务，用于发现和筛选可用工具，提升任务执行工具调用准确性，复杂任务工具调用效率)

示例:
  # 本地 STDIO 模式 (默认)
  registry-tools

  # 远程 HTTP 模式
  registry-tools --transport http --host 0.0.0.0 --port 8000

  # 远程 HTTP 模式 + API Key 认证
  registry-tools --transport http --host 0.0.0.0 --port 8000 --enable-auth

  # 使用环境变量
  REGISTRYTOOLS_DATA_PATH=/custom/path registry-tools

  # API Key 管理
  registry-tools api-key create "My API Key" --permission read
  registry-tools api-key list
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
    parser.add_argument(
        "--enable-auth",
        action="store_true",
        help="启用 API Key 认证 (仅 HTTP 模式, Phase 15)",
    )
    parser.add_argument("--version", action="version", version=f"RegistryTools {__version__}")

    # 添加 API Key 管理子命令 (Phase 15)
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # api-key 子命令
    api_key_parser = subparsers.add_parser("api-key", help="API Key 管理")
    api_key_subparsers = api_key_parser.add_subparsers(dest="api_key_action", help="API Key 操作")

    # create 子命令
    create_parser = api_key_subparsers.add_parser("create", help="创建 API Key")
    create_parser.add_argument("name", type=str, help="API Key 名称/描述")
    create_parser.add_argument(
        "--permission",
        type=str,
        choices=["read", "write", "admin"],
        default="read",
        help="权限级别 (默认: read)",
    )
    create_parser.add_argument("--expires-in", type=int, help="过期时间（秒）")
    create_parser.add_argument("--owner", type=str, help="所有者标识")

    # list 子命令
    list_parser = api_key_subparsers.add_parser("list", help="列出 API Key")
    list_parser.add_argument("--owner", type=str, help="按所有者筛选")

    # delete 子命令
    delete_parser = api_key_subparsers.add_parser("delete", help="删除 API Key")
    delete_parser.add_argument("key_id", type=str, help="API Key ID")

    args = parser.parse_args()

    # ========================================================
    # API Key 管理命令处理 (Phase 15)
    # ========================================================
    if args.command == "api-key":
        return _handle_api_key_command(args)

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
        # 先展开环境变量（如 $HOME），再展开 ~
        expanded = os.path.expandvars(data_path_str)
        data_path = Path(expanded).expanduser()
    else:
        data_path = Path.home() / ".RegistryTools"

    # 传输协议
    transport = os.getenv("REGISTRYTOOLS_TRANSPORT") or args.transport or "stdio"
    if transport not in ("stdio", "http"):
        raise ValueError(f"无效的传输协议: {transport}. 支持: stdio, http")

    # 认证启用状态 (Phase 15)
    enable_auth_str = os.getenv("REGISTRYTOOLS_ENABLE_AUTH", "false").lower()
    enable_auth = enable_auth_str in ("true", "1", "yes") or args.enable_auth

    # 验证认证配置
    if enable_auth and transport == "stdio":
        logger.warning("STDIO 模式不支持认证，认证将被禁用")
        enable_auth = False

    # 确保数据目录存在
    data_path.mkdir(parents=True, exist_ok=True)

    # 记录配置信息
    logger.info(f"数据路径: {data_path}")
    logger.info(f"传输协议: {transport}")
    if transport == "http":
        logger.info(f"API Key 认证: {'启用' if enable_auth else '禁用'}")

    # 导入并启动服务器
    from registrytools.server import create_auth_middleware_for_server, create_server

    logger.info("正在创建 MCP 服务器...")

    # 根据认证配置创建服务器
    if enable_auth:
        auth_middleware = create_auth_middleware_for_server(data_path)
        app = create_server(data_path, auth_middleware)
        logger.info("API Key 认证中间件已启用")
    else:
        app = create_server(data_path)
        logger.info("API Key 认证中间件未启用")

    logger.info("MCP 服务器创建完成")

    # 根据传输协议启动服务器
    if transport == "http":
        # Streamable HTTP 传输 (推荐用于远程部署)
        logger.info(f"启动 HTTP 服务器: {args.host}:{args.port}{args.path}")
        if enable_auth:
            logger.info("注意: 客户端需要在 HTTP Header 中提供 X-API-Key")
        app.run(transport="http", host=args.host, port=args.port, path=args.path)
    else:
        # STDIO 传输 (默认,用于本地 CLI 集成)
        logger.info("启动 STDIO 服务器")
        app.run()


def _handle_api_key_command(args: argparse.Namespace) -> None:
    """
    处理 API Key 管理命令 (Phase 15)

    Args:
        args: 命令行参数
    """

    from registrytools.auth import APIKeyPermission, APIKeyScope, APIKeyStorage, generate_api_key

    # 获取数据路径
    data_path_str = os.getenv("REGISTRYTOOLS_DATA_PATH") or args.data_path
    if data_path_str:
        # 先展开环境变量（如 $HOME），再展开 ~
        expanded = os.path.expandvars(data_path_str)
        data_path = Path(expanded).expanduser()
    else:
        data_path = Path.home() / ".RegistryTools"

    data_path.mkdir(parents=True, exist_ok=True)

    # 创建存储
    storage = APIKeyStorage(data_path / "api_keys.db")

    if args.api_key_action == "create":
        # 创建 API Key
        permission = APIKeyPermission(args.permission)
        api_key = generate_api_key(
            name=args.name,
            permission=permission,
            scope=APIKeyScope.ALL,
            expires_in=args.expires_in,
            owner=args.owner,
        )
        storage.save(api_key)

        print("✓ API Key 创建成功:")
        print(f"  ID: {api_key.key_id}")
        print(f"  Name: {api_key.name}")
        print(f"  Permission: {api_key.permission.value}")
        print(f"  API Key: {api_key.api_key}")
        print("\n重要: 请妥善保存 API Key，它只会显示这一次！")

    elif args.api_key_action == "list":
        # 列出 API Key
        api_keys = storage.list_all(owner=args.owner)

        if not api_keys:
            print("没有找到 API Key")
            return

        print(f"找到 {len(api_keys)} 个 API Key:\n")
        for key_meta in api_keys:
            print(f"ID: {key_meta.key_id}")
            print(f"Name: {key_meta.name}")
            print(f"Permission: {key_meta.permission.value}")
            print(f"Active: {key_meta.is_active}")
            print(f"Created: {key_meta.created_at}")
            print(f"Usage: {key_meta.usage_count} 次")
            print("-" * 40)

    elif args.api_key_action == "delete":
        # 删除 API Key
        deleted = storage.delete(args.key_id)
        if deleted:
            print(f"✓ API Key 已删除: {args.key_id}")
        else:
            print(f"✗ API Key 不存在: {args.key_id}")


if __name__ == "__main__":
    main()
