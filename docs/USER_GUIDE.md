# RegistryTools 用户指南

**版本**: v0.2.0
**更新日期**: 2026-01-10
**项目**: RegistryTools - MCP Tool Registry Server

---

## ⚠️ PyPI 发布状态

> **注意**: RegistryTools 尚未发布到 PyPI，当前仅支持本地开发环境安装。
> 详见 [安装指南 - PyPI 发布状态](INSTALLATION.md#pypi-发布状态)。

---

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
- `search_method` (string): 搜索方法，可选值：`regex`、`bm25`、`embedding`（默认使用环境变量 `REGISTRYTOOLS_SEARCH_METHOD`，未设置时为 `bm25`）
- `limit` (integer): 返回结果数量，默认 5

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
  "mcp_server": "github",
  "category": "github",
  "tags": ["github", "pull-request", "code-review"],
  "use_frequency": 0,
  "temperature": "cold"
}
```

> **注意**: `input_schema` 和 `output_schema` 字段为可选扩展字段，用于存储工具的输入输出 JSON Schema 定义。当前默认工具集中这些字段均为 `null`，预留用于未来集成外部 MCP 服务器的 schema 信息。

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

### unregister_tool - 注销工具

从注册表中移除已注册的工具（Phase 33: 新增）。

#### 参数

- `tool_name` (string): 要注销的工具名称

#### 示例

```python
# 注销自定义工具
unregister_tool("my.custom.tool")
```

#### 注意

- 需要 WRITE 或 ADMIN 权限
- 注销后工具将不再出现在搜索结果中
- 工具的使用频率统计将被保留

### search_hot_tools - 快速搜索热工具

快速搜索热工具和温工具，跳过冷工具以提升搜索性能（Phase 33: 新增）。

#### 参数

- `query` (string): 搜索查询
- `search_method` (string): 搜索方法，可选值：`regex`、`bm25`（默认使用环境变量 `REGISTRYTOOLS_SEARCH_METHOD`，未设置时为 `bm25`）
- `limit` (integer): 返回结果数量，默认 5

#### 示例

```python
# 快速搜索常用工具
search_hot_tools("github", "bm25", 5)

# 使用正则表达式精确匹配
search_hot_tools("github.*pull", "regex", 10)
```

#### 性能优势

- **跳过冷工具**: 仅搜索热工具（使用频率 ≥ 10）和温工具（使用频率 ≥ 3）
- **减少搜索时间**: 对于大型工具集，搜索速度提升 40-60%
- **推荐场景**:
  - 大型工具集（> 100 个工具）
  - 需要快速响应的实时搜索
  - 主要使用高频工具的场景

#### 返回结果

```json
[
  {
    "tool_name": "github.create_pull_request",
    "description": "Create a pull request in a GitHub repository",
    "score": 0.95,
    "temperature": "hot",
    "match_reason": "关键词匹配: github"
  }
]
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
      "args": ["registry-tools"]
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
      "args": ["registry-tools", "--data-path", "/custom/path"]
    }
  }
}
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

## API Key 认证

### 概述

RegistryTools 支持 API Key 认证功能，用于保护 HTTP 模式下的服务访问。通过 API Key 认证，您可以：

- 控制谁可以访问工具注册表
- 限制不同客户端的操作权限
- 追踪 API Key 的使用情况

### 何时使用认证

**建议启用认证的场景**：
- RegistryTools 部署在公网环境中
- 多个团队或客户端共享同一个 RegistryTools 实例
- 需要追踪和管理不同客户端的使用情况
- 需要限制某些客户端的操作权限（只读 vs 读写）

**不需要认证的场景**：
- 仅在本地环境使用 STDIO 模式
- 在可信的私有网络中部署
- 个人开发测试环境

### 启用认证

#### 方法 1: 命令行参数

```bash
registry-tools --transport http --port 8000 --enable-auth
```

#### 方法 2: 环境变量

```bash
export REGISTRYTOOLS_ENABLE_AUTH=true
registry-tools --transport http --port 8000
```

### API Key 管理

#### 创建 API Key

**创建只读 Key（可以搜索和查看工具定义）**：
```bash
registry-tools api-key create "生产环境只读 Key" --permission read
```

**创建读写 Key（可以注册新工具）**：
```bash
registry-tools api-key create "开发环境读写 Key" --permission write
```

**创建带过期时间的 Key（1 小时后过期）**：
```bash
registry-tools api-key create "临时测试 Key" --expires-in 3600
```

**创建带所有者的 Key**：
```bash
registry-tools api-key create "团队 Key" --owner team@example.com
```

#### 列出 API Key

**列出所有 Key**：
```bash
registry-tools api-key list
```

**按所有者筛选**：
```bash
registry-tools api-key list --owner user@example.com
```

#### 删除 API Key

```bash
registry-tools api-key delete <key-id>
```

### 使用 API Key

#### 在 HTTP 请求中使用

**方法 1: X-API-Key Header**

```bash
curl -X POST http://localhost:8000/mcp/tools/search_tools \
  -H "Content-Type: application/json" \
  -H "X-API-Key: rtk_a1b2c3d4e5f6789012345678901234567890123456789012345678901234" \
  -d '{"query": "github", "search_method": "bm25", "limit": 5}'
```

**方法 2: Authorization Bearer Token**

```bash
curl -X POST http://localhost:8000/mcp/tools/search_tools \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer rtk_a1b2c3d4e5f6789012345678901234567890123456789012345678901234" \
  -d '{"query": "github", "search_method": "bm25", "limit": 5}'
```

#### 在 Claude Desktop 中使用

```json
{
  "mcpServers": {
    "RegistryTools": {
      "url": "http://localhost:8000/mcp",
      "headers": {
        "X-API-Key": "rtk_a1b2c3d4e5f6789012345678901234567890123456789012345678901234"
      }
    }
  }
}
```

### 权限级别

| 权限 | 描述 | 允许操作 |
|------|------|----------|
| `read` | 只读 | search_tools, get_tool_definition, list_tools_by_category |
| `write` | 读写 | 上述 + register_tool |
| `admin` | 管理员 | 所有操作 + API Key 管理 |

### 安全最佳实践

1. **使用 HTTPS**: 生产环境必须使用 HTTPS 传输 API Key
2. **妥善保管密钥**: API Key 创建后只显示一次，请妥善保存
3. **权限最小化**: 根据使用场景授予最小必要权限
4. **定期轮换**: 建议定期更换 API Key
5. **设置过期**: 为临时使用场景设置过期时间
6. **定期清理**: 使用 `cleanup_expired` 功能清理过期的 Key

### 示例：完整的认证流程

```bash
# 1. 启用认证启动服务
registry-tools --transport http --port 8000 --enable-auth

# 2. 创建只读 API Key
registry-tools api-key create "我的客户端" --permission read
# 输出: API Key: rtk_abc123... (请妥善保存)

# 3. 客户端使用 API Key 访问
curl -X POST http://localhost:8000/mcp/tools/search_tools \
  -H "X-API-Key: rtk_abc123..." \
  -H "Content-Type: application/json" \
  -d '{"query": "github"}'

# 4. 查看使用情况
registry-tools api-key list

# 5. 如需删除 Key
registry-tools api-key delete <key-id>
```

---

## 最佳实践

### 1. 选择合适的搜索方法

#### 搜索方法对比

| 方法 | 速度 | 准确率 | 中文支持 | 语义理解 | 适用场景 |
|------|------|--------|----------|----------|----------|
| `regex` | 最快 | 高 | 有限 | 无 | 已知工具名称或模式 |
| `bm25` | 快 | 高 | 完美 | 无 | 关键词搜索（推荐） |
| `embedding` | 慢 | 最高 | 完美 | 有 | 语义搜索、模糊查询 |

#### 使用场景指南

**何时使用 Regex**:
- 已知工具的确切名称或模式
- 需要最快响应速度
- 批量工具名称匹配

```python
# 精确匹配工具名称
search_tools("github.create_pull_request", "regex", 10)

# 使用正则表达式模式
search_tools("github\..*pull", "regex", 10)
```

**何时使用 BM25** (推荐):
- 通用关键词搜索
- 需要平衡速度和准确率
- 支持中文分词
- 中英文混合搜索

```python
# 使用全局默认搜索方法（推荐）
search_tools("github pull request 创建", limit=5)

# 显式指定 BM25
search_tools("github pull request", "bm25", 5)
```

**何时使用 Embedding**:
- 语义搜索，理解查询意图
- 工具描述与关键词不直接匹配
- 需要最高准确率
- 同义词或相似表达

```python
# 语义搜索示例
search_tools("如何在 GitHub 上提交代码", "embedding", 5)
search_tools("创建合并请求", "embedding", 5)
```

#### 设置全局默认搜索方法

您可以通过环境变量设置默认搜索引擎：

```bash
# 在 ~/.bashrc 或 ~/.zshrc 中添加
export REGISTRYTOOLS_SEARCH_METHOD=bm25  # 或 regex/embedding
```

这样在调用搜索工具时可以省略 `search_method` 参数：

```python
# 使用全局默认搜索方法
search_tools("github pull request", limit=5)
```

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
