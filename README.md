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

### 传输协议

RegistryTools 支持多种 MCP 传输协议:

| 协议 | 适用场景 | 配置方式 |
|------|----------|----------|
| **STDIO** | 本地 CLI 集成 (默认) | `registry-tools` |
| **Streamable HTTP** | 远程服务部署 | `registry-tools --transport http` |

#### STDIO 模式 (默认)

适用于 Claude Desktop、本地脚本等本地集成场景。

**Claude Desktop 配置**:

在 Claude Desktop 配置文件中添加:

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

#### Streamable HTTP 模式 (远程部署)

适用于远程服务、容器化部署、多客户端共享等场景。

**启动 HTTP 服务器**:

```bash
# 使用默认参数 (127.0.0.1:8000)
registry-tools --transport http

# 自定义主机和端口
registry-tools --transport http --host 0.0.0.0 --port 8000

# 自定义路径
registry-tools --transport http --port 8000 --path /api/mcp
```

**客户端连接示例**:

```json
{
  "mcpServers": {
    "RegistryTools": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

### fastmcp.json 配置

使用 `fastmcp.json` 进行声明式配置 (推荐):

```bash
# 使用配置文件启动
fastmcp run fastmcp.json

# 或直接运行 (自动检测当前目录的 fastmcp.json)
fastmcp run
```

**fastmcp.json 示例**:

```json
{
  "$schema": "https://gofastmcp.com/public/schemas/fastmcp.json/v1.json",
  "source": {
    "path": "RegistryTools/__main__.py",
    "entrypoint": "main"
  },
  "deployment": {
    "transport": "http",
    "host": "0.0.0.0",
    "port": 8000,
    "path": "/mcp"
  }
}
```

详见: [fastmcp.json](fastmcp.json) (STDIO 默认配置)
详见: [fastmcp.http.json](fastmcp.http.json) (HTTP 配置示例)

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

| 算法 | 描述 | 速度 | 适用场景 |
|------|------|------|----------|
| **Regex** | 正则表达式精确匹配 | 最快 | 精确名称匹配 |
| **BM25** | BM25 关键词搜索（支持中文分词） | 快 | 关键词搜索（推荐） |

### MCP 工具接口

- `search_tools` - 搜索可用的 MCP 工具
- `get_tool_definition` - 获取工具的完整定义
- `list_tools_by_category` - 按类别列出工具
- `register_tool` - 动态注册新工具

### MCP 资源接口

- `registry://stats` - 工具注册表统计信息
- `registry://categories` - 所有工具类别

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
- [使用示例](examples/) - 代码示例
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

### v0.1.0 (当前 - 2026-01-05)
- ✅ 基础工具注册和搜索
- ✅ BM25 搜索算法（支持中文分词）
- ✅ JSON/SQLite 存储
- ✅ MCP 工具和资源接口
- ✅ STDIO 和 Streamable HTTP 传输协议支持
- ✅ fastmcp.json 配置文件支持
- ✅ 测试覆盖率 88%
- ✅ 完整文档和使用示例
- ✅ 性能优化（索引缓存、冷热工具分离）

### v0.2.0 (计划中)
- ⏳ Embedding 语义搜索
- ⏳ 分布式工具注册
- ⏳ 工具依赖管理
- ⏳ Web UI 管理界面

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
