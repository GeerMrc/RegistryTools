# RegistryTools 配置指南

**版本**: v0.2.1
**更新日期**: 2026-01-11
**项目**: RegistryTools - MCP Tool Registry Server

---

本文档提供 RegistryTools 的完整配置说明，包括所有配置参数、默认值和使用示例。

---

## 目录

- [快速开始](#快速开始)
- [配置优先级](#配置优先级)
- [环境变量配置](#环境变量配置)
- [CLI 参数配置](#cli-参数配置)
- [日志配置](#日志配置)
- [API Key 认证配置](#api-key-认证配置)
- [冷热工具分离配置](#冷热工具分离配置)
- [性能调优配置](#性能调优配置)
- [配置示例](#配置示例)

---

## 快速开始

### 最小配置

使用默认配置启动服务：

```bash
# STDIO 模式（默认）
registry-tools

# HTTP 模式
registry-tools --transport http --port 8000
```

### 常用配置

```bash
# 自定义数据路径
registry-tools --data-path /custom/path

# 启用 API Key 认证
registry-tools --transport http --enable-auth

# 启用 DEBUG 日志
export REGISTRYTOOLS_LOG_LEVEL=DEBUG
registry-tools
```

---

## 配置优先级

RegistryTools 支持多种配置方式，按优先级从高到低：

| 优先级 | 配置方式 | 说明 |
|--------|----------|------|
| 1 (最高) | 环境变量 | 覆盖所有其他配置 |
| 2 | CLI 参数 | 覆盖默认值 |
| 3 (最低) | 默认值 | 代码中的硬编码默认值 |

**示例**：
```bash
# 环境变量会覆盖 CLI 参数
export REGISTRYTOOLS_PORT=9000
registry-tools --port 8000  # 实际使用 9000
```

---

## 环境变量配置

### 可用环境变量

| 环境变量 | 描述 | 默认值 | 可选值 |
|---------|------|--------|--------|
| `REGISTRYTOOLS_DATA_PATH` | 数据目录路径 | `~/.RegistryTools` | 任意有效路径 |
| `REGISTRYTOOLS_TRANSPORT` | 传输协议 | `stdio` | `stdio`, `http` |
| `REGISTRYTOOLS_LOG_LEVEL` | 日志级别 | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `REGISTRYTOOLS_ENABLE_AUTH` | 启用 API Key 认证 | `false` | `true`, `false`, `1`, `0`, `yes`, `no` |
| `REGISTRYTOOLS_SEARCH_METHOD` | 默认搜索方法 | `bm25` | `regex`, `bm25`, `embedding` |
| `REGISTRYTOOLS_DEVICE` | Embedding 模型计算设备 | `cpu` | `cpu`, `gpu:0`, `gpu:1`, `auto` |
| `REGISTRYTOOLS_DESCRIPTION` | MCP 服务器描述 | 统一的 MCP 工具注册与搜索服务，用于发现和筛选可用工具，提升任务执行工具调用准确性，复杂任务工具调用效率 | 任意有效字符串 |

### 详细说明

#### REGISTRYTOOLS_DATA_PATH

指定 RegistryTools 数据存储目录。

**默认值**: `~/.RegistryTools`

**目录结构**:
```
~/.RegistryTools/
├── tools.json              # 工具元数据存储
├── api_keys.db             # API Key 数据库（如果启用认证）
└── logs/                   # 日志文件（如果配置）
```

**示例**:
```bash
# 使用自定义路径
export REGISTRYTOOLS_DATA_PATH=/var/lib/registrytools
registry-tools

# 使用相对路径
export REGISTRYTOOLS_DATA_PATH=./data
registry-tools
```

#### REGISTRYTOOLS_TRANSPORT

指定 MCP 传输协议。

**可选值**:
- `stdio`: 标准输入输出，用于本地 CLI 集成（默认）
- `http`: Streamable HTTP，用于远程部署

**示例**:
```bash
# 使用 HTTP 传输
export REGISTRYTOOLS_TRANSPORT=http
registry-tools --host 0.0.0.0 --port 8000
```

#### REGISTRYTOOLS_LOG_LEVEL

指定日志级别。

**可选值**:
- `DEBUG`: 详细调试信息，用于开发
- `INFO`: 一般信息（默认）
- `WARNING`: 警告信息
- `ERROR`: 仅错误信息

**示例**:
```bash
# 启用调试日志
export REGISTRYTOOLS_LOG_LEVEL=DEBUG
registry-tools

# 仅显示错误
export REGISTRYTOOLS_LOG_LEVEL=ERROR
registry-tools
```

#### REGISTRYTOOLS_ENABLE_AUTH

启用 API Key 认证（仅 HTTP 模式有效）。

**可选值**:
- `true`, `1`, `yes`: 启用认证
- `false`, `0`, `no`: 禁用认证（默认）

**注意事项**:
- STDIO 模式不支持认证，会自动禁用
- 启用认证后，客户端需要在 HTTP Header 中提供 API Key

**示例**:
```bash
# 启用认证
export REGISTRYTOOLS_ENABLE_AUTH=true
registry-tools --transport http --port 8000
```

#### REGISTRYTOOLS_DESCRIPTION

指定 MCP 服务器的描述信息，在 MCP 客户端的服务器列表中显示。

**默认值**:
```
统一的 MCP 工具注册与搜索服务，用于发现和筛选可用工具，
提升任务执行工具调用准确性，复杂任务工具调用效率
```

**示例**:
```bash
# 使用自定义描述
export REGISTRYTOOLS_DESCRIPTION="我的工具服务器"
registry-tools

# 在 Claude Desktop 配置中使用
{
  "mcpServers": {
    "RegistryTools": {
      "command": "registry-tools",
      "env": {
        "REGISTRYTOOLS_DESCRIPTION": "团队内部工具目录"
      }
    }
  }
}
```

**注意事项**:
- 描述会在 MCP 客户端的服务器列表中显示
- 建议描述内容简洁明了，突出服务器用途
- 如果不设置，将使用默认描述："统一的 MCP 工具注册与搜索服务，用于发现和筛选可用工具，提升任务执行工具调用准确性，复杂任务工具调用效率"
- 支持多行描述，使用 `\\n` 表示换行

#### REGISTRYTOOLS_SEARCH_METHOD

指定默认搜索方法，应用于所有搜索工具。

**可选值**:
- `regex`: 正则表达式精确匹配（最快）
- `bm25`: BM25 关键词搜索（推荐，默认）
- `embedding`: 语义向量搜索（最准确，需要安装额外依赖）

**性能对比**:
| 方法 | 速度 | 准确率 | 依赖 |
|------|------|--------|------|
| `regex` | 最快 | 高 | 无 |
| `bm25` | 快 | 高 | rank-bm25, jieba |
| `embedding` | 慢 | 最高 | sentence-transformers, numpy |

**延迟加载机制**:
- 当配置为 `bm25`（默认）时，Embedding 搜索器不会被注册，不加载任何模型
- 当配置为 `embedding` 时，采用延迟加载：
  - 服务器启动时只注册延迟加载器，不实际加载模型
  - 首次执行 embedding 搜索时才初始化模型
  - 这样可以显著减少启动时间和内存占用

**示例**:
```bash
# 使用 BM25 搜索（默认，不加载 embedding 模型）
registry-tools

# 使用正则表达式搜索
export REGISTRYTOOLS_SEARCH_METHOD=regex
registry-tools

# 使用语义搜索（需要安装额外依赖）
pip install registry-tools[embedding]
export REGISTRYTOOLS_SEARCH_METHOD=embedding
registry-tools
```

**注意事项**:
- `search_hot_tools` 工具不支持 `embedding` 方法，会自动回退到 `bm25`
- 如果设置了无效值，会记录警告并使用默认值 `bm25`
- 可以在调用时通过参数覆盖全局默认值

#### REGISTRYTOOLS_DEVICE

控制 Embedding 搜索器使用的计算设备（GPU/CPU）。

**可选值**:
- `cpu` 或未设置: 使用 CPU（默认，最安全）
- `gpu:0` 或 `cuda:0`: 使用第一个 GPU
- `gpu:1` 或 `cuda:1`: 使用第二个 GPU
- `auto`: 自动选择（有 GPU 时使用第一个）

**设计原则**:
- **默认安全**: 不设置时默认使用 CPU，确保不意外占用 GPU
- **显式启用**: 只有明确配置 `gpu:N` 时才使用 GPU
- **多 GPU 支持**: 支持指定 GPU 编号（0、1、2...）
- **可用性验证**: 系统会验证 GPU 是否可用，不可用时自动降级

**GPU 降级策略**:

| 配置 | GPU 可用 | GPU 不可用 |
|-----|---------|-----------|
| `auto` | 使用 GPU:0，**静默**切换 | 降级到 CPU，**不记录日志** |
| `gpu:0` / `gpu:1` | 使用指定 GPU | 降级到 CPU，**记录警告日志** |
| `cpu` | 使用 CPU | 使用 CPU |

**日志行为示例**:
```bash
# auto 模式降级（静默）
# 日志：Embedding 搜索：自动检测到 GPU，使用 cuda:0
# （无降级日志）

# 具体 GPU 降级（警告）
# 日志：Embedding 搜索：配置的 GPU gpu:0 不可用，已降级到 CPU
```

**示例**:
```bash
# 默认 CPU 模式（推荐，无 GPU 占用）
registry-tools

# 显式 CPU 模式
export REGISTRYTOOLS_DEVICE=cpu
registry-tools

# 使用第一个 GPU
export REGISTRYTOOLS_DEVICE=gpu:0
registry-tools

# 使用第二个 GPU
export REGISTRYTOOLS_DEVICE=gpu:1
registry-tools

# 自动模式（有 GPU 时使用第一个，无 GPU 时静默降级）
export REGISTRYTOOLS_DEVICE=auto
registry-tools
```

**注意事项**:
- 默认使用 CPU 是为了确保不意外占用 GPU 资源
- 如果需要 GPU 加速，请显式设置 `REGISTRYTOOLS_DEVICE=gpu:N`
- GPU 模式需要安装 CUDA 版本的 PyTorch
- 多 GPU 环境下可以指定使用哪个 GPU
- 配置的 GPU 不可用时，系统会自动降级到 CPU 并记录警告

**GPU 内存需求**:

使用 Embedding 搜索时，不同模型的内存占用：

| 模型 | GPU 内存 | CPU 内存 |
|------|---------|----------|
| paraphrase-multilingual-MiniLM-L12-v2 (默认) | ~500MB | ~1GB |
| all-MiniLM-L6-v2 | ~100MB | ~300MB |
| paraphrase-multilingual-mpnet-base-v2 | ~1.2GB | ~2.5GB |

**注意**: 模型会在首次使用时从 Hugging Face 下载并缓存在 `~/.cache/huggingface/`。

---

## CLI 参数配置

### 服务器参数

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `--data-path` | string | `~/.RegistryTools` | 数据目录路径 |
| `--transport` | string | `stdio` | 传输协议: `stdio` 或 `http` |
| `--host` | string | `127.0.0.1` | HTTP 主机地址 |
| `--port` | integer | `8000` | HTTP 端口 |
| `--path` | string | `/` | HTTP 路径前缀 |
| `--enable-auth` | flag | `false` | 启用 API Key 认证 |
| `--version` | flag | - | 显示版本信息 |

### API Key 管理参数

| 子命令 | 参数 | 描述 |
|--------|------|------|
| `api-key create` | `name` | API Key 名称（必需） |
| | `--permission` | 权限级别: `read`, `write`, `admin`（默认: `read`） |
| | `--expires-in` | 过期时间（秒） |
| | `--owner` | 所有者标识 |
| `api-key list` | `--owner` | 按所有者筛选 |
| `api-key delete` | `key_id` | API Key ID（必需） |

### 使用示例

```bash
# 服务器启动
registry-tools --data-path /data --transport http --host 0.0.0.0 --port 8000

# 创建只读 API Key
registry-tools api-key create "My Key" --permission read

# 创建带过期时间的 API Key
registry-tools api-key create "Temp Key" --expires-in 3600

# 列出所有 API Key
registry-tools api-key list

# 删除 API Key
registry-tools api-key delete <key-id>
```

---

## 日志配置

### 日志级别

| 级别 | 描述 | 使用场景 |
|------|------|----------|
| `DEBUG` | 详细调试信息 | 开发调试、问题排查 |
| `INFO` | 一般信息（默认） | 正常运行监控 |
| `WARNING` | 警告信息 | 潜在问题提醒 |
| `ERROR` | 错误信息 | 错误发生追踪 |

### 配置方式

#### 方式 1: 环境变量（推荐）

```bash
export REGISTRYTOOLS_LOG_LEVEL=DEBUG
registry-tools
```

#### 方式 2: 仅环境变量

**注意**: 日志级别不支持 CLI 参数配置，只能通过环境变量设置。

### 日志格式

```
YYYY-MM-DD HH:MM:SS - registrytools - LEVEL - Message
```

**示例**:
```
2026-01-09 10:30:45 - registrytools - INFO - Starting RegistryTools server...
2026-01-09 10:30:46 - registrytools - DEBUG - Loading tools from storage...
2026-01-09 10:30:47 - registrytools - INFO - Server ready, serving 26 tools
```

### 日志查看

#### 终端输出（默认）

```bash
# 日志直接输出到终端
registry-tools
```

#### 重定向到文件

```bash
# 重定向所有输出
registry-tools > registrytools.log 2>&1

# 仅重定向日志
registry-tools 2>&1 | tee registrytools.log
```

#### 过滤特定级别

```bash
# 仅查看错误
registry-tools 2>&1 | grep ERROR

# 查看警告和错误
registry-tools 2>&1 | grep -E 'WARNING|ERROR'
```

---

## API Key 认证配置

### 启用认证

#### 方式 1: CLI 参数

```bash
registry-tools --transport http --port 8000 --enable-auth
```

#### 方式 2: 环境变量

```bash
export REGISTRYTOOLS_ENABLE_AUTH=true
registry-tools --transport http --port 8000
```

### API Key 管理

#### 创建 API Key

```bash
# 创建只读 Key（搜索和查看工具）
registry-tools api-key create "Production Read Key" --permission read

# 创建读写 Key（包括注册新工具）
registry-tools api-key create "Development Write Key" --permission write

# 创建管理员 Key（所有操作 + API Key 管理）
registry-tools api-key create "Admin Key" --permission admin

# 创建带过期时间的 Key（1 小时后过期）
registry-tools api-key create "Temporary Key" --expires-in 3600

# 创建带所有者的 Key
registry-tools api-key create "Team Key" --owner team@example.com
```

#### 列出 API Key

```bash
# 列出所有 Key
registry-tools api-key list

# 按所有者筛选
registry-tools api-key list --owner user@example.com
```

#### 删除 API Key

```bash
registry-tools api-key delete <key-id>
```

### API Key 格式

```
rtk_<64-char-hex>
```

- **前缀**: `rtk` (RegistryTools Key)
- **随机部分**: 64 个十六进制字符（32 字节，256 位安全随机）

**示例**:
```
rtk_a1b2c3d4e5f6789012345678901234567890123456789012345678901234
```

### 权限级别

| 权限 | 描述 | 允许操作 |
|------|------|----------|
| `read` | 只读 | `search_tools`, `get_tool_definition`, `list_tools_by_category` |
| `write` | 读写 | 上述操作 + `register_tool` |
| `admin` | 管理员 | 所有操作 + API Key 管理命令 |

### 客户端使用

#### 方式 1: X-API-Key Header

```bash
curl -X POST http://localhost:8000/mcp/tools/search_tools \
  -H "Content-Type: application/json" \
  -H "X-API-Key: rtk_a1b2c3d4e5f6789012345678901234567890123456789012345678901234" \
  -d '{"query": "github", "search_method": "bm25", "limit": 5}'
```

#### 方式 2: Authorization Bearer Token

```bash
curl -X POST http://localhost:8000/mcp/tools/search_tools \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer rtk_a1b2c3d4e5f6789012345678901234567890123456789012345678901234" \
  -d '{"query": "github"}'
```

#### Claude Desktop 配置

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

### 安全最佳实践

1. **使用 HTTPS**: 生产环境必须使用 HTTPS 传输 API Key
2. **妥善保管密钥**: API Key 创建后只显示一次，请妥善保存
3. **权限最小化**: 根据使用场景授予最小必要权限
4. **定期轮换**: 建议定期更换 API Key
5. **设置过期**: 为临时使用场景设置过期时间
6. **定期清理**: 使用完成后及时删除不再需要的 API Key

---

## 冷热工具分离配置

RegistryTools 实现了智能的冷热工具分离机制，根据使用频率自动分类工具，优化搜索性能。

### 温度级别定义

工具根据使用频率分为三个温度级别：

| 温度级别 | 使用频率 | 描述 |
|---------|---------|------|
| `HOT` (热工具) | ≥ 10 次 | 高频使用工具，优先加载 |
| `WARM` (温工具) | 3-9 次 | 中频使用工具 |
| `COLD` (冷工具) | < 3 次 | 低频使用工具，延迟加载 |

### 配置参数

| 参数 | 默认值 | 描述 |
|------|--------|------|
| `HOT_TOOL_THRESHOLD` | `10` | 热工具阈值（使用次数） |
| `WARM_TOOL_THRESHOLD` | `3` | 温工具阈值（使用次数） |
| `HOT_TOOL_INACTIVE_DAYS` | `30` | 热工具降级天数（30 天未使用 → 温工具） |
| `WARM_TOOL_INACTIVE_DAYS` | `60` | 温工具降级天数（60 天未使用 → 冷工具） |
| `MAX_HOT_TOOLS_PRELOAD` | `100` | 最多预加载的热工具数量 |
| `ENABLE_DOWNGRADE` | `True` | 是否启用工具降级机制 |

### 升降级机制

#### 升级（低 → 高）

工具使用频率增加时自动升级：

```
COLD (使用 1 次) → WARM (使用 3 次) → HOT (使用 10 次)
```

#### 降级（高 → 低）

工具长期未使用时自动降级：

```
HOT (30 天未使用) → WARM (60 天未使用) → COLD
```

**注意**: 降级机制可通过 `ENABLE_DOWNGRADE = False` 禁用。

### 性能影响

| 温度级别 | 加载方式 | 搜索性能 |
|---------|---------|----------|
| `HOT` | 启动时预加载（最多 100 个） | 最快（内存索引） |
| `WARM` | 按需加载，缓存保留 | 快（索引缓存） |
| `COLD` | 按需加载，延迟释放 | 标准（实时搜索） |

### 配置示例

#### 默认配置（推荐大多数场景）

```python
# src/registrytools/defaults.py
HOT_TOOL_THRESHOLD = 10
WARM_TOOL_THRESHOLD = 3
HOT_TOOL_INACTIVE_DAYS = 30
WARM_TOOL_INACTIVE_DAYS = 60
MAX_HOT_TOOLS_PRELOAD = 100
ENABLE_DOWNGRADE = True
```

#### 高频使用场景（工具集 < 100）

```python
# 所有工具都作为热工具处理
HOT_TOOL_THRESHOLD = 1  # 使用 1 次即为热工具
WARM_TOOL_THRESHOLD = 1
MAX_HOT_TOOLS_PRELOAD = 1000  # 增加预加载数量
ENABLE_DOWNGRADE = False  # 禁用降级
```

#### 低频使用场景（大型工具集）

```python
# 更严格的分类
HOT_TOOL_THRESHOLD = 20  # 使用 20 次才为热工具
WARM_TOOL_THRESHOLD = 5
HOT_TOOL_INACTIVE_DAYS = 14  # 更快的降级
WARM_TOOL_INACTIVE_DAYS = 30
MAX_HOT_TOOLS_PRELOAD = 50  # 减少预加载数量
```

### 监控工具温度

使用 `registry://stats` 资源查看工具温度分布：

```python
import requests

# 获取统计信息
response = requests.get(
    "http://localhost:8000/mcp/resources/registry://stats",
    headers={"X-API-Key": "rtk_xxx..."}
)

stats = response.json()
print(f"总工具数: {stats['total_tools']}")
print(f"热工具数: {stats.get('hot_tools', 0)}")
print(f"温工具数: {stats.get('warm_tools', 0)}")
print(f"冷工具数: {stats.get('cold_tools', 0)}")
```

---

## 性能调优配置

### 输入参数限制

为保护系统性能和稳定性，以下输入参数受到限制：

| 参数 | 限制值 | 说明 |
|------|--------|------|
| `query` 长度 | ≤ 1000 字符 | 搜索查询字符串的最大长度 |
| `limit` | 1 ≤ limit ≤ 100 | 返回结果的最大数量 |
| `tool_name` | 非空 | 工具名称不能为空 |
| `description` | ≤ 1000 字符 | 工具描述的最大长度 |
| `search_method` | regex/bm25/embedding | 仅支持这三种搜索方法 |

**错误处理**:
- 超过限制时会返回详细的错误信息
- 建议客户端实现输入验证以提供更好的用户体验

### 搜索性能优化

#### 选择合适的搜索方法

| 方法 | 适用场景 | 速度 | 准确率 |
|------|----------|------|--------|
| `regex` | 已知工具名称，精确匹配 | 最快 | 高 |
| `bm25` | 关键词搜索，支持中文分词 | 快 | 高 |
| `embedding` | 语义搜索，理解查询意图 | 慢 | 高 |

**示例**:
```python
# 精确查找（已知工具名称）
search_tools("github.*pull", "regex", 10)

# 关键词搜索（分词匹配）
search_tools("github pull request", "bm25", 5)

# 语义搜索（理解意图）
search_tools("如何在 GitHub 上创建 PR", "embedding", 5)
```

#### 调整搜索结果数量

```python
# 少量结果（快速响应）
search_tools("github", "bm25", 3)

# 大量结果（完整扫描）
search_tools("github", "bm25", 50)
```

### 内存优化

#### 限制热工具预加载

对于内存受限环境：

```python
# 减少预加载的热工具数量
MAX_HOT_TOOLS_PRELOAD = 20  # 默认 100
```

#### 禁用降级机制

对于稳定的生产环境：

```python
# 禁用降级，保持工具温度稳定
ENABLE_DOWNGRADE = False
```

### 并发优化

RegistryTools 使用线程安全的搜索实现：

- **线程锁**: `threading.RLock()` 保护共享状态
- **无状态搜索**: 搜索操作不修改工具元数据
- **并发安全**: 支持多个客户端同时搜索

### 性能基准

| 指标 | BM25 目标值 | Embedding 目标值 | 测试条件 |
|------|-----------|----------------|----------|
| 搜索响应时间 | < 100ms | < 500ms | 1000+ 工具 |
| 内存占用（不含模型） | < 50MB | < 100MB | 1000+ 工具 |
| 模型内存占用 | 0MB | ~500MB | paraphrase-multilingual-MiniLM-L12-v2 |
| 首次搜索延迟 | < 50ms | < 2s | 模型加载 |
| 索引构建时间 | < 1s | < 3s | 1000+ 工具 |
| 热工具加载 | < 50ms | < 100ms | 100 个工具 |

---

## 配置示例

### 场景 1: 本地开发

```bash
# 使用默认配置，STDIO 模式
registry-tools

# 启用 DEBUG 日志
export REGISTRYTOOLS_LOG_LEVEL=DEBUG
registry-tools
```

### 场景 2: 团队共享服务器

```bash
# HTTP 模式 + API Key 认证
registry-tools \
  --transport http \
  --host 0.0.0.0 \
  --port 8000 \
  --enable-auth

# 创建团队 API Key
registry-tools api-key create "Team Key" --permission write --owner team@example.com
```

### 场景 3: 生产环境

```bash
# 使用环境变量配置
export REGISTRYTOOLS_DATA_PATH=/var/lib/registrytools
export REGISTRYTOOLS_TRANSPORT=http
export REGISTRYTOOLS_LOG_LEVEL=INFO
export REGISTRYTOOLS_ENABLE_AUTH=true

# 启动服务
registry-tools --host 0.0.0.0 --port 8000

# 使用 systemd 管理（推荐）
# /etc/systemd/system/registrytools.service
[Unit]
Description=RegistryTools MCP Server
After=network.target

[Service]
Type=simple
User=registrytools
Environment="REGISTRYTOOLS_DATA_PATH=/var/lib/registrytools"
Environment="REGISTRYTOOLS_TRANSPORT=http"
Environment="REGISTRYTOOLS_ENABLE_AUTH=true"
ExecStart=/usr/local/bin/registry-tools --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

### 场景 4: Docker 部署

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN pip install -e .

ENV REGISTRYTOOLS_DATA_PATH=/data
ENV REGISTRYTOOLS_TRANSPORT=http
ENV REGISTRYTOOLS_ENABLE_AUTH=true

EXPOSE 8000

CMD ["registry-tools", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  registrytools:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - registrytools-data:/data
    environment:
      - REGISTRYTOOLS_ENABLE_AUTH=true
      - REGISTRYTOOLS_LOG_LEVEL=INFO

volumes:
  registrytools-data:
```

### 场景 5: Claude Desktop 集成

```json
// ~/Library/Application Support/Claude/claude_desktop_config.json (macOS)
// %APPDATA%\Claude\claude_desktop_config.json (Windows)
// ~/.config/Claude/claude_desktop_config.json (Linux)

{
  "mcpServers": {
    "RegistryTools": {
      "command": "uvx",
      "args": ["registry-tools"],
      "env": {
        "REGISTRYTOOLS_DATA_PATH": "~/.RegistryTools",
        "REGISTRYTOOLS_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

---

## 相关文档

- [用户指南](USER_GUIDE.md) - 快速开始和基本使用
- [API 文档](API.md) - 完整的 API 参考
- [架构设计](ARCHITECTURE.md) - 系统架构和设计决策
- [最佳实践](BEST_PRACTICES.md) - 工具命名和优化建议
- [故障排除](TROUBLESHOOTING.md) - 常见问题和解决方案

---

**维护者**: Maric
**文档版本**: v0.2.1
