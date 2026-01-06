#!/usr/bin/env python
"""
MCP 安装包构建脚本

用于构建 RegistryTools 的 MCP 安装包。

用法:
    python scripts/build/build-mcp.py
"""

import json
import shutil
from pathlib import Path


def create_mcp_package():
    """创建 MCP 安装包"""
    print("📦 创建 MCP 安装包...")

    # 确保 dist 目录存在
    dist_dir = Path("dist")
    dist_dir.mkdir(exist_ok=True)

    # 复制 wheel 包
    print("  - 复制 Wheel 包...")
    for wheel in Path(".").glob("dist/*.whl"):
        shutil.copy(wheel, dist_dir / wheel.name)
        print(f"    ✓ {wheel.name}")

    # 创建 mcp-manifest.json
    manifest = {
        "name": "RegistryTools",
        "description": "A universal MCP Tool Registry Server with search capabilities",
        "version": "0.1.0",
        "author": "Maric",
        "license": "MIT",
        "python": ">=3.10",
        "install_command": "pip install registry-tools",
        "mcp_config": {
            "command": "uvx",
            "args": ["registry-tools", "--data-path", "~/.RegistryTools"]
        }
    }

    manifest_path = dist_dir / "mcp-manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"  ✓ 已创建: {manifest_path.name}")

    # 创建安装说明
    readme = """# RegistryTools MCP 安装指南

## 快速安装

### 使用 uvx (推荐)
```bash
uvx registry-tools
```

### 使用 pip
```bash
pip install registry-tools
```

## Claude Desktop 配置

在 Claude Desktop 的配置文件中添加:

```json
{
  "mcpServers": {
    "RegistryTools": {
      "command": "uvx",
      "args": ["registry-tools", "--data-path", "~/.RegistryTools"]
    }
  }
}
```

配置文件位置:
- macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
- Windows: %APPDATA%/Claude/claude_desktop_config.json
- Linux: ~/.config/Claude/claude_desktop_config.json

## 验证安装

```bash
# 测试 MCP 服务器
registry-tools --help
```

## 更多信息

- GitHub: [项目主页]
- 文档: [文档链接]
"""

    readme_path = dist_dir / "INSTALL.md"
    readme_path.write_text(readme, encoding="utf-8")
    print(f"  ✓ 已创建: {readme_path.name}")


def main():
    """主函数"""
    print("=" * 60)
    print("RegistryTools - MCP 安装包构建")
    print("=" * 60)
    print()

    create_mcp_package()

    print()
    print("=" * 60)
    print("✅ MCP 安装包构建完成!")
    print(f"📂 输出目录: dist/")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    exit(main())
