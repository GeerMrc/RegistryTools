#!/usr/bin/env python
"""
安装后验证脚本

用于验证 RegistryTools 是否正确安装。

用法:
    python scripts/verify/verify-after-install.py
"""

import importlib
import subprocess
import sys
from pathlib import Path


def verify_import():
    """验证模块导入"""
    print("🔍 验证模块导入...")

    try:
        import RegistryTools
        print("  ✓ RegistryTools 模块导入成功")
        return True
    except ImportError as e:
        print(f"  ✗ 模块导入失败: {e}")
        return False


def verify_dependencies():
    """验证依赖项"""
    print("\n🔍 验证依赖项...")

    dependencies = [
        "fastmcp",
        "rank_bm25",
        "jieba",
        "pydantic",
    ]

    all_ok = True
    for dep in dependencies:
        try:
            importlib.import_module(dep)
            print(f"  ✓ {dep}")
        except ImportError:
            print(f"  ✗ {dep} 未安装")
            all_ok = False

    return all_ok


def verify_cli():
    """验证命令行工具"""
    print("\n🔍 验证命令行工具...")

    try:
        result = subprocess.run(
            ["registry-tools", "--help"],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            print("  ✓ registry-tools 命令可用")
            return True
        else:
            print("  ✗ registry-tools 命令不可用")
            return False
    except Exception as e:
        print(f"  ✗ registry-tools 命令不可用: {e}")
        return False


def verify_data_directory():
    """验证数据目录"""
    print("\n🔍 验证数据目录...")

    from pathlib import Path
    data_dir = Path.home() / ".RegistryTools"

    if data_dir.exists():
        print(f"  ✓ 数据目录存在: {data_dir}")
    else:
        print(f"  ⚠️  数据目录不存在（首次运行时创建）: {data_dir}")

    return True


def main():
    """主函数"""
    print("=" * 60)
    print("RegistryTools - 安装后验证")
    print("=" * 60)
    print()

    checks = [
        verify_import(),
        verify_dependencies(),
        verify_cli(),
        verify_data_directory(),
    ]

    print()
    print("=" * 60)

    if all(checks):
        print("✅ 所有验证通过，安装正常！")
        print("=" * 60)
        return 0
    else:
        print("❌ 部分验证失败，请检查安装。")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    exit(main())
