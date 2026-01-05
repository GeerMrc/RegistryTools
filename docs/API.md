# RegistryTools API 文档

> **版本**: v0.1.0
> **更新日期**: 2026-01-05
> **项目**: RegistryTools - MCP Tool Registry Server

---

## 概述

RegistryTools 提供以下 MCP 工具接口：

1. `search_tools` - 搜索可用的 MCP 工具
2. `get_tool_definition` - 获取工具的完整定义
3. `list_tools_by_category` - 按类别列出工具
4. `register_tool` - 动态注册新工具

以及以下 MCP 资源接口：

1. `registry://stats` - 工具注册表统计信息
2. `registry://categories` - 所有工具类别

---

## MCP 工具接口

### search_tools

搜索可用的 MCP 工具

#### 语法

```python
search_tools(
    query: str,
    search_method: str = "bm25",
    limit: int = 5
) -> str
```

#### 参数

| 参数 | 类型 | 必需 | 默认值 | 描述 |
|------|------|------|--------|------|
| `query` | string | 是 | - | 搜索查询，支持关键词或自然语言描述 |
| `search_method` | string | 否 | "bm25" | 搜索方法 (regex/bm25) |
| `limit` | integer | 否 | 5 | 返回结果数量 |

#### 搜索方法

| 方法 | 描述 | 准确率 | 速度 |
|------|------|--------|------|
| `regex` | 正则表达式精确匹配 | 高 | 最快 |
| `bm25` | BM25 关键词搜索（支持中文分词） | 高 | 快 |

#### 返回值

返回 JSON 格式字符串的搜索结果：

```json
[
  {
    "tool_name": "github.create_pull_request",
    "description": "Create a new pull request in a GitHub repository",
    "score": 0.85,
    "match_reason": "bm25_keyword_similarity"
  },
  {
    "tool_name": "gitlab.merge_request",
    "description": "Create a merge request in GitLab",
    "score": 0.72,
    "match_reason": "bm25_keyword_similarity"
  }
]
```

#### 示例

```python
# 搜索 GitHub 相关工具
search_tools("github create pull request", "bm25", 5)

# 搜索 AWS 工具
search_tools("aws s3 upload", "bm25", 3)
```

---

### get_tool_definition

获取指定工具的完整元数据

#### 语法

```python
get_tool_definition(tool_name: str) -> str
```

#### 参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `tool_name` | string | 是 | 工具名称 |

#### 返回值

返回工具的完整元数据，JSON 格式字符串：

```json
{
  "name": "github.create_pull_request",
  "description": "Create a new pull request in a GitHub repository",
  "mcp_server": "github",
  "tags": ["github", "git", "pr"],
  "category": "github",
  "use_frequency": 5,
  "defer_loading": true
}
```

#### 示例

```python
# 获取工具定义
get_tool_definition("github.create_pull_request")
```

---

### list_tools_by_category

按类别列出工具

#### 语法

```python
list_tools_by_category(
    category: str,
    limit: int = 20
) -> str
```

#### 参数

| 参数 | 类型 | 必需 | 默认值 | 描述 |
|------|------|------|--------|------|
| `category` | string | 是 | - | 工具类别，使用 "all" 列出所有类别 |
| `limit` | integer | 否 | 20 | 返回结果数量 |

#### 返回值

返回 JSON 格式字符串的结果：

**列出指定类别：**

```json
{
  "category": "github",
  "count": 8,
  "tools": [
    {
      "name": "github.create_pull_request",
      "description": "Create a new pull request in a GitHub repository",
      "tags": ["github", "git", "pr"]
    },
    {
      "name": "github.merge_pull_request",
      "description": "Merge a pull request in a GitHub repository",
      "tags": ["github", "git", "merge"]
    }
  ]
}
```

**列出所有类别：**

```json
{
  "categories": ["github", "gitlab", "slack", "aws", "google", "utilities", "database", "filesystem"]
}
```

#### 示例

```python
# 列出所有 GitHub 工具
list_tools_by_category("github", 20)

# 列出所有类别
list_tools_by_category("all")
```

---

### register_tool

动态注册新工具

#### 语法

```python
register_tool(
    name: str,
    description: str,
    category: str = None,
    tags: list[str] = None
) -> str
```

#### 参数

| 参数 | 类型 | 必需 | 默认值 | 描述 |
|------|------|------|--------|------|
| `name` | string | 是 | - | 工具名称（唯一标识符） |
| `description` | string | 是 | - | 工具描述 |
| `category` | string | 否 | None | 工具类别 |
| `tags` | list[string] | 否 | [] | 工具标签列表 |

#### 返回值

返回 JSON 格式字符串的注册结果：

```json
{
  "success": true,
  "message": "工具已注册: my.custom.tool",
  "tool": {
    "name": "my.custom.tool",
    "description": "A custom tool for specific purpose",
    "category": "custom",
    "tags": ["custom", "utility"]
  }
}
```

#### 示例

```python
# 注册简单工具
register_tool(
    name="my.custom.tool",
    description="A custom tool for specific purpose"
)

# 注册带类别和标签的工具
register_tool(
    name="data.processor",
    description="Process data from various sources",
    category="data",
    tags=["etl", "pipeline", "transformation"]
)
```

---

## MCP 资源接口

### registry://stats

获取工具注册表统计信息

#### 返回值

```json
{
  "total_tools": 26,
  "total_categories": 8,
  "categories": ["github", "slack", "aws", "google", "utilities", "database", "filesystem"],
  "most_used": [
    {
      "name": "github.create_pull_request",
      "description": "Create a new pull request in a GitHub repository",
      "use_count": 15
    }
  ]
}
```

---

### registry://categories

获取所有工具类别

#### 返回值

```json
{
  "count": 8,
  "categories": ["github", "slack", "aws", "google", "utilities", "database", "filesystem"]
}
```

---

## 数据模型

### ToolMetadata

工具元数据模型

```python
class ToolMetadata(BaseModel):
    name: str                              # 工具名称
    description: str                        # 工具描述
    mcp_server: Optional[str] = None        # 所属 MCP 服务器
    defer_loading: bool = True              # 是否延迟加载
    tags: set[str] = set()                 # 标签
    category: Optional[str] = None          # 类别
    use_frequency: int = 0                  # 使用频率
    last_used: Optional[datetime] = None    # 最后使用时间
    input_schema: Optional[dict] = None     # 输入 Schema
    output_schema: Optional[dict] = None    # 输出 Schema
```

### ToolSearchResult

搜索结果模型

```python
class ToolSearchResult(BaseModel):
    tool_name: str                          # 工具名称
    description: str                        # 工具描述
    score: float                            # 相关度分数 (0-1)
    match_reason: str                       # 匹配原因
```

---

## Python API

### 创建服务器

```python
from pathlib import Path
from registrytools.server import create_server, create_server_with_sqlite

# 使用 JSON 存储
mcp_server = create_server(Path("/path/to/data"))

# 使用 SQLite 存储
mcp_server = create_server_with_sqlite(Path("/path/to/data"))

# 运行服务器
mcp_server.run()
```

### ToolRegistry

工具注册表核心类

```python
from registrytools.registry import ToolRegistry
from registrytools.registry.models import SearchMethod

# 创建注册表
registry = ToolRegistry()

# 注册工具
registry.register(tool_metadata)

# 搜索工具
results = registry.search("github pull request", SearchMethod.BM25, 5)

# 获取工具
tool = registry.get_tool("github.create_pull_request")

# 更新使用频率
registry.update_usage("github.create_pull_request")

# 列出类别
categories = registry.list_categories()

# 按类别列出工具
github_tools = registry.list_tools(category="github")
```

---

## 错误处理

### 错误响应

所有错误通过异常抛出：

| 异常类型 | 描述 |
|----------|------|
| `ValueError` | 工具不存在、搜索方法无效、工具已存在 |

### 示例

```python
try:
    get_tool_definition("non.existent.tool")
except ValueError as e:
    print(f"错误: {e}")
    # 输出: 错误: 工具不存在: non.existent.tool
```

---

## 性能指标

| 指标 | 目标值 |
|------|--------|
| 搜索响应时间 | < 200ms (1000+ 工具) |
| 内存占用 | < 100MB (1000+ 工具) |
| 索引构建时间 | < 2s (1000+ 工具) |

---

**维护者**: Maric
**文档版本**: v0.1.0
