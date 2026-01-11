# RegistryTools 贡献指南

**版本**: v0.2.1
**更新日期**: 2026-01-11
**项目**: RegistryTools - MCP Tool Registry Server

感谢您对 RegistryTools 项目的关注！

---

## 项目概述

RegistryTools 是一个独立的 MCP Tool Registry Server，提供通用的工具搜索和发现能力，可用于任何支持 MCP 的客户端。

---

## 如何贡献

### 报告问题

在报告问题前，请先：

1. 检查 [Issues](../../issues) 确认问题未被报告
2. 准备以下信息：
   - 项目版本
   - Python 版本
   - 复现步骤
   - 预期行为与实际行为
   - 错误日志（如有）

### 提交代码

#### 开发流程

1. **Fork 项目**
   ```bash
   git clone https://github.com/YOUR_USERNAME/RegistryTools.git
   cd RegistryTools
   ```

2. **创建功能分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **遵循开发流程规范**
   - 阅读并遵循 [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md)
   - 基于 `docs/TASK.md` 创建任务清单
   - 执行交叉验证

4. **提交代码**
   ```bash
   git add .
   git commit -m "feat(scope): description"
   git push origin feature/your-feature-name
   ```

5. **创建 Pull Request**
   - 填写 PR 模板
   - 关联相关 Issue
   - 等待代码审查

---

## 开发规范

### 代码规范

- **Python 代码**: 遵循 PEP 8 规范
- **格式化**: 使用 Black（line-length=100）
- **类型检查**: 使用 Pyright 或 mypy
- **代码检查**: 使用 Ruff

### 文档规范

- **格式**: 使用 Markdown
- **语言**: 中文
- **更新**: 代码变更时同步更新文档

### Git 提交规范

遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
type(scope): subject

body

footer
```

**类型（type）**：
- `feat`: 新功能
- `fix`: 问题修复
- `docs`: 文档更新
- `test`: 测试相关
- `chore`: 构建工具或辅助工具的变动
- `refactor`: 代码重构
- `perf`: 性能优化
- `ci`: CI 配置文件和脚本的变动
- `style`: 代码格式调整

**示例**：
```
feat(registry): add tool usage statistics tracking

Implement usage frequency tracking for all registered tools.
This enables cold/hot tool separation for optimization.

Closes #1
```

---

## 开发环境设置

### 安装依赖

```bash
# 克隆项目
git clone https://github.com/YOUR_USERNAME/RegistryTools.git
cd RegistryTools

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装开发依赖
pip install -e ".[dev]"
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_registry.py

# 查看覆盖率
pytest --cov=registrytools --cov-report=html
```

### 代码格式化

```bash
# 格式化代码
black src/registrytools/ tests/

# 代码检查
ruff check src/registrytools/ tests/
```

---

## 发布规范

发布流程由项目维护者负责，详见项目开发计划。

### 版本号规范

遵循 [Semantic Versioning](https://semver.org/)：
- `MAJOR.MINOR.PATCH`
- MAJOR: 不兼容的 API 变更
- MINOR: 向后兼容的功能新增
- PATCH: 向后兼容的问题修复

---

## 许可证

本项目采用 MIT 许可证，详见 [LICENSE](../LICENSE) 文件。

---

## 联系方式

- 项目主页: [GitHub Repository](../../)
- 问题反馈: [Issues](../../issues)
- 讨论区: [Discussions](../../discussions)
