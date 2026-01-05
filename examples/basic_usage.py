"""
基本使用示例

演示 RegistryTools 的基本用法。

Copyright (c) 2026 Maric
License: MIT
"""

from pathlib import Path
from RegistryTools.registry.models import SearchMethod, ToolMetadata
from RegistryTools.registry.registry import ToolRegistry
from RegistryTools.search.bm25_search import BM25Search
from RegistryTools.search.regex_search import RegexSearch
from RegistryTools.storage.json_storage import JSONStorage


def main() -> None:
    """基本使用示例"""
    # 设置数据路径
    data_path = Path.home() / ".RegistryTools"
    data_path.mkdir(parents=True, exist_ok=True)

    # 创建存储和注册表
    storage = JSONStorage(data_path / "tools.json")
    registry = ToolRegistry()

    # 加载已保存的工具
    if storage.validate():
        tools = storage.load_all()
        registry.register_many(tools)
        print(f"已加载 {len(tools)} 个工具")

    # 注册搜索算法
    registry.register_searcher(SearchMethod.REGEX, RegexSearch(case_sensitive=False))
    registry.register_searcher(SearchMethod.BM25, BM25Search())

    # 重建搜索索引
    registry.rebuild_indexes()

    # 示例 1: 搜索 GitHub 工具
    print("\n=== 搜索 GitHub 工具 ===")
    results = registry.search("github pull request", SearchMethod.BM25, limit=3)
    for result in results:
        print(f"- {result.tool_name}: {result.description} (相关度: {result.score:.2f})")

    # 示例 2: 按类别列出工具
    print("\n=== 按类别列出工具 ===")
    categories = registry.list_categories()
    print(f"可用类别: {', '.join(categories[:5])}...")

    github_tools = registry.list_tools(category="github")
    print(f"GitHub 工具 ({len(github_tools)} 个):")
    for tool in github_tools[:3]:
        print(f"  - {tool.name}")

    # 示例 3: 获取工具定义
    print("\n=== 获取工具定义 ===")
    tool = registry.get_tool("github.create_pull_request")
    if tool:
        print(f"工具: {tool.name}")
        print(f"描述: {tool.description}")
        print(f"类别: {tool.category}")
        print(f"标签: {', '.join(tool.tags)}")

    # 示例 4: 注册新工具
    print("\n=== 注册新工具 ===")
    new_tool = ToolMetadata(
        name="my.custom.tool",
        description="我的自定义工具",
        category="custom",
        tags={"custom", "demo"},
    )
    registry.register(new_tool)
    storage.save(new_tool)
    print(f"已注册: {new_tool.name}")


if __name__ == "__main__":
    main()
