# RegistryTools 脚本工具

> **版本**: v0.1.0
> **更新日期**: 2026-01-06

---

## 概述

`scripts/` 目录包含 RegistryTools 项目开发、构建、验证和发布所需的自动化脚本。

```
scripts/
├── build/           # 构建脚本
│   ├── build-wheel.py
│   └── build-mcp.py
├── release/         # 发布脚本
│   └── create-release.py
└── verify/          # 验证脚本
    ├── verify-before-release.py
    └── verify-after-install.py
```

---

## 快速开始

### 构建项目

```bash
# 构建 Wheel 包
python scripts/build/build-wheel.py

# 构建 MCP 安装包
python scripts/build/build-mcp.py
```

### 验证项目

```bash
# 发布前验证
python scripts/verify/verify-before-release.py

# 安装后验证
python scripts/verify/verify-after-install.py
```

### 创建发布

```bash
# 创建发布包（指定版本号）
python scripts/release/create-release.py 0.1.0
```

---

## 脚本说明

### build/ 目录

| 脚本 | 用途 | 用法 |
|------|------|------|
| `build-wheel.py` | 构建 Python Wheel 分发包 | `python scripts/build/build-wheel.py` |
| `build-mcp.py` | 构建 MCP 安装包 | `python scripts/build/build-mcp.py` |

### verify/ 目录

| 脚本 | 用途 | 用法 |
|------|------|------|
| `verify-before-release.py` | 发布前验证项目状态 | `python scripts/verify/verify-before-release.py` |
| `verify-after-install.py` | 安装后验证功能 | `python scripts/verify/verify-after-install.py` |

### release/ 目录

| 脚本 | 用途 | 用法 |
|------|------|------|
| `create-release.py` | 创建发布包和 Git 标签 | `python scripts/release/create-release.py <version>` |

---

## 详细文档

完整的脚本使用指南请参考: [docs/SCRIPTS_GUIDE.md](../docs/SCRIPTS_GUIDE.md)

---

## 依赖要求

所有脚本需要 Python 3.10+ 环境。部分脚本需要额外依赖：

- `build-wheel.py`: 需要 `build` 包
- `verify-before-release.py`: 需要 `pytest`, `black`, `ruff`

安装开发依赖：
```bash
pip install -e ".[dev]"
```

---

**维护者**: Maric
**文档版本**: v0.1.0
