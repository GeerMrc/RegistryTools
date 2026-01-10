# RegistryTools - Claude Code 配置指南

**版本**: v0.1.1
**更新日期**: 2026-01-09
**项目**: RegistryTools - MCP Tool Registry Server

---

## ⚠️ PyPI 发布状态

> **注意**: RegistryTools 尚未发布到 PyPI，当前仅支持本地开发环境安装。
> 详见 [安装指南 - PyPI 发布状态](INSTALLATION.md#pypi-发布状态)。

---

本文档描述如何在 Claude Code 和 Claude Desktop 中配置和使用 RegistryTools。

---

## Claude Code (VSCode) 配置

Claude Code 是 Anthropic 官方的 VSCode AI 助手，支持通过 MCP 协议集成 RegistryTools。

### 方式 1：CLI 命令（推荐）

使用 Claude Code CLI 命令快速配置，一行命令完成：

> **重要提示**:
> - **本地开发环境**: 使用 `pip install -e .` 安装后，使用 `registry-tools` 命令
> - **PyPI 发布后**: 可以使用 `uvx registry-tools` 无需安装

**STDIO 本地服务器**：

**本地开发环境配置** (推荐用于开发):
```bash
# 基础配置
claude mcp add --transport stdio RegistryTools -- registry-tools

# 带环境变量
claude mcp add --transport stdio RegistryTools \
  --env REGISTRYTOOLS_LOG_LEVEL=INFO \
  -- registry-tools
```

**PyPI 发布后配置** (推荐用于生产):
```bash
# 基础配置（使用 uvx）
claude mcp add --transport stdio RegistryTools -- uvx registry-tools

# 带环境变量
claude mcp add --transport stdio RegistryTools \
  --env REGISTRYTOOLS_LOG_LEVEL=INFO \
  -- uvx registry-tools
```

**Streamable HTTP 远程服务器**：
```bash
# 无认证
claude mcp add --transport http RegistryTools-Remote http://localhost:8000/mcp

# 使用 RegistryTools 内置 API Key 认证（Phase 15，推荐）
# 1. 先启用认证并创建 API Key
registry-tools --transport http --enable-auth
registry-tools api-key create "Claude Code" --permission read

# 2. 添加服务器（使用 API Key）
claude mcp add --transport http RegistryTools-Remote \
  http://localhost:8000/mcp \
  --header "X-API-Key: rtk_your_api_key_here"
```

**管理命令**：
```bash
claude mcp list              # 列出所有服务器
claude mcp get RegistryTools  # 查看详情
claude mcp remove RegistryTools  # 删除服务器
```

**配置范围**：
```bash
# 项目级配置（可版本控制）
# 本地开发环境
claude mcp add --scope project --transport stdio RegistryTools -- registry-tools
# PyPI 发布后
claude mcp add --scope project --transport stdio RegistryTools -- uvx registry-tools

# 用户级配置（跨项目使用）
# 本地开发环境
claude mcp add --scope user --transport stdio RegistryTools -- registry-tools
# PyPI 发布后
claude mcp add --scope user --transport stdio RegistryTools -- uvx registry-tools
```

### 方式 2：配置文件

创建 `.claude/config.json`（项目级）或 `~/.claude/config.json`（用户级）：

**本地开发环境配置** (推荐用于开发):
```json
{
  "mcpServers": {
    "RegistryTools": {
      "command": "registry-tools",
      "env": {
        "REGISTRYTOOLS_DATA_PATH": "~/.RegistryTools",
        "REGISTRYTOOLS_LOG_LEVEL": "INFO"
      }
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
      "args": ["registry-tools"],
      "env": {
        "REGISTRYTOOLS_DATA_PATH": "~/.RegistryTools",
        "REGISTRYTOOLS_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### 方式 3：JSON 配置命令 (add-json)

使用 `claude mcp add-json` 命令直接通过 JSON 配置添加 MCP 服务器：

**STDIO 本地服务器**：

**本地开发环境配置** (推荐用于开发):
```bash
# 基础配置
claude mcp add-json "RegistryTools" '{"command": "registry-tools"}' --scope user

# 带环境变量
claude mcp add-json "RegistryTools" '{
  "command": "registry-tools",
  "env": {
    "REGISTRYTOOLS_DATA_PATH": "~/.RegistryTools",
    "REGISTRYTOOLS_LOG_LEVEL": "INFO"
  }
}' --scope user
```

**PyPI 发布后配置** (推荐用于生产):
```bash
# 基础配置（使用 uvx）
claude mcp add-json "RegistryTools" '{"command": "uvx", "args": ["registry-tools"]}' --scope user

# 带环境变量
claude mcp add-json "RegistryTools" '{
  "command": "uvx",
  "args": ["registry-tools"],
  "env": {
    "REGISTRYTOOLS_DATA_PATH": "~/.RegistryTools",
    "REGISTRYTOOLS_LOG_LEVEL": "INFO"
  }
}' --scope user
```

**Streamable HTTP 远程服务器**：
```bash
# 无认证
claude mcp add-json "RegistryTools-Remote" '{
  "url": "http://localhost:8000/mcp"
}' --scope user

# 使用 API Key 认证
claude mcp add-json "RegistryTools-Remote" '{
  "url": "http://localhost:8000/mcp",
  "headers": {
    "X-API-Key": "rtk_your_api_key_here"
  }
}' --scope user
```

**配置范围**：
```bash
# 项目级配置（可版本控制）
claude mcp add-json "RegistryTools" '{...}' --scope project

# 用户级配置（跨项目使用，默认）
claude mcp add-json "RegistryTools" '{...}' --scope user

# 本地级配置（项目特定，gitignored）
claude mcp add-json "RegistryTools" '{...}' --scope local
```

### MCP 配置参数说明

Claude Code MCP 配置支持以下可选参数：

| 参数 | 类型 | 描述 | 示例 |
|------|------|------|------|
| `description` | string | MCP 服务器描述信息 | `"统一的 MCP 工具注册与搜索服务"` |
| `priority` | number | 服务器优先级（数字越小优先级越高） | `10` |

**完整配置示例**：
```bash
claude mcp add-json "RegistryTools" '{
  "command": "uvx",
  "args": ["registry-tools"],
  "env": {
    "REGISTRYTOOLS_DATA_PATH": "$HOME/.RegistryTools",
    "REGISTRYTOOLS_LOG_LEVEL": "INFO"
  },
  "description": "统一的 MCP 工具注册与搜索服务，用于发现和筛选可用工具",
  "priority": 10
}' --scope user
```

> **注意**: `description` 和 `priority` 是 Claude Code 的元数据字段，用于在 MCP 服务器列表中显示和排序，不会传递给 MCP 服务器进程。

---

## Claude Desktop 配置

### 配置文件位置

根据操作系统，Claude Desktop 配置文件位于：

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### STDIO 模式配置

推荐使用 STDIO 模式进行本地集成：

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

**本地开发环境配置** (推荐用于开发):
```json
{
  "mcpServers": {
    "RegistryTools": {
      "command": "registry-tools",
      "args": [
        "--data-path", "~/.RegistryTools"
      ],
      "env": {
        "REGISTRYTOOLS_LOG_LEVEL": "INFO"
      }
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
      "args": [
        "registry-tools",
        "--data-path", "~/.RegistryTools"
      ],
      "env": {
        "REGISTRYTOOLS_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

---

## Cline (VSCode) 配置

### 项目级配置

在项目根目录创建 `.cline/settings.json`：

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

### 用户级配置

在 Cline 设置中添加 MCP 服务器配置。

---

## Cursor 配置

### 方法 1: 通过 Cursor 设置

1. 打开 Cursor 设置
2. 导航到 MCP Servers
3. 添加新服务器：

**本地开发环境配置** (推荐用于开发):
   - 名称: `RegistryTools`
   - 命令: `registry-tools`

**PyPI 发布后配置** (推荐用于生产):
   - 名称: `RegistryTools`
   - 命令: `uvx`
   - 参数: `["registry-tools"]`

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
| `REGISTRYTOOLS_ENABLE_AUTH` | `false` | 启用 API Key 认证（仅 HTTP 模式） |
| `REGISTRYTOOLS_DESCRIPTION` | 统一的 MCP 工具注册与搜索服务，用于发现和筛选可用工具，提升任务执行工具调用准确性，复杂任务工具调用效率 | MCP 服务器描述 |

> **完整配置**: 更多环境变量、可选值和详细说明，请参考 [配置指南](CONFIGURATION.md#环境变量配置)。

### 配置示例

**本地开发环境配置** (推荐用于开发):
```json
{
  "mcpServers": {
    "RegistryTools": {
      "command": "registry-tools",
      "env": {
        "REGISTRYTOOLS_DATA_PATH": "/custom/data/path",
        "REGISTRYTOOLS_LOG_LEVEL": "DEBUG"
      }
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
      "args": ["registry-tools"],
      "env": {
        "REGISTRYTOOLS_DATA_PATH": "/custom/data/path",
        "REGISTRYTOOLS_LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

### 路径配置说明

`REGISTRYTOOLS_DATA_PATH` 支持多种路径格式：

| 路径格式 | 示例 | 推荐度 |
|----------|------|--------|
| 波浪号 | `~/.RegistryTools` | ✅ 推荐 |
| 绝对路径 | `/home/user/.RegistryTools` | ✅ 推荐 |
| 相对路径 | `./.RegistryTools` | ⚠️ 谨慎使用 |

> **详细说明**: 请查看 [配置指南 - 路径配置说明](CONFIGURATION.md#路径配置说明) 了解每种路径格式的详细说明、适用场景和最佳实践。
>
> **版本说明**: RegistryTools v0.1.0 及以上版本已修复波浪号（`~`）展开问题，可直接使用 `~/.RegistryTools` 格式。

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

### Q: uvx 命令不可用或连接失败

**问题原因**: `uvx registry-tools` 需要包已发布到 PyPI 才能工作。

**本地开发环境解决方案**:
1. 使用 `pip install -e .` 安装本地开发版本
2. 配置中使用 `registry-tools` 命令而非 `uvx`
3. 或使用 `python -m registrytools`

**生产环境解决方案** (PyPI 发布后):
1. 确保已安装 uv: `pip install uv`
2. 使用 `uvx registry-tools` 无需手动安装
3. 或使用 `pip install registry-tools` 然后 `registry-tools` 命令

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
        "registry-tools",
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
      "args": ["registry-tools", "--data-path", "~/.RegistryTools-github"]
    },
    "RegistryTools-GitLab": {
      "command": "uvx",
      "args": ["registry-tools", "--data-path", "~/.RegistryTools-gitlab"]
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
