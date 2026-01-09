# RegistryTools API 文档

> **版本**: v0.1.0
> **更新日期**: 2026-01-05
> **项目**: RegistryTools - MCP Tool Registry Server
>
> **⚠️ PyPI 发布状态**: **RegistryTools 尚未发布到 PyPI**
>
> **当前仅支持本地安装**:
>
> ```bash
> # 从源码安装
> git clone https://github.com/GeerMrc/RegistryTools.git
> cd RegistryTools
> pip install -e .
> ```
>
> **安装后配置命令**:
> ```json
> {
>   "command": "registry-tools"
> }
> ```
>
> ❌ **不可用**: `uvx registry-tools`（仅在 PyPI 发布后可用）

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
    temperature: ToolTemperature = ToolTemperature.COLD  # 工具温度级别
    input_schema: Optional[dict] = None     # 输入 Schema
    output_schema: Optional[dict] = None    # 输出 Schema
```

**temperature 字段说明**:

| 值 | 使用频率 | 描述 |
|----|---------|------|
| `HOT` | ≥ 10 次 | 热工具，启动时预加载到内存 |
| `WARM` | 3-9 次 | 温工具，按需加载并缓存 |
| `COLD` | < 3 次 | 冷工具，延迟加载（默认） |

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

## 配置选项

完整的环境变量、CLI 参数和性能调优配置请参见 [配置指南](CONFIGURATION.md)。

### 快速参考

**常用环境变量**:
- `REGISTRYTOOLS_DATA_PATH` - 数据目录路径（默认: `~/.RegistryTools`）
- `REGISTRYTOOLS_TRANSPORT` - 传输协议（默认: `stdio`）
- `REGISTRYTOOLS_LOG_LEVEL` - 日志级别（默认: `INFO`）
- `REGISTRYTOOLS_ENABLE_AUTH` - 启用 API Key 认证（默认: `false`）

**配置优先级**: 环境变量 > CLI 参数 > 默认值

**详细配置**:
- 环境变量配置 → [配置指南 - 环境变量配置](CONFIGURATION.md#环境变量配置)
- CLI 参数配置 → [配置指南 - CLI 参数配置](CONFIGURATION.md#cli-参数配置)
- 日志配置 → [配置指南 - 日志配置](CONFIGURATION.md#日志配置)
- API Key 认证 → [配置指南 - API Key 认证配置](CONFIGURATION.md#api-key-认证配置)
- 冷热工具分离 → [配置指南 - 冷热工具分离配置](CONFIGURATION.md#冷热工具分离配置)
- 性能调优 → [配置指南 - 性能调优配置](CONFIGURATION.md#性能调优配置)

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

## API Key 认证 (Phase 15)

RegistryTools 支持通过 API Key 进行身份验证，保护 HTTP 模式下的服务访问。

### 启用认证

**命令行参数**:
```bash
registry-tools --transport http --host 0.0.0.0 --port 8000 --enable-auth
```

**环境变量**:
```bash
REGISTRYTOOLS_ENABLE_AUTH=true registry-tools --transport http
```

### API Key 格式

```
rtk_<64-char-hex>
```

- 前缀: `rtk` (RegistryTools Key)
- 随机部分: 64 个十六进制字符（32 字节，256 位安全随机）

### 权限级别

| 权限 | 描述 | 允许操作 |
|------|------|----------|
| `READ` | 只读 | search_tools, get_tool_definition, list_tools_by_category |
| `WRITE` | 读写 | 上述 + register_tool |
| `ADMIN` | 管理员 | 所有操作 + API Key 管理 |

### 客户端认证

**HTTP Header 方式 1**:
```
X-API-Key: rtk_a1b2c3d4e5f6789012345678901234567890123456789012345678901234
```

**HTTP Header 方式 2 (Bearer Token)**:
```
Authorization: Bearer rtk_a1b2c3d4e5f6789012345678901234567890123456789012345678901234
```

### 命令行管理 API Key

**创建 API Key**:
```bash
# 创建只读 Key
registry-tools api-key create "My Read Key" --permission read

# 创建读写 Key
registry-tools api-key create "My Write Key" --permission write

# 创建带过期时间的 Key (1 小时)
registry-tools api-key create "Temp Key" --expires-in 3600

# 创建带所有者的 Key
registry-tools api-key create "Team Key" --owner team@example.com
```

**列出 API Key**:
```bash
# 列出所有 Key
registry-tools api-key list

# 按所有者筛选
registry-tools api-key list --owner user@example.com
```

**删除 API Key**:
```bash
registry-tools api-key delete <key-id>
```

### Python API

**创建启用认证的服务器**:
```python
from pathlib import Path
from registrytools.server import create_server, create_auth_middleware_for_server

data_path = Path("~/.RegistryTools")

# 创建认证中间件
auth_middleware = create_auth_middleware_for_server(data_path)

# 创建服务器并启用认证
mcp_server = create_server(data_path, auth_middleware=auth_middleware)
mcp_server.run(transport="http", host="0.0.0.0", port=8000)
```

**使用 API Key 存储**:
```python
from registrytools.auth import (
    APIKeyStorage,
    APIKeyPermission,
    generate_api_key,
)

# 创建存储
storage = APIKeyStorage("~/.RegistryTools/api_keys.db")

# 生成 API Key
api_key = generate_api_key(
    name="My API Key",
    permission=APIKeyPermission.READ,
    expires_in=3600  # 1 小时
)

# 保存到存储
storage.save(api_key)

# 验证 API Key
retrieved_key = storage.get_by_api_key(api_key.api_key)
if retrieved_key and retrieved_key.is_valid():
    print(f"认证成功: {retrieved_key.name}")
```

**使用认证中间件**:
```python
from registrytools.auth import APIKeyAuthMiddleware, APIKeyStorage

# 创建中间件
storage = APIKeyStorage("~/.RegistryTools/api_keys.db")
middleware = APIKeyAuthMiddleware(storage)

# 从 Headers 认证
headers = {"X-API-Key": "rtk_xxx..."}
result = middleware.authenticate_from_headers(headers)

if result.success:
    print(f"认证成功: {result.key_metadata.name}")
else:
    print(f"认证失败: {result.error}")

# 带权限检查的认证
result = middleware.authenticate(
    "rtk_xxx...",
    required_permission=APIKeyPermission.WRITE
)
```

### 安全注意事项

1. **HTTPS**: 生产环境必须使用 HTTPS 传输 API Key
2. **密钥保护**: API Key 创建后只显示一次，请妥善保存
3. **权限最小化**: 根据使用场景授予最小必要权限
4. **定期轮换**: 建议定期更换 API Key
5. **过期设置**: 为临时使用场景设置过期时间

### 数据模型

**APIKey**:
```python
class APIKey(BaseModel):
    key_id: str                              # 唯一标识符 (UUID)
    api_key: str                             # 密钥值
    name: str                                # 名称/描述
    permission: APIKeyPermission            # 权限级别
    scope: APIKeyScope                      # 作用范围
    is_active: bool                          # 是否激活
    created_at: datetime                     # 创建时间
    expires_at: Optional[datetime]          # 过期时间
    last_used_at: Optional[datetime]        # 最后使用时间
    usage_count: int                         # 使用次数
    owner: Optional[str]                     # 所有者
    metadata: Optional[dict[str, str]]      # 额外元数据
```

---

## 相关文档

### 核心文档
- [USER_GUIDE.md](USER_GUIDE.md) - 用户使用指南
- [ARCHITECTURE.md](ARCHITECTURE.md) - 架构设计文档
- [CONFIGURATION.md](CONFIGURATION.md) - 配置参数说明

### 配置指南
- [CLAUDE_CONFIG.md](CLAUDE_CONFIG.md) - Claude Desktop 配置
- [IDE_CONFIG.md](IDE_CONFIG.md) - IDE (VS Code/Cursor) 配置
- [INSTALLATION.md](INSTALLATION.md) - 安装指南

### 支持文档
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - 故障排除
- [BEST_PRACTICES.md](BEST_PRACTICES.md) - 最佳实践
- [CHANGELOG.md](CHANGELOG.md) - 变更日志

---

**维护者**: Maric
**文档版本**: v0.1.0
