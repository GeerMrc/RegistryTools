# RegistryTools 用户指南

> **版本**: v1.0
> **更新日期**: 2026-01-05
> **项目**: RegistryTools - MCP Tool Registry Server

本文档介绍如何使用 RegistryTools 进行工具搜索和管理。

---

## 快速开始

### 概述

RegistryTools 是一个独立的 MCP Tool Registry Server，提供通用的工具搜索和发现能力。

### 核心价值

- **减少 Token 消耗 85%**: 从 ~77K 降至 ~8.7K（按需加载工具）
- **提升准确率**: 工具选择准确率从 49% 提升至 74%
- **解耦复用**: 独立部署，任何 MCP 客户端都可连接

---

## MCP 工具接口

### search_tools - 搜索工具

搜索可用的 MCP 工具。

#### 参数

- `query` (string): 搜索查询
- `method` (string): 搜索方法，可选值：`regex`、`bm25`
- `limit` (integer): 返回结果数量，默认 10

#### 示例

```python
# 使用 BM25 搜索 "github pull request" 相关工具
search_tools("github create pull request", "bm25", 5)

# 使用正则表达式精确匹配
search_tools("github.*pull", "regex", 10)
```

#### 返回结果

```json
[
  {
    "tool_name": "github.create_pull_request",
    "description": "Create a pull request in a GitHub repository",
    "score": 0.95,
    "match_reason": "关键词匹配: github, create, pull, request"
  }
]
```

### get_tool_definition - 获取工具定义

获取指定工具的完整定义。

#### 参数

- `tool_name` (string): 工具名称

#### 示例

```python
get_tool_definition("github.create_pull_request")
```

#### 返回结果

```json
{
  "name": "github.create_pull_request",
  "description": "Create a pull request in a GitHub repository",
  "input_schema": {
    "type": "object",
    "properties": {
      "owner": {"type": "string"},
      "repo": {"type": "string"},
      "title": {"type": "string"}
    },
    "required": ["owner", "repo", "title"]
  }
}
```

### list_tools_by_category - 按类别列出工具

按类别列出可用的工具。

#### 参数

- `category` (string): 工具类别，使用 `"all"` 列出所有类别
- `limit` (integer): 返回结果数量，默认 20

#### 示例

```python
# 列出所有 GitHub 工具
list_tools_by_category("github", 20)

# 列出所有类别
list_tools_by_category("all", 100)
```

### register_tool - 注册工具

动态注册新工具到注册表。

#### 参数

- `name` (string): 工具名称
- `description` (string): 工具描述
- `category` (string): 工具类别
- `tags` (list): 工具标签

#### 示例

```python
register_tool(
    name="my.custom.tool",
    description="A custom tool for specific purpose",
    category="custom",
    tags=["utility", "helper"]
)
```

---

## MCP 资源接口

### registry://stats - 统计信息

获取工具注册表的统计信息。

#### 返回结果

```json
{
  "total_tools": 26,
  "categories": ["github", "gitlab", "filesystem"],
  "most_used_tools": [
    {"name": "github.create_pull_request", "count": 42}
  ]
}
```

### registry://categories - 类别列表

获取所有工具类别。

#### 返回结果

```json
{
  "categories": ["github", "gitlab", "filesystem", "utility"]
}
```

---

## 搜索算法

### Regex 搜索

- **特点**: 精确匹配，最快
- **适用**: 已知工具名称
- **示例**: `search_tools("github.*pull", "regex")`

### BM25 搜索

- **特点**: 关键词搜索，支持中文分词
- **适用**: 语义搜索
- **示例**: `search_tools("创建 PR", "bm25")`

---

## 使用场景

### 场景 1: 在 Claude Desktop 中使用

配置 `claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "RegistryTools": {
      "command": "uvx",
      "args": ["Registry-Tools"]
    }
  }
}
```

然后在对话中：

```
用户: 帮我创建一个 GitHub PR

Claude: 我来搜索创建 PR 的工具...
[调用 search_tools("github create pull request", "bm25")]
找到工具: github.create_pull_request
```

### 场景 2: 作为远程 HTTP 服务

启动 HTTP 服务器：

```bash
registry-tools --transport http --port 8000
```

客户端配置：

```json
{
  "mcpServers": {
    "RegistryTools": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

### 场景 3: 自定义数据目录

```bash
registry-tools --data-path /custom/path
```

配置：

```json
{
  "mcpServers": {
    "RegistryTools": {
      "command": "uvx",
      "args": ["Registry-Tools", "--data-path", "/custom/path"]
    }
  }
}
```

---

## 最佳实践

### 1. 选择合适的搜索方法

- **已知工具名称**: 使用 `regex`
- **语义搜索**: 使用 `bm25`
- **中文搜索**: 使用 `bm25`（支持中文分词）

### 2. 优化搜索结果

- 使用更具体的关键词
- 调整 `limit` 参数获取更多结果
- 按类别筛选缩小范围

### 3. 工具命名规范

推荐的工具命名格式：

```
<provider>.<action>_<resource>
```

示例：
- `github.create_pull_request`
- `gitlab.merge_request`
- `filesystem.read_file`

---

## 高级用法

### 冷热工具分离

RegistryTools 自动将工具分为三层：

- **HOT** (热工具): 使用频率 ≥ 10
- **WARM** (温工具): 使用频率 3-9
- **COLD** (冷工具): 使用频率 < 3

热工具会优先加载，提升搜索性能。

### 自定义工具集

可以通过编程方式注册自定义工具：

```python
from registrytools import ToolRegistry, ToolMetadata

registry = ToolRegistry()

# 注册自定义工具
registry.register(
    ToolMetadata(
        name="my.tool",
        description="My custom tool",
        category="custom",
        tags=["utility"]
    )
)
```

---

## 故障排除

### 问题: 搜索结果为空

**可能原因**:
1. 查询关键词不匹配
2. 工具未注册

**解决方案**:
1. 尝试使用不同的关键词
2. 使用 `list_tools_by_category("all")` 查看所有工具
3. 检查工具是否正确注册

### 问题: HTTP 服务无法启动

**可能原因**:
1. 端口已被占用
2. 防火墙阻止

**解决方案**:
1. 使用不同的端口：`--port 9000`
2. 检查防火墙设置

---

## 相关文档

- [安装指南](INSTALLATION.md)
- [架构设计](ARCHITECTURE.md)
- [API 文档](API.md)
- [发布指南](PUBLISHING.md)

---

**维护者**: Maric
**文档版本**: v1.0
