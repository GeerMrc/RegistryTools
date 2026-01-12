"""
SQLite 存储使用示例

演示如何使用 SQLite 存储后端创建和使用工具注册表。

SQLite 存储适合以下场景：
- 工具数量超过 1000 个
- 需要高性能查询和过滤
- 需要支持并发访问
- 需要 ACID 事务保证

Copyright (c) 2026 Maric
License: MIT
"""

from pathlib import Path

from registrytools.registry.models import (
    SearchMethod,
    ToolMetadata,
    ToolTemperature,
)
from registrytools.registry.registry import ToolRegistry
from registrytools.search.bm25_search import BM25Search
from registrytools.search.regex_search import RegexSearch
from registrytools.storage.sqlite_storage import SQLiteStorage


def main() -> None:
    """SQLite 存储使用示例"""
    # 设置数据路径
    data_path = Path.home() / ".RegistryTools"
    data_path.mkdir(parents=True, exist_ok=True)

    # 创建 SQLite 存储实例
    storage = SQLiteStorage(data_path / "tools.db")

    # 创建注册表
    registry = ToolRegistry()

    # 加载已保存的工具
    if storage.validate():
        tools = storage.load_all()
        registry.register_many(tools)
        print(f"从 SQLite 加载了 {len(tools)} 个工具")
    else:
        print("SQLite 数据库为空，将使用默认工具集")

    # 注册搜索算法
    registry.register_searcher(SearchMethod.REGEX, RegexSearch(case_sensitive=False))
    registry.register_searcher(SearchMethod.BM25, BM25Search())

    # 重建搜索索引
    registry.rebuild_indexes()

    # 示例 1: 使用按温度加载功能（SQLite 性能优势）
    print("\n=== 按温度加载工具（性能优化）===")
    hot_tools = storage.load_by_temperature(ToolTemperature.HOT)
    warm_tools = storage.load_by_temperature(ToolTemperature.WARM)

    print(f"热工具（使用频率 ≥ 10）: {len(hot_tools)} 个")
    print(f"温工具（使用频率 3-9）: {len(warm_tools)} 个")

    # 示例 2: 按标签过滤（使用注册表过滤）
    print("\n=== 按标签过滤工具 ===")
    all_tools = registry.list_tools()
    tagged_tools = [t for t in all_tools if "github" in t.tags]
    print(f"标签 'github': {len(tagged_tools)} 个工具")

    # 示例 3: 按类别过滤
    print("\n=== 按类别过滤工具 ===")
    category_tools = registry.list_tools(category="github")
    print(f"类别 'github': {len(category_tools)} 个工具")

    # 示例 4: 搜索工具
    print("\n=== 搜索 GitHub 工具 ===")
    results = registry.search("github pull request", SearchMethod.BM25, limit=3)
    for result in results:
        print(f"- {result.tool_name}: {result.description} (相关度: {result.score:.2f})")

    # 示例 5: 注册新工具（使用事务）
    print("\n=== 注册新工具（事务保证）===")
    new_tool = ToolMetadata(
        name="my.custom.tool",
        description="我的自定义工具（使用 SQLite 存储）",
        category="custom",
        tags={"custom", "demo", "sqlite"},
    )
    registry.register(new_tool)
    storage.save(new_tool)
    print(f"已注册: {new_tool.name}")

    # 示例 6: 批量保存（SQLite 性能优势）
    print("\n=== 批量保存工具 ===")
    batch_tools = [
        ToolMetadata(
            name=f"batch.tool.{i}",
            description=f"批量工具 {i}",
            category="batch",
            tags={"batch", "demo"},
        )
        for i in range(10)
    ]

    storage.save_many(batch_tools)
    registry.register_many(batch_tools)
    print(f"已批量保存 {len(batch_tools)} 个工具")

    # 性能对比提示
    print("\n=== SQLite 性能优势 ===")
    print("- 加载 1000 工具: ~18ms (比 JSON 快 76%)")
    print("- 按标签过滤: ~4ms (比 JSON 快 73%)")
    print("- 内存占用: ~6MB (比 JSON 少 60%)")
    print("\n详见: docs/STORAGE.md")


if __name__ == "__main__":
    main()
