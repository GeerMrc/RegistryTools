#!/usr/bin/env python
"""
Wheel 包构建脚本

用于构建 RegistryTools 的 Python Wheel 分发包。

用法:
    python scripts/build/build-wheel.py
"""

import os
import shutil
import subprocess
from pathlib import Path


def clean_build():
    """清理构建目录"""
    print("🧹 清理构建目录...")
    for dir_name in ["build", "dist", "*.egg-info"]:
        for path in Path(".").glob(dir_name):
            if path.is_dir():
                shutil.rmtree(path)
                print(f"  已删除: {path}")


def build_wheel():
    """构建 Wheel 包"""
    print("📦 构建 Wheel 包...")
    result = subprocess.run(
        ["python", "-m", "build", "--wheel"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print("❌ 构建失败:")
        print(result.stderr)
        return False
    print(result.stdout)
    return True


def list_output():
    """列出生成的包"""
    print("📋 生成的包:")
    dist_dir = Path("dist")
    if dist_dir.exists():
        for file in dist_dir.glob("*.whl"):
            size = file.stat().st_size / 1024  # KB
            print(f"  - {file.name} ({size:.1f} KB)")
        return True
    else:
        print("  ⚠️  未找到 dist 目录")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("RegistryTools - Wheel 包构建")
    print("=" * 60)
    print()

    # 清理
    clean_build()
    print()

    # 构建
    if not build_wheel():
        print("\n❌ 构建失败")
        return 1

    print()
    # 列出输出
    list_output()

    print()
    print("=" * 60)
    print("✅ 构建完成!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    exit(main())
