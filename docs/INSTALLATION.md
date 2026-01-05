# RegistryTools 安装指南

> **版本**: v1.0
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

```json
{
  "mcpServers": {
    "RegistryTools": {
      "url": "http://localhost:8000/mcp"
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

# 启动 HTTP 服务器
CMD ["registry-tools", "--transport", "http", "--host", "0.0.0.0", "--port", "8000"]
```

### 构建和运行

```bash
# 构建镜像
docker build -t registrytools .

# 运行容器
docker run -p 8000:8000 -v ~/.RegistryTools:/data registrytools
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
