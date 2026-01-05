"""
搜索功能演示

演示 RegistryTools 的搜索功能。

Copyright (c) 2026 Maric
License: MIT
"""

from pathlib import Path
from RegistryTools.registry.models import SearchMethod
from RegistryTools.registry.registry import ToolRegistry
from RegistryTools.search.bm25_search import BM25Search
from RegistryTools.search.regex_search import RegexSearch
from RegistryTools.storage.json_storage import JSONStorage


def main() -> None:
    """搜索功能演示"""
    # 设置数据路径
    data_path = Path.home() / ".RegistryTools"
    storage = JSONStorage(data_path / "tools.json")
    registry = ToolRegistry()

    # 加载工具
    if storage.validate():
        tools = storage.load_all()
        registry.register_many(tools)

    # 注册搜索算法
    registry.register_searcher(SearchMethod.BM25, BM25Search())
    registry.register_searcher(SearchMethod.REGEX, RegexSearch(case_sensitive=False))
    registry.rebuild_indexes()

    print("=== 搜索演示 ===\n")

    # 演示 1: BM25 搜索
    print("1. BM25 搜索 'github pull'")
    results = registry.search("github pull", SearchMethod.BM25, limit=3)
    for r in results:
        print(f"   {r.tool_name} (分数: {r.score:.2f})")

    # 演示 2: Regex 搜索
    print("\n2. Regex 搜索 'github.*pr'")
    results = registry.search("github.*pr", SearchMethod.REGEX, limit=3)
    for r in results:
        print(f"   {r.tool_name} (分数: {r.score:.2f})")

    # 演示 3: 中文搜索
    print("\n3. BM25 搜索 'aws 存储'")
    results = registry.search("aws 存储", SearchMethod.BM25, limit=3)
    for r in results:
        print(f"   {r.tool_name} (分数: {r.score:.2f})")

    # 演示 4: 自然语言搜索
    print("\n4. 自然语言搜索 'send message to slack'")
    results = registry.search("send message to slack", SearchMethod.BM25, limit=3)
    for r in results:
        print(f"   {r.tool_name} (分数: {r.score:.2f})")


if __name__ == "__main__":
    main()
