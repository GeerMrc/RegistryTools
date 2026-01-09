# RegistryTools 配置指南

**版本**: v0.1.0
**更新日期**: 2026-01-09
**项目**: RegistryTools - MCP Tool Registry Server

---

## ⚠️ PyPI 发布状态

**RegistryTools 尚未发布到 PyPI**

### 当前安装方式

仅支持从源码本地安装：

```bash
# 从源码安装
git clone https://github.com/GeerMrc/RegistryTools.git
cd RegistryTools
pip install -e .
```

### 安装后配置命令

```json
{
  "command": "registry-tools"
}
```

❌ **不可用**: `uvx registry-tools`（仅在 PyPI 发布后可用）

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

### 搜索性能优化

#### 选择合适的搜索方法

| 方法 | 适用场景 | 速度 | 准确率 |
|------|----------|------|--------|
| `regex` | 已知工具名称，精确匹配 | 最快 | 高 |
| `bm25` | 语义搜索，自然语言查询 | 快 | 高 |

**示例**:
```python
# 精确查找（已知工具名称）
search_tools("github.*pull", "regex", 10)

# 语义搜索（自然语言）
search_tools("如何在 GitHub 上创建 PR", "bm25", 5)
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

| 指标 | 目标值 | 测试条件 |
|------|--------|----------|
| 搜索响应时间 | < 200ms | 1000+ 工具 |
| 内存占用 | < 100MB | 1000+ 工具 |
| 索引构建时间 | < 2s | 1000+ 工具 |
| 热工具加载 | < 100ms | 100 个工具 |

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
**文档版本**: v0.1.0
