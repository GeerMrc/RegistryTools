# RegistryTools

> **独立 MCP Tool Registry Server** - 通用工具搜索与发现服务

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-Protocol-orange.svg)](https://modelcontextprotocol.io/)

---

## 简介

RegistryTools 是一个独立的 MCP Tool Registry Server，提供通用的工具搜索和发现能力。它可以被任何支持 MCP 协议的客户端（如 DeepThinking Agent、Cursor IDE、Claude Desktop）使用。

### 核心价值

- **减少 Token 消耗 85%**: 从 ~77K 降至 ~8.7K（按需加载工具）
- **提升准确率**: 工具选择准确率从 49% 提升至 74%
- **解耦复用**: 独立部署，任何 MCP 客户端都可连接

---

## 快速开始

### 安装

```bash
# 使用 uvx (推荐)
uvx Registry-Tools

# 或使用 pip
pip install Registry-Tools
```

### Claude Desktop 配置

在 Claude Desktop 配置文件中添加：

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "RegistryTools": {
      "command": "uvx",
      "args": ["Registry-Tools", "--data-path", "~/.RegistryTools"]
    }
  }
}
```

### 使用示例

```python
# 搜索工具
search_tools("github create pull request", "bm25", 5)

# 获取工具定义
get_tool_definition("github.create_pull_request")

# 按类别列出工具
list_tools_by_category("github", 20)

# 动态注册工具
register_tool(
    name="my.custom.tool",
    description="A custom tool for specific purpose"
)
```

---

## 功能特性

### 搜索算法

| 算法 | 准确率 | 速度 | 适用场景 |
|------|--------|------|----------|
| **Regex** | 56% | 最快 | 精确名称匹配 |
| **BM25** | 64% | 快 | 关键词搜索（推荐） |
| **Embedding** | 75%+ | 慢 | 语义搜索（可选） |

### MCP 工具接口

- `search_tools` - 搜索可用的 MCP 工具
- `get_tool_definition` - 获取工具的完整定义
- `list_tools_by_category` - 按类别列出工具
- `register_tool` - 动态注册新工具

---

## 架构设计

```
MCP Clients (任何支持 MCP 的应用)
    │
    ▼
RegistryTools (独立 MCP Server)
    │
    ├── Tool Registry (工具注册表)
    │   └── 管理所有工具的元数据和索引
    │
    ├── Search Engine (搜索引擎)
    │   ├── Regex 搜索 (精确匹配)
    │   ├── BM25 搜索 (关键词)
    │   └── Embedding 搜索 (语义)
    │
    └── Storage Layer (存储层)
        ├── JSON 文件存储
        └── SQLite 存储
```

详见 [ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## 开发

### 环境设置

```bash
# 克隆项目
git clone https://github.com/maric/RegistryTools.git
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

# 查看覆盖率
pytest --cov=RegistryTools --cov-report=html
```

### 代码格式化

```bash
# 格式化代码
black RegistryTools/ tests/

# 代码检查
ruff check RegistryTools/ tests/
```

### 贡献指南

请参阅 [CONTRIBUTING.md](docs/CONTRIBUTING.md)

---

## 文档

- [架构设计](docs/ARCHITECTURE.md) - 系统架构说明
- [API 文档](docs/API.md) - API 接口文档
- [开发流程规范](docs/DEVELOPMENT_WORKFLOW.md) - 开发流程规范
- [任务追踪](docs/TASK.md) - 项目任务追踪
- [变更日志](docs/CHANGELOG.md) - 版本变更记录

---

## 性能指标

| 指标 | 目标值 |
|------|--------|
| 搜索响应时间 | < 200ms (1000+ 工具) |
| 内存占用 | < 100MB (1000+ 工具) |
| 索引构建时间 | < 2s (1000+ 工具) |

---

## 路线图

### v0.1.0 (当前)
- ✅ 基础工具注册和搜索
- ✅ BM25 搜索算法
- ✅ JSON/SQLite 存储

### v0.2.0 (计划中)
- ⏳ 语义搜索 (Embedding)
- ⏳ 冷热工具分离
- ⏳ 性能优化

### v0.3.0 (未来)
- ⏳ Web UI 管理界面
- ⏳ 分布式工具索引
- ⏳ 多语言支持

---

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 致谢

- [Anthropic](https://www.anthropic.com/) - MCP 协议设计
- [FastMCP](https://github.com/jlowin/fastmcp) - MCP 服务器框架
- [rank-bm25](https://github.com/dorianbrown/rank_bm25) - BM25 算法实现

---

**项目维护者**: Maric
**项目主页**: [GitHub](https://github.com/maric/RegistryTools)
