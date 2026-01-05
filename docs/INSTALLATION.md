# RegistryTools 安装指南

> **版本**: v0.1.0
> **更新日期**: 2026-01-05
> **项目**: RegistryTools - MCP Tool Registry Server

本文档描述如何在不同环境中安装 RegistryTools。

---

## 系统要求

- Python 3.10 或更高版本
- pip 或 uv 包管理器

---

## 安装方法

### 方法 1: 使用 uvx (推荐)

[uvx](https://github.com/astral-sh/uv) 是运行 Python 工具的最简单方式：

```bash
uvx Registry-Tools
```

### 方法 2: 使用 pip

#### 从 PyPI 安装

```bash
pip install Registry-Tools
```

#### 从源码安装

```bash
# 克隆仓库
git clone https://github.com/maric/RegistryTools.git
cd RegistryTools

# 以可编辑模式安装
pip install -e .
```

### 方法 3: 使用 uv

```bash
uv pip install Registry-Tools
```

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

**方式 1: 命令行参数**

```bash
registry-tools --log-level DEBUG
```

**方式 2: 环境变量**

```bash
export REGISTRYTOOLS_LOG_LEVEL=DEBUG
registry-tools
```

**日志格式**:
```
YYYY-MM-DD HH:MM:SS - registrytools - LEVEL - Message
```

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

### Cursor

在 Cursor 设置中添加 MCP 服务器配置，或在项目中使用 `fastmcp.json`。

---

## Docker 部署

### 创建 Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# 安装 RegistryTools
RUN pip install Registry-Tools

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
pip uninstall Registry-Tools
```

如果使用 uvx 安装，无需卸载，uvx 会自动管理版本。

---

## 更新

```bash
# 使用 pip
pip install --upgrade Registry-Tools

# 使用 uv
uv pip install --upgrade Registry-Tools
```

---

**维护者**: Maric
**文档版本**: v1.0
