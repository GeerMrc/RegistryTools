"""
存储迁移示例

演示如何在 JSON 和 SQLite 存储后端之间迁移数据。

迁移场景：
- 从 JSON 迁移到 SQLite：提升大规模工具集性能
- 从 SQLite 迁移到 JSON：简化部署或调试

Copyright (c) 2026 Maric
License: MIT
"""

from pathlib import Path
from registrytools.storage.json_storage import JSONStorage
from registrytools.storage.sqlite_storage import SQLiteStorage


def migrate_json_to_sqlite(
    json_path: Path,
    sqlite_path: Path,
    backup: bool = True,
) -> int:
    """
    从 JSON 存储迁移到 SQLite 存储

    Args:
        json_path: JSON 存储文件路径
        sqlite_path: SQLite 数据库文件路径
        backup: 是否备份原 JSON 文件

    Returns:
        迁移的工具数量
    """
    print(f"=== 从 JSON 迁移到 SQLite ===")
    print(f"源文件: {json_path}")
    print(f"目标文件: {sqlite_path}")

    # 1. 备份原 JSON 文件
    if backup and json_path.exists():
        backup_path = json_path.with_suffix(".json.backup")
        import shutil

        shutil.copy2(json_path, backup_path)
        print(f"✓ 已备份原文件到: {backup_path}")

    # 2. 从 JSON 加载工具
    json_storage = JSONStorage(json_path)
    if not json_storage.validate():
        print("✗ JSON 文件无效或不存在")
        return 0

    tools = json_storage.load_all()
    print(f"✓ 从 JSON 加载了 {len(tools)} 个工具")

    # 3. 保存到 SQLite
    sqlite_storage = SQLiteStorage(sqlite_path)
    sqlite_storage.save_many(tools)
    print(f"✓ 已迁移 {len(tools)} 个工具到 SQLite")

    # 4. 验证数据
    loaded_tools = sqlite_storage.load_all()
    if len(loaded_tools) == len(tools):
        print(f"✓ 数据验证成功：SQLite 中有 {len(loaded_tools)} 个工具")
    else:
        print(f"✗ 数据验证失败：预期 {len(tools)} 个，实际 {len(loaded_tools)} 个")
        return 0

    return len(tools)


def migrate_sqlite_to_json(
    sqlite_path: Path,
    json_path: Path,
    backup: bool = True,
) -> int:
    """
    从 SQLite 存储迁移到 JSON 存储

    Args:
        sqlite_path: SQLite 数据库文件路径
        json_path: JSON 存储文件路径
        backup: 是否备份原数据库文件

    Returns:
        迁移的工具数量
    """
    print(f"=== 从 SQLite 迁移到 JSON ===")
    print(f"源文件: {sqlite_path}")
    print(f"目标文件: {json_path}")

    # 1. 备份原数据库文件
    if backup and sqlite_path.exists():
        backup_path = sqlite_path.with_suffix(".db.backup")
        import shutil

        shutil.copy2(sqlite_path, backup_path)
        print(f"✓ 已备份原文件到: {backup_path}")

    # 2. 从 SQLite 加载工具
    sqlite_storage = SQLiteStorage(sqlite_path)
    if not sqlite_storage.validate():
        print("✗ SQLite 数据库无效或不存在")
        return 0

    tools = sqlite_storage.load_all()
    print(f"✓ 从 SQLite 加载了 {len(tools)} 个工具")

    # 3. 保存到 JSON
    json_storage = JSONStorage(json_path)
    json_storage.save_many(tools)
    print(f"✓ 已迁移 {len(tools)} 个工具到 JSON")

    # 4. 验证数据
    loaded_tools = json_storage.load_all()
    if len(loaded_tools) == len(tools):
        print(f"✓ 数据验证成功：JSON 中有 {len(loaded_tools)} 个工具")
    else:
        print(f"✗ 数据验证失败：预期 {len(tools)} 个，实际 {len(loaded_tools)} 个")
        return 0

    return len(tools)


def main() -> None:
    """存储迁移示例"""
    # 设置数据路径
    data_path = Path.home() / ".RegistryTools"
    data_path.mkdir(parents=True, exist_ok=True)

    json_file = data_path / "tools.json"
    sqlite_file = data_path / "tools.db"

    print("RegistryTools 存储迁移工具")
    print("=" * 50)
    print()

    # 检查现有存储
    has_json = json_file.exists()
    has_sqlite = sqlite_file.exists()

    if has_json and not has_sqlite:
        # 场景 1: 只有 JSON，迁移到 SQLite
        print("检测到 JSON 存储，建议迁移到 SQLite 以提升性能")
        choice = input("是否继续迁移？(y/N): ").strip().lower()

        if choice == "y":
            count = migrate_json_to_sqlite(json_file, sqlite_file)
            if count > 0:
                print(f"\n✓ 迁移成功！共迁移 {count} 个工具")
                print(f"\n后续步骤：")
                print(f"1. 设置环境变量：export REGISTRYTOOLS_STORAGE_BACKEND=sqlite")
                print(f"2. 或使用 CLI 参数：registry-tools --storage-backend sqlite")
                print(f"3. 确认 SQLite 工作正常后，可删除原 JSON 文件")

    elif has_sqlite and not has_json:
        # 场景 2: 只有 SQLite，迁移到 JSON
        print("检测到 SQLite 存储")
        print("注意：JSON 存储适合小规模工具集（< 1000 工具）")
        choice = input("是否迁移到 JSON？(y/N): ").strip().lower()

        if choice == "y":
            count = migrate_sqlite_to_json(sqlite_file, json_file)
            if count > 0:
                print(f"\n✓ 迁移成功！共迁移 {count} 个工具")
                print(f"\n后续步骤：")
                print(f"1. 设置环境变量：export REGISTRYTOOLS_STORAGE_BACKEND=json")
                print(f"2. 或使用 CLI 参数：registry-tools --storage-backend json")
                print(f"3. 确认 JSON 工作正常后，可删除原 SQLite 文件")

    elif has_json and has_sqlite:
        # 场景 3: 两者都存在
        print("检测到 JSON 和 SQLite 存储都存在")
        print("请选择要使用的存储后端：")
        print("1. JSON 存储")
        print("2. SQLite 存储")
        print("3. 从 JSON 迁移到 SQLite")
        print("4. 从 SQLite 迁移到 JSON")

        choice = input("请选择 (1-4): ").strip()

        if choice == "1":
            print("\n使用 JSON 存储：")
            print("export REGISTRYTOOLS_STORAGE_BACKEND=json")
        elif choice == "2":
            print("\n使用 SQLite 存储：")
            print("export REGISTRYTOOLS_STORAGE_BACKEND=sqlite")
        elif choice == "3":
            count = migrate_json_to_sqlite(json_file, sqlite_file)
            print(f"\n✓ 迁移成功！共迁移 {count} 个工具")
        elif choice == "4":
            count = migrate_sqlite_to_json(sqlite_file, json_file)
            print(f"\n✓ 迁移成功！共迁移 {count} 个工具")

    else:
        # 场景 4: 都不存在
        print("未检测到现有存储数据")
        print("请先运行 RegistryTools 生成默认工具集")

    print("\n" + "=" * 50)
    print("详见: docs/STORAGE.md#数据迁移")


if __name__ == "__main__":
    main()
