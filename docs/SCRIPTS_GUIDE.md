# RegistryTools 脚本工具完整使用指南

> **版本**: v0.1.0
> **更新日期**: 2026-01-06
> **项目**: RegistryTools - MCP Tool Registry Server

---

## 概述

`scripts/` 目录包含 RegistryTools 项目开发、构建、验证和发布所需的自动化脚本。这些脚本简化了常见工作流程，确保项目质量和发布一致性。

### 目录结构

```
scripts/
├── build/           # 构建脚本 - 创建分发包
│   ├── build-wheel.py    # 构建 Python Wheel 包
│   └── build-mcp.py      # 构建 MCP 安装包
├── release/         # 发布脚本 - 管理版本发布
│   └── create-release.py # 创建发布包和 Git 标签
├── verify/          # 验证脚本 - 质量检查
│   ├── verify-before-release.py  # 发布前验证
│   └── verify-after-install.py   # 安装后验证
└── README.md        # 本文档
```

---

## 第一部分：构建脚本 (build/)

### 1.1 build-wheel.py - 构建 Wheel 包

构建 Python Wheel 分发包用于 PyPI 发布。

**用法**:
```bash
python scripts/build/build-wheel.py
```

**功能**:
1. 清理旧的构建目录 (`build/`, `dist/`, `*.egg-info`)
2. 使用 `python -m build --wheel` 构建新包
3. 列出生成的包文件及大小

**输出**:
```
============================================================
RegistryTools - Wheel 包构建
============================================================

🧹 清理构建目录...
  已删除: build
  已删除: dist

📦 构建 Wheel包...
* Creating new build for purepython wheel...
... 构建输出 ...

📋 生成的包:
  - registry-tools-0.1.0-py3-none-any.whl (45.2 KB)

============================================================
✅ 构建完成!
============================================================
```

**依赖**:
- Python 3.10+
- `build` 包 (`pip install build`)

**输出位置**:
- `dist/registry-tools-<version>-py3-none-any.whl`

---

### 1.2 build-mcp.py - 构建 MCP 安装包

创建 MCP 服务器安装包，包含配置清单和安装说明。

**用法**:
```bash
python scripts/build/build-mcp.py
```

**功能**:
1. 复制 Wheel 包到 `dist/` 目录
2. 创建 `mcp-manifest.json` 清单文件
3. 生成 `INSTALL.md` 安装说明

**输出文件**:

#### `mcp-manifest.json`
```json
{
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
```

#### `INSTALL.md`
包含完整的安装和配置说明，支持 Claude Desktop、Cline、Cursor 等客户端。

**依赖**:
- 无额外依赖（仅标准库）

---

## 第二部分：验证脚本 (verify/)

### 2.1 verify-before-release.py - 发布前验证

在发布新版本前执行完整的质量检查，确保项目处于可发布状态。

**用法**:
```bash
python scripts/verify/verify-before-release.py
```

**检查项目**:

| 检查项 | 描述 | 状态 |
|--------|------|------|
| **项目结构** | 验证必需目录和文件存在 | ✓ |
| **文档同步** | 确认 TASK.md 包含所有 Phase | ✓ |
| **测试** | 检查测试文件存在并可用 pytest 收集 | ✓ |
| **代码质量** | 运行 Black 和 Ruff 检查 | ✓ |
| **Git 状态** | 验证工作目录干净 | ✓ |

**验证的目录**:
- `docs/`, `src/`, `scripts/`, `tests/`, `examples/`

**验证的文档**:
- `docs/TASK.md`
- `docs/CONTRIBUTING.md`
- `docs/DEVELOPMENT_WORKFLOW.md`
- `docs/ARCHITECTURE.md`
- `docs/API.md`
- `docs/CHANGELOG.md`

**输出示例**:
```
============================================================
RegistryTools - 发布前验证
============================================================

📁 验证项目结构
  ✓ PASS 目录 docs/
  ✓ PASS 目录 src/
  ✓ PASS 目录 scripts/
  ✓ PASS 目录 tests/
  ✓ PASS 目录 examples/
  ✓ PASS 文件 docs/TASK.md
  ...

🧪 验证测试
  ✓ PASS 测试文件 (15 个)
  ✓ PASS pytest 可运行

🔍 验证代码质量
  ✓ PASS 代码格式 (Black)
  ✓ PASS 代码检查 (Ruff)

============================================================
验证总结
============================================================
  PASS 项目结构
  PASS 文档同步
  PASS 测试
  PASS 代码质量
  PASS Git 状态

✅ 所有验证通过，可以发布！
```

**依赖**:
- `pytest` (可选，用于测试验证)
- `black` (代码格式检查)
- `ruff` (代码质量检查)

**退出码**:
- `0` - 所有验证通过
- `1` - 部分验证失败

---

### 2.2 verify-after-install.py - 安装后验证

验证已安装的包是否正常工作。

**用法**:
```bash
python scripts/verify/verify-after-install.py
```

**验证项目**:
1. 检查包导入
2. 验证命令行工具可用
3. 运行基本功能测试

**依赖**:
- 包已安装 (`pip install registry-tools`)

---

## 第三部分：发布脚本 (release/)

### 3.1 create-release.py - 创建发布包

自动化创建版本发布，包括版本号更新、Git 标签、发布说明和打包。

**用法**:
```bash
python scripts/release/create-release.py <version>

# 示例
python scripts/release/create-release.py 0.1.0
```

**执行步骤**:

1. **更新版本号**: 修改 `pyproject.toml` 中的版本号
2. **创建 Git 标签**: 创建带注释的 Git 标签 `v<version>`
3. **创建发布说明**: 生成 `dist/release-notes/v<version>.md`
4. **创建发布包**: 生成 `dist/RegistryTools-<version>.tar.gz`

**输出示例**:
```
============================================================
RegistryTools - 创建发布包 v0.1.0
============================================================

📝 更新版本号到 0.1.0...
  ✓ pyproject.toml 已更新

🏷️  创建 Git 标签 v0.1.0...
  ✓ 标签 v0.1.0 已创建

📝 创建发布说明...
  ✓ 发布说明已创建: dist/release-notes/v0.1.0.md

📦 创建发布包 v0.1.0...
  ✓ 发布包已创建: RegistryTools-0.1.0.tar.gz

============================================================
✅ 发布包创建完成!
============================================================

📂 输出文件:
  - dist/RegistryTools-0.1.0.tar.gz
  - dist/release-notes/v0.1.0.md

📝 下一步:
  1. 检查发布内容: ls -la dist/
  2. 推送标签: git push origin v0.1.0
  3. 发布到 PyPI: python -m twine upload dist/*
```

**生成的文件**:

#### `dist/release-notes/v<version>.md`
```markdown
# RegistryTools v0.1.0 Release Notes

Release Date: 2026-01-06

## 安装

```bash
pip install registry-tools==0.1.0
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
{
  "mcpServers": {
    "RegistryTools": {
      "command": "uvx",
      "args": ["registry-tools==0.1.0", "--data-path", "~/.RegistryTools"]
    }
  }
}
```
```

**依赖**:
- Git (用于创建标签)
- 项目目录必须为 Git 仓库

**注意事项**:
- 如果标签已存在，脚本会警告并跳过
- 手动检查生成的发布包后再推送

---

## 第四部分：完整工作流程

### 4.1 开发到发布完整流程

```bash
# 1. 开发完成后，运行发布前验证
python scripts/verify/verify-before-release.py

# 2. 验证通过后，构建发布包
python scripts/build/build-wheel.py
python scripts/build/build-mcp.py

# 3. 创建发布
python scripts/release/create-release.py 0.1.0

# 4. 检查发布内容
ls -la dist/

# 5. 推送 Git 标签
git push origin v0.1.0

# 6. 发布到 PyPI (需要 twine)
python -m twine upload dist/*

# 7. 安装后验证
pip install registry-tools==0.1.0
python scripts/verify/verify-after-install.py
```

### 4.2 快速构建和测试流程

```bash
# 仅构建 Wheel 包
python scripts/build/build-wheel.py

# 测试安装
pip install --force-reinstall dist/*.whl
registry-tools --help
```

---

## 第五部分：故障排除

### 5.1 常见问题

#### 构建失败

**问题**: `build-wheel.py` 报错 "ModuleNotFoundError"

**解决方案**:
```bash
# 安装 build 依赖
pip install build

# 或使用开发依赖
pip install -e ".[dev]"
```

#### 验证失败

**问题**: `verify-before-release.py` 报告 Black/Ruff 检查失败

**解决方案**:
```bash
# 自动修复格式问题
black src/registrytools/ tests/
ruff check --fix src/registrytools/ tests/

# 重新验证
python scripts/verify/verify-before-release.py
```

#### Git 标签已存在

**问题**: `create-release.py` 报告 "标签已存在"

**解决方案**:
```bash
# 删除现有标签（本地和远程）
git tag -d v0.1.0
git push origin :refs/tags/v0.1.0

# 重新创建
python scripts/release/create-release.py 0.1.0
```

### 5.2 脚本权限问题

如果脚本无法执行（Linux/Mac），确保有执行权限：

```bash
chmod +x scripts/**/*.py
```

---

## 第六部分：开发指南

### 6.1 添加新脚本

1. 在对应目录创建新脚本
2. 添加 shebang (`#!/usr/bin/env python`)
3. 包含文档字符串说明用途和用法
4. 更新本文档

### 6.2 脚本编码规范

- 使用 Python 标准库（除非必要）
- 添加中文文档字符串
- 使用 `pathlib.Path` 处理路径
- 添加适当的错误处理
- 使用彩色输出提升用户体验（参考 `verify-before-release.py`）

---

## 附录

### A. 环境变量

| 环境变量 | 描述 | 默认值 |
|---------|------|--------|
| `PYTHONPATH` | Python 模块搜索路径 | - |
| `REGISTRYTOOLS_DATA_PATH` | 数据目录路径 | `~/.RegistryTools` |

### B. 相关文档

- [PUBLISHING.md](PUBLISHING.md) - PyPI 发布完整流程
- [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) - 开发流程规范
- [TASK.md](TASK.md) - 项目任务追踪

### C. 外部工具

- [build](https://pypa-build.readthedocs.io/) - Python 包构建工具
- [twine](https://twine.readthedocs.io/) - PyPI 上传工具
- [pytest](https://docs.pytest.org/) - 测试框架
- [black](https://black.readthedocs.io/) - 代码格式化
- [ruff](https://docs.astral.sh/ruff/) - 代码检查

---

**维护者**: Maric
**文档版本**: v0.1.0
**项目主页**: [GitHub](https://github.com/maric/RegistryTools)
