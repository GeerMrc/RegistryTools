# RegistryTools 发布指南

**版本**: v0.2.0
**更新日期**: 2026-01-10
**项目**: RegistryTools - MCP Tool Registry Server

本文档描述如何将 RegistryTools 发布到 PyPI。

---

## 前置条件

### 必要工具

- Python 3.10+
- pip
- [build](https://pypa-build.readthedocs.io/)
- [twine](https://twine.readthedocs.io/)

### 安装构建工具

```bash
pip install build twine
```

---

## 发布前检查

### 1. 运行验证脚本

```bash
python scripts/verify/verify-before-release.py
```

该脚本会检查：
- 代码格式 (Black)
- 代码质量 (Ruff)
- 类型检查 (MyPy)
- 测试覆盖率
- 文档完整性

### 2. 手动验证

```bash
# 运行测试
pytest tests/ -v

# 代码格式检查
black --check src/registrytools tests/

# 代码质量检查
ruff check src/registrytools tests/

# 类型检查
mypy src/registrytools
```

### 3. 更新版本号

如果需要发布新版本，请更新 `pyproject.toml` 中的版本号：

```toml
[project]
name = "registry-tools"
version = "0.2.0"  # 更新版本号
```

同时更新 `src/registrytools/__init__.py`：

```python
__version__ = "0.2.0"
```

### 4. 更新 CHANGELOG.md

在 `docs/CHANGELOG.md` 中添加版本变更记录：

```markdown
## [0.2.0] - 2026-01-05

### 新增
- 新功能描述

### 修复
- 问题修复描述

### 变更
- 变更描述
```

---

## 构建发布包

### 1. 清理旧的构建文件

```bash
rm -rf dist/ build/ *.egg-info
```

### 2. 构建源码包和 Wheel 包

```bash
python -m build
```

这将生成：
- `dist/registry-tools-{version}.tar.gz` (源码包)
- `dist/registry-tools-{version}-py3-none-any.whl` (Wheel 包)

### 3. 验证构建包

```bash
# 检查包内容
twine check dist/*
```

---

## 测试发布

### 1. 发布到 TestPyPI

首先配置 TestPyPI 凭据（如果尚未配置）：

```bash
# 创建 ~/.pypirc
[distutils]
index-servers =
    pypi
    testpypi

[testpypi]
username = __token__
password = <testpypi-token>
```

发布到 TestPyPI：

```bash
twine upload --repository testpypi dist/*
```

### 2. 从 TestPyPI 安装测试

```bash
pip install --index-url https://test.pypi.org/simple/ registry-tools
```

验证安装是否成功：

```bash
registry-tools --version
registry-tools --help
```

### 3. 清理 TestPyPI 测试环境

```bash
pip uninstall -y registry-tools
```

---

## 正式发布

### 1. 发布到 PyPI

```bash
twine upload dist/*
```

### 2. 验证 PyPI 发布

从 PyPI 安装：

```bash
pip install registry-tools
```

验证功能：

```bash
registry-tools --version
registry-tools --help
```

### 3. 创建 GitHub Release

1. 访问 GitHub Releases 页面
2. 点击 "Draft a new release"
3. 填写发布信息：
   - **Tag**: `v0.2.0`
   - **Title**: `RegistryTools v0.2.0`
   - **Description**: 从 CHANGELOG.md 复制变更内容
4. 上传构建包
5. 点击 "Publish release"

---

## 发布后检查

### 1. 验证安装

```bash
# 使用 uvx 测试
uvx registry-tools --version

# 或使用 pip 安装测试
pip install registry-tools
registry-tools --help
```

### 2. 验证 MCP 集成

测试在不同 MCP 客户端中的集成：

**Claude Desktop 配置**:

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

**HTTP 模式测试**:

```bash
registry-tools --transport http --port 8000
```

---

## 回滚/重新发布

如果发现问题需要重新发布：

### 1. 删除已发布的版本

**注意**: PyPI 不允许删除已发布的版本，只能发布新版本修复问题。

### 2. 发布新版本

1. 更新版本号（例如 `0.2.1`）
2. 修复问题
3. 重新构建和发布

```bash
# 更新版本号后
rm -rf dist/ build/
python -m build
twine upload dist/*
```

---

## 常见问题

### Q: 上传失败提示 403 错误

A: 检查 PyPI Token 是否正确配置，或重新生成 Token。

### Q: 构建失败提示缺少依赖

A: 确保 `pyproject.toml` 中所有依赖都正确声明。

### Q: TestPyPI 上传成功但无法安装

A: TestPyPI 可能有延迟，等待几分钟后重试。

---

**维护者**: Maric
**文档版本**: v1.0
