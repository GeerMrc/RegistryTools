#!/usr/bin/env python
"""
创建发布包脚本

用于创建 RegistryTools 的发布包。

用法:
    python scripts/release/create-release.py [version]
"""

import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


def create_git_tag(version: str):
    """创建 Git 标签"""
    print(f"🏷️  创建 Git 标签 v{version}...")

    # 检查标签是否已存在
    result = subprocess.run(
        ["git", "tag", "-l", f"v{version}"],
        capture_output=True,
        text=True
    )

    if result.stdout.strip():
        print(f"  ⚠️  标签 v{version} 已存在")
        return False

    # 创建标签
    result = subprocess.run(
        ["git", "tag", "-a", f"v{version}", "-m", f"Release v{version}"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"  ✗ 标签创建失败: {result.stderr}")
        return False

    print(f"  ✓ 标签 v{version} 已创建")
    return True


def create_release_notes(version: str):
    """创建发布说明"""
    print("📝 创建发布说明...")

    # 从 CHANGELOG.md 提取变更
    changelog = Path("docs/CHANGELOG.md")
    if not changelog.exists():
        content = "# Release Notes\n\nInitial release.\n"
    else:
        content = changelog.read_text(encoding="utf-8")

    # 创建发布说明文件
    release_notes = f"""# RegistryTools v{version} Release Notes

Release Date: {datetime.now().strftime('%Y-%m-%d')}

## 安装

```bash
pip install registry-tools=={version}
```

## 变更内容

详见 [CHANGELOG.md](../CHANGELOG.md)

## 验证

```bash
python scripts/verify/verify-after-install.py
```

## 配置

在 Claude Desktop 配置中添加:

```json
{{
  "mcpServers": {{
    "RegistryTools": {{
      "command": "uvx",
      "args": ["registry-tools=={version}", "--data-path", "~/.RegistryTools"]
    }}
  }}
}}
```
"""

    notes_dir = Path("dist") / "release-notes"
    notes_dir.mkdir(parents=True, exist_ok=True)

    notes_file = notes_dir / f"v{version}.md"
    notes_file.write_text(release_notes, encoding="utf-8")

    print(f"  ✓ 发布说明已创建: {notes_file}")
    return True


def create_release_package(version: str):
    """创建发布包"""
    print(f"📦 创建发布包 v{version}...")

    dist_dir = Path("dist")
    release_dir = dist_dir / f"registry-tools-{version}"
    release_dir.mkdir(parents=True, exist_ok=True)

    # 复制文件
    files_to_copy = [
        "README.md",
        "LICENSE",
        "pyproject.toml",
        "docs/",
        "examples/",
    ]

    for item in files_to_copy:
        src = Path(item)
        dst = release_dir / item
        if src.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)

    # 复制包目录
    package_dir = release_dir / "RegistryTools"
    if package_dir.exists():
        shutil.rmtree(package_dir)
    shutil.copytree("RegistryTools", package_dir,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    # 创建压缩包
    archive_name = f"registry-tools-{version}"
    archive_path = dist_dir / f"{archive_name}.tar.gz"

    if archive_path.exists():
        archive_path.unlink()

    shutil.make_archive(str(archive_path.with_suffix("")), "gztar",
                       root_dir=dist_dir,
                       base_dir=f"registry-tools-{version}")

    print(f"  ✓ 发布包已创建: {archive_path.name}")

    # 清理临时目录
    shutil.rmtree(release_dir)

    return True


def update_version(version: str):
    """更新版本号"""
    print(f"📝 更新版本号到 {version}...")

    # 更新 pyproject.toml
    pyproject = Path("pyproject.toml")
    if pyproject.exists():
        content = pyproject.read_text(encoding="utf-8")
        # 简单的版本号替换（实际应使用 toml 库）
        import re
        new_content = re.sub(
            r'version\s*=\s*"[^"]+"',
            f'version = "{version}"',
            content
        )
        pyproject.write_text(new_content, encoding="utf-8")
        print("  ✓ pyproject.toml 已更新")

    return True


def main():
    """主函数"""
    import sys

    version = sys.argv[1] if len(sys.argv) > 1 else "0.1.0"

    print("=" * 60)
    print(f"RegistryTools - 创建发布包 v{version}")
    print("=" * 60)
    print()

    steps = [
        ("更新版本号", lambda: update_version(version)),
        ("创建 Git 标签", lambda: create_git_tag(version)),
        ("创建发布说明", lambda: create_release_notes(version)),
        ("创建发布包", lambda: create_release_package(version)),
    ]

    for name, func in steps:
        print()
        try:
            if not func():
                print(f"\n❌ {name} 失败")
                return 1
        except Exception as e:
            print(f"\n❌ {name} 出错: {e}")
            return 1

    print()
    print("=" * 60)
    print("✅ 发布包创建完成!")
    print("=" * 60)
    print(f"\n📂 输出文件:")
    print(f"  - dist/registry-tools-{version}.tar.gz")
    print(f"  - dist/release-notes/v{version}.md")
    print(f"\n📝 下一步:")
    print(f"  1. 检查发布内容: ls -la dist/")
    print(f"  2. 推送标签: git push origin v{version}")
    print(f"  3. 发布到 PyPI: python -m twine upload dist/*")

    return 0


if __name__ == "__main__":
    exit(main())
