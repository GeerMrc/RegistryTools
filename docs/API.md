# RegistryTools API 文档

> **版本**: v0.1.0
> **更新日期**: 2026-01-04
> **项目**: RegistryTools - MCP Tool Registry Server

---

## 概述

RegistryTools 提供以下 MCP 工具接口：

1. `search_tools` - 搜索可用的 MCP 工具
2. `get_tool_definition` - 获取工具的完整定义
3. `list_tools_by_category` - 按类别列出工具
4. `register_tool` - 动态注册新工具

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
| `search_method` | string | 否 | "bm25" | 搜索方法 (regex/bm25/embedding) |
| `limit` | integer | 否 | 5 | 返回结果数量 |

#### 搜索方法

| 方法 | 描述 | 准确率 | 速度 |
|------|------|--------|------|
| `regex` | 正则表达式精确匹配 | 56% | 最快 |
| `bm25` | BM25 关键词搜索 | 64% | 快 |
| `embedding` | 语义向量搜索 | 75%+ | 慢 |

#### 返回值

返回 Markdown 格式的搜索结果：

```markdown
## 搜索结果

1. **github.create_pull_request**
   - 描述: Create a new pull request in a GitHub repository
   - 相关度: 0.85

2. **gitlab.merge_request**
   - 描述: Create a merge request in GitLab
   - 相关度: 0.72
```

#### 示例

```python
# 搜索 GitHub 相关工具
search_tools("github create pull request", "bm25", 5)

# 搜索 AWS 工具
search_tools("aws cost billing", "bm25", 3)
```

---

### get_tool_definition

获取指定工具的完整 JSON Schema 定义

#### 语法

```python
get_tool_definition(tool_name: str) -> str
```

#### 参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `tool_name` | string | 是 | 工具名称 |

#### 返回值

返回工具的完整 JSON Schema 定义：

```json
{
  "name": "github.create_pull_request",
  "description": "Create a new pull request in a GitHub repository",
  "input_schema": {
    "type": "object",
    "properties": {
      "owner": {"type": "string"},
      "repo": {"type": "string"},
      "title": {"type": "string"},
      "body": {"type": "string"},
      "head": {"type": "string"},
      "base": {"type": "string"}
    },
    "required": ["owner", "repo", "title", "head", "base"]
  }
}
```

**注意**: 调用此工具会自动更新工具的使用频率。

#### 示例

```python
# 获取工具定义
get_tool_definition("github.create_pull_request")

# 不存在的工具
get_tool_definition("non.existent.tool")
# 返回: "错误: 工具 'non.existent.tool' 不存在"
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
| `category` | string | 是 | - | 工具类别 |
| `limit` | integer | 否 | 20 | 返回结果数量 |

#### 支持的类别

| 类别 | 描述 |
|------|------|
| `github` | GitHub 相关工具 |
| `gitlab` | GitLab 相关工具 |
| `slack` | Slack 相关工具 |
| `aws` | AWS 相关工具 |
| `database` | 数据库操作 |
| `notification` | 通知类工具 |

#### 返回值

返回该类别下的所有工具：

```markdown
## 类别 'github' 下的工具 (15 个)

- **github.create_pull_request**: Create a new pull request
- **github.merge_pull_request**: Merge a pull request
- **github.add_review_comment**: Add a comment to a PR review
- ...
```

#### 示例

```python
# 列出所有 GitHub 工具
list_tools_by_category("github", 20)

# 列出前 5 个 Slack 工具
list_tools_by_category("slack", 5)
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
| `name` | string | 是 | - | 工具名称 |
| `description` | string | 是 | - | 工具描述 |
| `category` | string | 否 | None | 工具类别 |
| `tags` | list[string] | 否 | [] | 工具标签 |

#### 返回值

返回注册结果：

```
工具 'my.custom.tool' 已成功注册
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

### ToolRegistry

工具注册表核心类

```python
from RegistryTools.registry import ToolRegistry

# 创建注册表
registry = ToolRegistry(storage)

# 注册工具
registry.register(tool_metadata)

# 搜索工具
results = registry.search("github pull request", SearchMethod.BM25, 5)

# 获取工具
tool = registry.get_tool("github.create_pull_request")

# 更新使用频率
registry.update_usage("github.create_pull_request")
```

### SearchAlgorithm

搜索算法基类

```python
from RegistryTools.search import BM25Search, RegexSearch

# 创建搜索算法
search = BM25Search()
search.index(tools)

# 执行搜索
results = search.search("query", tools, 5)
```

---

## 错误处理

### 错误代码

| 代码 | 描述 |
|------|------|
| `TOOL_NOT_FOUND` | 工具不存在 |
| `INVALID_SEARCH_METHOD` | 无效的搜索方法 |
| `INVALID_CATEGORY` | 无效的类别 |
| `REGISTRATION_FAILED` | 工具注册失败 |

### 错误响应格式

```json
{
  "error": "TOOL_NOT_FOUND",
  "message": "工具 'non.existent.tool' 不存在"
}
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
