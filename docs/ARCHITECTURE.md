# RegistryTools 架构设计

**版本**: v0.2.1
**更新日期**: 2026-01-11
**项目**: RegistryTools - MCP Tool Registry Server

---

## 系统概述

RegistryTools 是一个独立的 MCP Tool Registry Server，提供通用的工具搜索和发现能力。其核心价值在于：

- **按需工具发现**: 减少 Token 消耗 85%（从 ~77K 降至 ~8.7K）
- **提升准确率**: 工具选择准确率从 49% 提升至 74%
- **解耦复用**: 可被任何 MCP 客户端使用

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           MCP Clients (任何支持 MCP 的应用)                      │
│  ┌────────────────┬────────────────┬────────────────┬──────────────────────┐   │
│  │ DeepThinking   │ Cursor / VSCode│ 其他 Agent     │ Claude Desktop       │   │
│  │   Agent        │    IDE         │                │                      │   │
│  └────────────────┴────────────────┴────────────────┴──────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────────────────────┘
                                │ MCP Protocol (STDIO/Streamable HTTP)
                                ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    RegistryTools (独立 MCP Server)                              │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    Tool Registry (工具注册表)                            │   │
│  │  • 管理所有工具的元数据                                                  │   │
│  │  • 维护搜索索引                                                          │   │
│  │  • 跟踪使用频率和最后使用时间                                            │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    Search Engine (搜索引擎)                             │   │
│  │  ┌──────────────┬──────────────┬──────────────────────────────────┐    │   │
│  │  │ Regex 搜索   │  BM25 搜索   │  Embedding 搜索 (可选)            │    │   │
│  │  │ (精确匹配)   │ (关键词)     │  (语义相似度)                     │    │   │
│  │  └──────────────┴──────────────┴──────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    MCP Tools (暴露的工具接口)                           │   │
│  │  • search_tools(query, method, limit) - 搜索工具                        │   │
│  │  • get_tool_definition(tool_name) - 获取完整定义                       │   │
│  │  • list_tools_by_category(category) - 按类别列出                       │   │
│  │  • register_tool(tool_def) - 动态注册工具                              │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────────────────────┘
                                │ 索引来源
                                ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    Tool Sources (工具来源)                                      │
│  ┌──────────────┬──────────────┬──────────────┬────────────────────────────┐   │
│  │ JSON 文件    │ 本地数据库   │ 其他 MCP     │ 动态注册                  │   │
│  │ (tools.json) │  (SQLite)    │  Servers     │                            │   │
│  └──────────────┴──────────────┴──────────────┴────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Agent Loop 工作流程

```
用户: "帮我查一下上周的 AWS 账单"
        │
        ▼
DeepThinking: 发现没有 aws_billing 工具
        │
        ▼
Action: search_tools("check aws billing cost")
        │
        ▼
RegistryTools: 返回 "Found: aws_cost_explorer"
        │
        ▼
DeepThinking: Action: get_tool_definition("aws_cost_explorer")
        │
        ▼
RegistryTools: 返回完整 JSON Schema
        │
        ▼
DeepThinking: Action: aws_cost_explorer(start_date="2026-01-01")
```

---

## 传输协议

RegistryTools 支持多种 MCP 传输协议,以适应不同的部署场景:

### STDIO 传输 (默认)

**适用场景**:
- Claude Desktop 等本地 MCP 客户端
- 本地脚本和命令行工具
- 单用户单客户端场景

**特点**:
- 基于标准输入输出的进程间通信
- 无需网络配置
- 客户端启动服务器进程
- 适合本地开发调试

**启动方式**:
```bash
# 默认 STDIO 模式
registry-tools

# 或显式指定
registry-tools --transport stdio
```

**客户端配置示例**:
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

### Streamable HTTP 传输

**适用场景**:
- 远程服务部署
- 容器化部署 (Docker/Kubernetes)
- 多客户端共享同一服务器
- 需要负载均衡和高可用的场景

**特点**:
- 基于 HTTP 的双向流式通信
- 支持多客户端并发访问
- 支持负载均衡
- 可选无状态模式 (stateless_http)

**启动方式**:
```bash
# 使用默认参数 (127.0.0.1:8000)
registry-tools --transport http

# 自定义主机和端口
registry-tools --transport http --host 0.0.0.0 --port 8000

# 自定义路径
registry-tools --transport http --port 8000 --path /api/mcp
```

**客户端配置示例**:
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

除了命令行参数,RegistryTools 还支持 FastMCP 的声明式配置文件:

**STDIO 配置** (`fastmcp.json`):
```json
{
  "$schema": "https://gofastmcp.com/public/schemas/fastmcp.json/v1.json",
  "source": {
    "path": "src/registrytools/__main__.py",
    "entrypoint": "main"
  },
  "deployment": {
    "transport": "stdio"
  }
}
```

**HTTP 配置** (`fastmcp.http.json`):
```json
{
  "$schema": "https://gofastmcp.com/public/schemas/fastmcp.json/v1.json",
  "source": {
    "path": "src/registrytools/__main__.py",
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

### 传输协议对比

| 特性 | STDIO | Streamable HTTP |
|------|-------|-----------------|
| **适用场景** | 本地 CLI 集成 | 远程服务部署 |
| **通信方式** | 进程间管道 | HTTP 流式通信 |
| **并发支持** | 单客户端 | 多客户端 |
| **负载均衡** | 不支持 | 完全支持 |
| **状态管理** | 进程级 | 可选无状态 |
| **网络配置** | 无需 | 需要 host/port |
| **防火墙** | 无需考虑 | 需要开放端口 |
| **推荐使用** | 本地开发 | 生产环境 |

### 协议选择建议

- **本地开发/调试**: 使用 STDIO (默认)
- **Claude Desktop**: 使用 STDIO
- **远程部署**: 使用 Streamable HTTP
- **容器化部署**: 使用 Streamable HTTP
- **多用户共享**: 使用 Streamable HTTP
- **需要负载均衡**: 使用 Streamable HTTP

---

## 核心组件设计

### 1. ToolRegistry（工具注册表）

**职责**: 管理所有工具的元数据和索引

**核心方法**:
```python
class ToolRegistry:
    def register(self, tool: ToolMetadata) -> None
    def search(self, query: str, method: SearchMethod, limit: int) -> list[ToolSearchResult]
    def get_tool(self, name: str) -> Optional[ToolMetadata]
    def update_usage(self, tool_name: str) -> None
```

**数据结构**:
```python
{
    "tool_name": {
        "name": "str",
        "description": "str",
        "mcp_server": "Optional[str]",
        "defer_loading": "bool",
        "tags": "set[str]",
        "category": "Optional[str]",
        "use_frequency": "int",
        "last_used": "Optional[datetime]",
        "input_schema": "Optional[dict]",
        "output_schema": "Optional[dict]"
    }
}
```

---

### 2. SearchEngine（搜索引擎）

**职责**: 提供多种搜索算法

**支持的算法**:

| 算法 | 准确率 | 速度 | 适用场景 |
|------|--------|------|----------|
| Regex | 56% | 最快 | 精确名称匹配 |
| BM25 | 64% | 快 | 关键词搜索（推荐） |
| Embedding | 75%+ | 中 | 语义搜索（可选依赖，支持中英文） |

**接口设计**:
```python
class SearchAlgorithm(ABC):
    @abstractmethod
    def index(self, tools: list[ToolMetadata]) -> None: ...

    @abstractmethod
    def search(self, query: str, tools: list[ToolMetadata], limit: int) -> list[ToolSearchResult]: ...
```

---

### 3. StorageLayer（存储层）

**职责**: 持久化工具元数据

**支持的存储后端**:

| 存储类型 | 适用场景 | 性能特点 | 配置方式 |
|---------|---------|----------|----------|
| **JSON** | 小规模工具集（< 1000 工具），默认 | 简单可读 | 默认 |
| **SQLite** | 大规模工具集（> 1000 工具） | 高性能查询 | `REGISTRYTOOLS_STORAGE_BACKEND=sqlite` |

**性能对比**:

| 操作 | JSON 存储 | SQLite 存储 | 性能提升 |
|-----|-----------|-------------|----------|
| 加载 1000 工具 | ~75ms | ~18ms | 76% |
| 按标签过滤 | ~15ms | ~4ms | 73% |
| 按温度加载 | ~12ms | ~3ms | 75% |
| 内存占用 (1000 工具) | ~15MB | ~6MB | 60% |

**存储后端选择机制**:

```
用户配置
    │
    ├── 环境变量: REGISTRYTOOLS_STORAGE_BACKEND
    ├── CLI 参数: --storage-backend
    │
    ▼
get_default_storage_backend() - 获取默认存储后端
    │
    ├── 优先级 1: CLI 参数 (--storage-backend)
    ├── 优先级 2: 环境变量 (REGISTRYTOOLS_STORAGE_BACKEND)
    └── 优先级 3: 默认值 (JSON)
    │
    ▼
create_storage(backend, data_path) - 创建存储实例
    │
    ├── StorageBackend.JSON → JSONStorage
    └── StorageBackend.SQLITE → SQLiteStorage
    │
    ▼
服务器创建
    │
    ├── create_server() - 使用 JSON 存储
    └── create_server_with_sqlite() - 使用 SQLite 存储
```

**配置示例**:

```bash
# 方法 1: 环境变量（推荐）
export REGISTRYTOOLS_STORAGE_BACKEND=sqlite
registry-tools

# 方法 2: CLI 参数
registry-tools --storage-backend sqlite

# 方法 3: Claude Desktop 配置
{
  "mcpServers": {
    "RegistryTools": {
      "command": "registry-tools",
      "env": {
        "REGISTRYTOOLS_STORAGE_BACKEND": "sqlite"
      }
    }
  }
}
```

**接口设计**:
```python
class ToolStorage(ABC):
    """存储抽象基类"""

    @abstractmethod
    def load_all(self) -> list[ToolMetadata]: ...

    @abstractmethod
    def save(self, tool: ToolMetadata) -> None: ...

    @abstractmethod
    def save_many(self, tools: list[ToolMetadata]) -> None: ...

    @abstractmethod
    def delete(self, tool_name: str) -> bool: ...

    @abstractmethod
    def validate(self) -> bool: ...

    @abstractmethod
    def load_by_temperature(
        self, temperature: ToolTemperature, limit: int | None = None
    ) -> list[ToolMetadata]: ...
```

**存储后端枚举**:
```python
class StorageBackend(str, Enum):
    """存储后端枚举"""

    JSON = "json"
    """JSON 文件存储（默认），适合小规模工具集"""

    SQLITE = "sqlite"
    """SQLite 数据库存储，适合大规模工具集"""
```

详见 [存储选择指南](STORAGE.md)。

---

## 数据模型

### ToolMetadata

```python
class ToolMetadata(BaseModel):
    """工具元数据"""
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

```python
class ToolSearchResult(BaseModel):
    """搜索结果"""
    tool_name: str
    description: str
    score: float
    match_reason: str  # 匹配原因（名称/描述/标签）
```

---

## MCP 工具接口

### search_tools

```python
def search_tools(
    query: str,
    search_method: str = "bm25",
    limit: int = 5
) -> str
```

**功能**: 搜索可用的 MCP 工具

**参数**:
- `query`: 搜索查询
- `search_method`: 搜索方法 (regex/bm25/embedding)
- `limit`: 返回结果数量

**返回**: 匹配的工具列表

---

### get_tool_definition

```python
def get_tool_definition(tool_name: str) -> str
```

**功能**: 获取指定工具的完整定义

**参数**:
- `tool_name`: 工具名称

**返回**: 工具的完整 JSON Schema 定义

---

### list_tools_by_category

```python
def list_tools_by_category(category: str, limit: int = 20) -> str
```

**功能**: 按类别列出工具

**参数**:
- `category`: 工具类别
- `limit`: 返回结果数量

**返回**: 该类别下的所有工具

---

### register_tool

```python
def register_tool(
    name: str,
    description: str,
    category: str = None,
    tags: list[str] = None
) -> str
```

**功能**: 动态注册新工具

**参数**:
- `name`: 工具名称
- `description`: 工具描述
- `category`: 工具类别（可选）
- `tags`: 工具标签（可选）

**返回**: 注册结果

---

## 性能优化策略

### 1. 冷热工具分离

基于使用频率将工具分为：
- **热工具**: 高频使用，预加载
- **冷工具**: 低频使用，延迟加载

### 2. 索引缓存

- 搜索索引缓存到内存
- 增量更新而非全量重建

### 3. 批量操作

- 支持批量工具注册
- 支持批量工具查询

---

## 安全考虑

### 输入验证

- 所有用户输入进行验证
- 防止注入攻击

### 权限控制

- 工具注册需要权限验证
- 敏感操作需要授权

### 数据隔离

- 不同客户端的数据隔离
- 支持多实例部署

---

## 扩展性设计

### 插件化搜索算法

```python
class CustomSearchAlgorithm(SearchAlgorithm):
    def index(self, tools): ...
    def search(self, query, tools, limit): ...
```

### 可扩展存储后端

```python
class CustomStorage(ToolStorage):
    def load_all(self): ...
    def save(self, tool): ...
```

---

## 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| MCP 框架 | FastMCP | 轻量级 MCP 服务器框架 |
| 搜索算法 | rank-bm25 | BM25 算法实现 |
| 中文分词 | jieba | 中文文本分词 |
| 向量搜索 | sentence-transformers | 可选的语义搜索 |
| 数据存储 | SQLite / JSON | 工具元数据持久化 |
| 数据验证 | Pydantic | 数据模型和验证 |

---

## 相关文档

### 核心文档
- [API.md](API.md) - API 参考文档
- [USER_GUIDE.md](USER_GUIDE.md) - 用户使用指南
- [CONFIGURATION.md](CONFIGURATION.md) - 配置参数说明

### 设计文档
- [REFACTORING_ANALYSIS.md](REFACTORING_ANALYSIS.md) - 目录结构重构分析
- [AUDIT_REPORT_PHASE16.md](AUDIT_REPORT_PHASE16.md) - Phase 16 审核报告

### 支持文档
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - 故障排除
- [BEST_PRACTICES.md](BEST_PRACTICES.md) - 最佳实践
- [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) - 开发流程规范

---

**维护者**: Maric
**文档版本**: v0.2.1
