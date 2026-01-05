"""
RegistryTools MCP 服务器入口

用于启动 RegistryTools 的 FastMCP 服务器。

用法:
    # STDIO 传输 (默认,用于本地 CLI 集成)
    registry-tools [--data-path PATH]

    # Streamable HTTP 传输 (用于远程部署)
    registry-tools --transport http --host 0.0.0.0 --port 8000 [--path /mcp]
"""

import argparse
from pathlib import Path

from registrytools import __version__


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        description="RegistryTools - MCP Tool Registry Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
传输协议说明:
  stdio    标准输入输出 (默认),用于本地 CLI 集成
  http     Streamable HTTP,用于远程服务部署

示例:
  # 本地 STDIO 模式 (默认)
  registry-tools

  # 远程 HTTP 模式
  registry-tools --transport http --host 0.0.0.0 --port 8000

  # 自定义 HTTP 路径
  registry-tools --transport http --port 8000 --path /api/mcp
        """,
    )
    parser.add_argument(
        "--data-path", type=str, default=None, help="数据目录路径 (默认: ~/.RegistryTools)"
    )
    parser.add_argument(
        "--transport",
        type=str,
        choices=["stdio", "http"],
        default="stdio",
        help="传输协议: stdio (默认) 或 http",
    )
    parser.add_argument(
        "--host", type=str, default="127.0.0.1", help="HTTP 主机地址 (默认: 127.0.0.1)"
    )
    parser.add_argument("--port", type=int, default=8000, help="HTTP 端口 (默认: 8000)")
    parser.add_argument("--path", type=str, default="/", help="HTTP 路径 (默认: /)")
    parser.add_argument("--version", action="version", version=f"RegistryTools {__version__}")

    args = parser.parse_args()

    # 确定数据路径
    if args.data_path:
        data_path = Path(args.data_path)
    else:
        data_path = Path.home() / ".RegistryTools"

    # 确保数据目录存在
    data_path.mkdir(parents=True, exist_ok=True)

    # 导入并启动服务器
    from registrytools.server import create_server

    app = create_server(data_path)

    # 根据传输协议启动服务器
    if args.transport == "http":
        # Streamable HTTP 传输 (推荐用于远程部署)
        app.run(transport="http", host=args.host, port=args.port, path=args.path)
    else:
        # STDIO 传输 (默认,用于本地 CLI 集成)
        app.run()


if __name__ == "__main__":
    main()
