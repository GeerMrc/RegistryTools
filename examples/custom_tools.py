"""
自定义工具注册示例

演示如何注册自定义工具。

Copyright (c) 2026 Maric
License: MIT
"""

from pathlib import Path
from registrytools.registry.models import ToolMetadata
from registrytools.storage.json_storage import JSONStorage


def main() -> None:
    """自定义工具注册示例"""
    # 设置数据路径
    data_path = Path.home() / ".RegistryTools"
    storage_path = data_path / "tools.json"

    # 创建存储
    storage = JSONStorage(storage_path)

    # 定义自定义工具
    custom_tools = [
        ToolMetadata(
            name="data.transform.csv",
            description="转换 CSV 文件格式",
            mcp_server="data-processor",
            category="data",
            tags={"csv", "transform", "data"},
        ),
        ToolMetadata(
            name="api.rest.call",
            description="发起 REST API 调用",
            mcp_server="http-client",
            category="network",
            tags={"api", "rest", "http"},
        ),
        ToolMetadata(
            name="file.backup",
            description="创建文件备份",
            mcp_server="file-utils",
            category="filesystem",
            tags={"backup", "file", "storage"},
        ),
    ]

    # 注册工具
    for tool in custom_tools:
        try:
            storage.save(tool)
            print(f"✓ 已注册: {tool.name}")
        except Exception as e:
            print(f"✗ 注册失败 {tool.name}: {e}")

    print(f"\n总计注册 {len(custom_tools)} 个自定义工具")


if __name__ == "__main__":
    main()
