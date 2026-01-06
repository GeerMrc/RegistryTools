# RegistryTools - Claude Code 配置指南

> **版本**: v0.1.0
> **更新日期**: 2026-01-05
> **项目**: RegistryTools - MCP Tool Registry Server

本文档描述如何在 Claude Code 中配置和使用 RegistryTools。

---

## Claude Desktop 配置

### 配置文件位置

根据操作系统，Claude Desktop 配置文件位于：

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### STDIO 模式配置

推荐使用 STDIO 模式进行本地集成：

```json
{
  "mcpServers": {
    "RegistryTools": {
      "command": "uvx",
      "args": ["Registry_Tools", "--data-path", "~/.RegistryTools"]
    }
  }
}
```

### HTTP 模式配置

如果使用远程 HTTP 服务：

```json
{
  "mcpServers": {
    "RegistryTools": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

### 完整配置示例

```json
{
  "mcpServers": {
    "RegistryTools": {
      "command": "uvx",
      "args": [
        "Registry_Tools",
        "--data-path", "~/.RegistryTools",
        "--transport", "stdio"
      ],
      "env": {
        "REGISTRYTOOLS_LOG_LEVEL": "INFO"
      }
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/files"]
    }
  }
}
```

---

## Cline (VSCode) 配置

### 项目级配置

在项目根目录创建 `.cline/settings.json`：

```json
{
  "mcpServers": {
    "RegistryTools": {
      "command": "uvx",
      "args": ["Registry_Tools"]
    }
  }
}
```

### 用户级配置

在 Cline 设置中添加 MCP 服务器配置。

---

## Cursor 配置

### 方法 1: 通过 Cursor 设置

1. 打开 Cursor 设置
2. 导航到 MCP Servers
3. 添加新服务器：
   - 名称: `RegistryTools`
   - 命令: `uvx`
   - 参数: `["Registry_Tools"]`

### 方法 2: 使用 fastmcp.json

在项目根目录创建 `fastmcp.json`：

```json
{
  "$schema": "https://gofastmcp.com/public/schemas/fastmcp.json/v1.json",
  "source": {
    "path": "src/registrytools/__main__.py",
    "entrypoint": "main"
  },
  "deployment": {
    "transport": "stdio",
    "log_level": "INFO"
  }
}
```

---

## 环境变量配置

### 可用环境变量

| 环境变量 | 默认值 | 描述 |
|---------|--------|------|
| `REGISTRYTOOLS_DATA_PATH` | `~/.RegistryTools` | 数据目录路径 |
| `REGISTRYTOOLS_LOG_LEVEL` | `INFO` | 日志级别 |
| `REGISTRYTOOLS_TRANSPORT` | `stdio` | 传输协议 |

### 配置示例

```json
{
  "mcpServers": {
    "RegistryTools": {
      "command": "uvx",
      "args": ["Registry_Tools"],
      "env": {
        "REGISTRYTOOLS_DATA_PATH": "/custom/data/path",
        "REGISTRYTOOLS_LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

---

## 验证配置

### 1. 重启 Claude Desktop

配置文件修改后，需要重启 Claude Desktop。

### 2. 检查 MCP 连接

在 Claude Desktop 中，查看 MCP 服务器状态。RegistryTools 应该显示为已连接。

### 3. 测试工具调用

在 Claude Desktop 中输入：

```
搜索 GitHub 创建 PR 的工具
```

Claude 应该会调用 `search_tools` 工具并返回结果。

---

## 常见问题

### Q: Claude Desktop 找不到 MCP 服务器

**解决方案**:
1. 确认配置文件路径正确
2. 检查 JSON 格式是否正确
3. 重启 Claude Desktop
4. 查看 Claude Desktop 日志

### Q: uvx 命令不可用

**解决方案**:
1. 安装 uv: `pip install uv`
2. 或使用 pip 安装: `pip install Registry_Tools`
3. 配置中使用完整 Python 路径

### Q: 工具调用无响应

**解决方案**:
1. 检查数据目录权限
2. 查看日志: 设置 `REGISTRYTOOLS_LOG_LEVEL=DEBUG`
3. 确认 RegistryTools 进程正在运行

---

## 高级配置

### 自定义工具集

如果需要使用自定义工具集，可以配置环境变量指向自定义数据目录：

```json
{
  "mcpServers": {
    "RegistryTools-Custom": {
      "command": "uvx",
      "args": [
        "Registry_Tools",
        "--data-path", "/path/to/custom/tools"
      ]
    }
  }
}
```

### 多实例配置

可以同时运行多个 RegistryTools 实例：

```json
{
  "mcpServers": {
    "RegistryTools-GitHub": {
      "command": "uvx",
      "args": ["Registry_Tools", "--data-path", "~/.RegistryTools-github"]
    },
    "RegistryTools-GitLab": {
      "command": "uvx",
      "args": ["Registry_Tools", "--data-path", "~/.RegistryTools-gitlab"]
    }
  }
}
```

---

## 相关文档

- [用户指南](USER_GUIDE.md)
- [安装指南](INSTALLATION.md)
- [架构设计](ARCHITECTURE.md)

---

**维护者**: Maric
**文档版本**: v1.0
