"""
RegistryTools MCP 服务器入口

用于启动 RegistryTools 的 FastMCP 服务器。

用法:
    registry-tools [--data-path PATH]
"""

import argparse
import sys
from pathlib import Path


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        description="RegistryTools - MCP Tool Registry Server"
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default=None,
        help="数据目录路径 (默认: ~/.RegistryTools)"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"RegistryTools {__version__}"
    )

    args = parser.parse_args()

    # 确定数据路径
    if args.data_path:
        data_path = Path(args.data_path)
    else:
        data_path = Path.home() / ".RegistryTools"

    # 确保数据目录存在
    data_path.mkdir(parents=True, exist_ok=True)

    # 导入并启动服务器
    from RegistryTools.server import create_server

    app = create_server(data_path)
    app.run()


if __name__ == "__main__":
    main()
