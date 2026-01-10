# RegistryTools 安装指南

**版本**: v0.1.1
**更新日期**: 2026-01-09
**项目**: RegistryTools - MCP Tool Registry Server

---

## ⚠️ PyPI 发布状态 {#pypi-发布状态}

**RegistryTools 尚未发布到 PyPI**

### 当前安装方式

仅支持从源码本地安装：

```bash
# 从源码安装
git clone https://github.com/GeerMrc/RegistryTools.git
cd RegistryTools
pip install -e .
# 或使用 uv
uv pip install -e .
```

### 安装后配置命令

```json
{
  "command": "registry-tools"
}
```

❌ **不可用**: `uvx registry-tools`（仅在 PyPI 发布后可用）

---

本文档描述如何在不同环境中安装 RegistryTools。

---

## 系统要求

- Python 3.10 或更高版本
- pip 或 uv 包管理器

---

## 安装方法

> **重要提示**:
> - **本地开发环境**: 从源码使用 `pip install -e .` 安装
> - **PyPI 发布后**: 可以使用 `pip install registry-tools` 或 `uvx registry-tools`

### 方法 1: 本地开发环境安装（当前）

从源码以可编辑模式安装：

```bash
# 克隆仓库
git clone https://github.com/maric/RegistryTools.git
cd RegistryTools

# 以可编辑模式安装
pip install -e .
```

安装后可以直接使用命令：
```bash
registry-tools --version
```

### 方法 2: 从 PyPI 安装（发布后）

> **注意**: 此方法仅在包发布到 PyPI 后可用

```bash
# 使用 pip 安装
pip install registry-tools

# 或使用 uv 安装
uv pip install registry-tools

# 或使用 uvx（无需安装）
uvx registry-tools
```

### 方法 3: 使用 uvx（发布后推荐）

[uvx](https://github.com/astral-sh/uv) 是运行 Python 工具的最简单方式：

```bash
uvx registry-tools
```

**优势**:
- 无需手动安装包
- 自动使用最新版本
- 隔离的运行环境

---

## 验证安装

安装完成后，验证工具是否可用：

```bash
# 查看版本
registry-tools --version

# 查看帮助
registry-tools --help
```

预期输出：

```
RegistryTools v0.1.0

usage: registry-tools [-h] [--data-path DATA_PATH] [--transport {stdio,http}]
                      [--host HOST] [--port PORT] [--path PATH] [--version]

RegistryTools - MCP Tool Registry Server
...
```

---

## 配置选项

### 数据目录

RegistryTools 默认使用 `~/.RegistryTools` 作为数据目录。可以通过以下方式自定义：

#### 方式 1: 命令行参数

```bash
registry-tools --data-path /path/to/data
```

#### 方式 2: 环境变量

```bash
export REGISTRYTOOLS_DATA_PATH=/path/to/data
registry-tools
```

### 传输协议

RegistryTools 支持两种传输协议：

#### STDIO (默认)

适用于本地 CLI 集成：

```bash
registry-tools
```

#### Streamable HTTP

适用于远程服务部署：

```bash
registry-tools --transport http --host 0.0.0.0 --port 8000
```

### 日志配置

RegistryTools 使用 Python 标准库 `logging` 模块记录运行日志。

**日志级别**:
- `DEBUG`: 详细调试信息
- `INFO`: 一般信息（默认）
- `WARNING`: 警告信息
- `ERROR`: 错误信息

**配置方式**:

#### 方式 1: 环境变量配置

```bash
export REGISTRYTOOLS_LOG_LEVEL=DEBUG
registry-tools
```

#### 方式 2: fastmcp.json 配置文件

编辑 `fastmcp.json` 或 `fastmcp.http.json`：

```json
{
  "$schema": "https://gofastmcp.com/public/schemas/fastmcp.json/v1.json",
  "source": {
    "path": "src/registrytools/__main__.py",
    "entrypoint": "main"
  },
  "deployment": {
    "transport": "stdio",
    "log_level": "DEBUG"  // 修改此处的日志级别
  }
}
```

**注意**: CLI 参数 `--log-level` 不支持，请使用环境变量或配置文件。

**详细配置**: 参见 [配置指南 - 日志配置](CONFIGURATION.md#日志配置)

**查看日志**:

```bash
# STDOUT 输出（默认）
registry-tools

# 重定向到文件
registry-tools > registrytools.log 2>&1
```

### API Key 认证 (Phase 15)

RegistryTools 支持可选的 API Key 认证功能，用于保护 HTTP 模式下的服务访问。

#### 启用认证

**方式 1: 命令行参数**

```bash
registry-tools --transport http --port 8000 --enable-auth
```

**方式 2: 环境变量**

```bash
export REGISTRYTOOLS_ENABLE_AUTH=true
registry-tools --transport http --port 8000
```

#### API Key 管理

启用认证后，需要创建和管理 API Key：

```bash
# 创建只读 API Key
registry-tools api-key create "只读 Key" --permission read

# 创建读写 API Key
registry-tools api-key create "读写 Key" --permission write

# 创建带过期时间的 Key（1 小时）
registry-tools api-key create "临时 Key" --expires-in 3600

# 列出所有 API Key
registry-tools api-key list

# 删除 API Key
registry-tools api-key delete <key-id>
```

#### 认证配置说明

- **STDIO 模式**: 不需要认证，适用于本地可信环境
- **HTTP 模式**: 认证可选，默认关闭
- **权限级别**:
  - `read`: 只读权限，可以搜索和查看工具定义
  - `write`: 读写权限，可以注册新工具
  - `admin`: 管理员权限，包含所有操作

详细使用说明请参考 [API 文档](API.md#api-key-认证-phase-15) 和 [用户指南](USER_GUIDE.md#api-key-认证-phase-15)。

---

## MCP 客户端配置

### Claude Desktop

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

**Linux**: `~/.config/Claude/claude_desktop_config.json`

#### STDIO 模式配置

> **重要提示**:
> - **本地开发环境**: 使用 `pip install -e .` 安装后，使用 `registry-tools` 命令
> - **PyPI 发布后**: 可以使用 `uvx registry-tools` 无需安装

**本地开发环境配置** (推荐用于开发):
```json
{
  "mcpServers": {
    "RegistryTools": {
      "command": "registry-tools",
      "args": ["--data-path", "~/.RegistryTools"]
    }
  }
}
```

**PyPI 发布后配置** (推荐用于生产):
```json
{
  "mcpServers": {
    "RegistryTools": {
      "command": "uvx",
      "args": ["registry-tools", "--data-path", "~/.RegistryTools"]
    }
  }
}
```

#### HTTP 模式配置

**不带认证**：

```json
{
  "mcpServers": {
    "RegistryTools": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

**带 API Key 认证**（需要先启用认证并创建 API Key）：

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

或者使用 Bearer Token 格式：

```json
{
  "mcpServers": {
    "RegistryTools": {
      "url": "http://localhost:8000/mcp",
      "headers": {
        "Authorization": "Bearer rtk_a1b2c3d4e5f6789012345678901234567890123456789012345678901234"
      }
    }
  }
}
```

### Cline (VSCode)

在 `.cline/settings.json` 中配置：

> **重要提示**:
> - **本地开发环境**: 使用 `pip install -e .` 安装后，使用 `registry-tools` 命令
> - **PyPI 发布后**: 可以使用 `uvx registry-tools` 无需安装

**本地开发环境配置** (推荐用于开发):
```json
{
  "mcpServers": {
    "RegistryTools": {
      "command": "registry-tools"
    }
  }
}
```

**PyPI 发布后配置** (推荐用于生产):
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

### Cursor

在 Cursor 设置中添加 MCP 服务器配置，或在项目中使用 `fastmcp.json`。

> **重要提示**:
> - **本地开发环境**: 使用 `pip install -e .` 安装后，使用 `registry-tools` 命令
> - **PyPI 发布后**: 可以使用 `uvx registry-tools` 无需安装

**本地开发环境配置** (推荐用于开发):
- 命令: `registry-tools`

**PyPI 发布后配置** (推荐用于生产):
- 命令: `uvx`
- 参数: `["registry-tools"]`

---

## Docker 部署

### 创建 Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# 安装 RegistryTools
RUN pip install registry-tools

# 暴露 HTTP 端口
EXPOSE 8000

# 启动 HTTP 服务器（不带认证）
CMD ["registry-tools", "--transport", "http", "--host", "0.0.0.0", "--port", "8000"]

# 或者启用认证
# CMD ["registry-tools", "--transport", "http", "--host", "0.0.0.0", "--port", "8000", "--enable-auth"]
```

### 构建和运行

```bash
# 构建镜像
docker build -t registrytools .

# 运行容器（不带认证）
docker run -p 8000:8000 -v ~/.RegistryTools:/data registrytools

# 运行容器（启用认证）
docker run -p 8000:8000 -v ~/.RegistryTools:/data -e REGISTRYTOOLS_ENABLE_AUTH=true registrytools
```

### 使用 Docker Compose（推荐）

创建 `docker-compose.yml`：

```yaml
version: '3.8'
services:
  registrytools:
    image: registrytools:latest
    ports:
      - "8000:8000"
    volumes:
      - ~/.RegistryTools:/data
    environment:
      - REGISTRYTOOLS_ENABLE_AUTH=true  # 启用认证
      - REGISTRYTOOLS_DATA_PATH=/data
    restart: unless-stopped
```

运行：

```bash
docker-compose up -d
```

---

## 开发环境安装

### 克隆仓库

```bash
git clone https://github.com/maric/RegistryTools.git
cd RegistryTools
```

### 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
```

### 安装开发依赖

```bash
pip install -e ".[dev]"
```

### 验证开发环境

```bash
# 运行测试
pytest tests/

# 代码格式化
black src/registrytools tests/

# 代码检查
ruff check src/registrytools tests/
```

---

## 故障排除

### 问题: uvx 命令无法连接

**问题原因**: `uvx registry-tools` 需要包已发布到 PyPI 才能工作。

**本地开发环境解决方案**:
```bash
# 1. 使用 pip install -e . 安装本地开发版本
pip install -e .

# 2. 配置中使用 registry-tools 命令而非 uvx
# Claude Desktop
{
  "mcpServers": {
    "RegistryTools": {
      "command": "registry-tools"
    }
  }
}

# Claude Code CLI
claude mcp add --transport stdio RegistryTools -- registry-tools
```

**生产环境解决方案** (PyPI 发布后):
```bash
# 1. 确保已安装 uv
pip install uv

# 2. 使用 uvx 无需手动安装
uvx registry-tools

# 或使用 pip 安装
pip install registry-tools
```

### 问题: 安装后命令不可用

**解决方案**: 确保 Python Scripts 目录在 PATH 中：

```bash
# Windows
set PATH=%PATH%;%APPDATA%\Python\Scripts

# Linux/Mac
export PATH="$HOME/.local/bin:$PATH"
```

### 问题: 导入错误

**解决方案**: 确保使用正确的导入路径：

```python
# 正确
from registrytools import ToolRegistry

# 错误
from RegistryTools import ToolRegistry
```

### 问题: MCP 客户端连接失败

**解决方案**:

1. 检查服务是否正在运行：

```bash
registry-tools --version
```

2. 检查配置文件路径是否正确

3. 查看客户端日志获取详细错误信息

---

## 卸载

```bash
pip uninstall registry-tools
```

如果使用 uvx 安装，无需卸载，uvx 会自动管理版本。

---

## 更新

```bash
# 使用 pip
pip install --upgrade registry-tools

# 使用 uv
uv pip install --upgrade registry-tools
```

---

## 相关文档

### 配置指南
- [CONFIGURATION.md](CONFIGURATION.md) - 配置参数完整说明
- [CLAUDE_CONFIG.md](CLAUDE_CONFIG.md) - Claude Desktop 配置指南
- [IDE_CONFIG.md](IDE_CONFIG.md) - IDE (VS Code/Cursor) 配置指南

### 使用指南
- [USER_GUIDE.md](USER_GUIDE.md) - 用户使用指南
- [API.md](API.md) - API 参考文档
- [BEST_PRACTICES.md](BEST_PRACTICES.md) - 最佳实践

### 支持文档
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - 故障排除
- [PUBLISHING.md](PUBLISHING.md) - PyPI 发布指南
- [CHANGELOG.md](CHANGELOG.md) - 变更日志

---

**维护者**: Maric
**文档版本**: v1.0
