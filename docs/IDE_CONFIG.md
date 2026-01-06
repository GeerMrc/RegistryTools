# RegistryTools IDE 配置指南

> **版本**: v0.1.0
> **更新日期**: 2026-01-05
> **适用对象**: Claude Desktop、Claude Code、Cursor、Continue.dev、Cline 等 MCP 客户端用户

---

## 概述

RegistryTools 是一个独立的 MCP Tool Registry Server，提供通用的工具搜索和发现能力。本文档提供主流 IDE 的快速配置示例。

### 支持的 IDE

| IDE / 编辑器 | 支持状态 | 传输模式 | 推荐度 |
|-------------|---------|----------|--------|
| Claude Desktop | ✅ 完全支持 | STDIO / Streamable HTTP | ⭐⭐⭐⭐⭐ |
| Claude Code (VSCode) | ✅ 完全支持 | STDIO / Streamable HTTP | ⭐⭐⭐⭐⭐ |
| Cursor | ✅ 完全支持 | STDIO / Streamable HTTP | ⭐⭐⭐⭐⭐ |
| Continue.dev | ✅ 完全支持 | STDIO | ⭐⭐⭐⭐ |
| Cline (VSCode) | ✅ 完全支持 | STDIO | ⭐⭐⭐⭐ |
| 其他 MCP 客户端 | ✅ 协议兼容 | STDIO / HTTP | ⭐⭐⭐ |

### 核心价值

- **减少 Token 消耗 85%**: 从 ~77K 降至 ~8.7K（按需加载工具）
- **提升准确率**: 工具选择准确率从 49% 提升至 74%
- **解耦复用**: 独立部署，任何 MCP 客户端都可连接

---

## Claude Desktop 配置

### 配置文件位置

| 操作系统 | 配置文件路径 |
|---------|-------------|
| **macOS** | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| **Windows** | `%APPDATA%/Claude/claude_desktop_config.json` |
| **Linux** | `~/.config/Claude/claude_desktop_config.json` |

### 基础 STDIO 配置（推荐）

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

### STDIO + 环境变量配置

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

### Streamable HTTP 模式配置（远程服务器）

```json
{
  "mcpServers": {
    "RegistryTools-Remote": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

**带认证的 HTTP 配置**：

RegistryTools 支持两种认证方式：

**方式 1: 内置 API Key 认证（Phase 15，推荐）**

RegistryTools 提供内置的 API Key 认证功能：

```bash
# 1. 启用认证启动服务
registry-tools --transport http --port 8000 --enable-auth

# 2. 创建 API Key
registry-tools api-key create "My Client" --permission read

# 3. 客户端使用 API Key
```

```json
{
  "mcpServers": {
    "RegistryTools": {
      "url": "http://localhost:8000/mcp",
      "headers": {
        "X-API-Key": "rtk_your_api_key_here"
      }
    }
  }
}
```

> **注意**: 这是 RegistryTools 内置的 API Key 认证，无需额外配置反向代理。详见 [用户指南 - API Key 认证](USER_GUIDE.md#api-key-认证-phase-15)。

**方式 2: 反向代理认证（可选）**

如果需要使用反向代理（如 Nginx、Caddy）进行认证：

```json
{
  "mcpServers": {
    "RegistryTools-Remote": {
      "url": "http://localhost:8000/mcp",
      "headers": {
        "X-API-Key": "your-api-key-here"
      }
    }
  }
}
```

### 使用 pip 安装版本

如果使用 `pip install registry-tools` 安装：

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

### 多实例配置（本地 + 远程）

**本地开发环境配置** (推荐用于开发):
```json
{
  "mcpServers": {
    "RegistryTools-Local": {
      "command": "registry-tools",
      "args": ["--data-path", "~/.RegistryTools"],
      "env": {
        "REGISTRYTOOLS_LOG_LEVEL": "DEBUG"
      }
    },
    "RegistryTools-Remote": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

**PyPI 发布后配置** (推荐用于生产):
```json
{
  "mcpServers": {
    "RegistryTools-Local": {
      "command": "uvx",
      "args": ["registry-tools", "--data-path", "~/.RegistryTools"],
      "env": {
        "REGISTRYTOOLS_LOG_LEVEL": "DEBUG"
      }
    },
    "RegistryTools-Remote": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

---

## Claude Code (VSCode) 配置

Claude Code 是 Anthropic 官方的 VSCode AI 助手，支持通过 MCP 协议集成 RegistryTools。

### 方式 1：CLI 命令（推荐）

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

# 3. 或使用反向代理认证（可选）
claude mcp add --transport http RegistryTools-Remote \
  http://localhost:8000/mcp \
  --header "X-API-Key: your-proxy-key"
```

> **认证说明**:
> - **内置认证**: RegistryTools 提供内置的 API Key 认证功能（Phase 15），使用 `--enable-auth` 启用后，通过 `registry-tools api-key` 命令管理密钥。
> - **反向代理**: 也可使用反向代理（如 Nginx、Caddy）进行认证，`--header` 参数设置的 headers 会被发送到反向代理验证。

**管理命令**：
```bash
claude mcp list              # 列出所有服务器
claude mcp get RegistryTools  # 查看详情
claude mcp remove RegistryTools  # 删除服务器
```

### 方式 2：配置文件

创建 `.claude/config.json`（项目级）或 `~/.claude/config.json`（用户级）：

**基础配置**：
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

**使用源码开发模式**：
```json
{
  "mcpServers": {
    "RegistryTools": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/RegistryTools",
        "run",
        "registry-tools"
      ],
      "env": {
        "REGISTRYTOOLS_DATA_PATH": "./.RegistryTools-dev"
      }
    }
  }
}
```

### 配置范围

| 范围 | 命令参数 | 存储位置 | 适用场景 |
|------|---------|---------|----------|
| **本地** | `--scope local`（默认） | 项目特定用户设置 | 个人开发、敏感凭证 |
| **项目** | `--scope project` | `.mcp.json`（可版本控制） | 团队共享 |
| **用户** | `--scope user` | 用户级全局配置 | 跨项目使用 |

**配置范围示例**：
```bash
# 项目级配置（可版本控制）
claude mcp add --scope project --transport stdio RegistryTools -- uvx registry-tools

# 用户级配置（跨项目使用）
claude mcp add --scope user --transport stdio RegistryTools -- uvx registry-tools
```

---

## Cursor 配置

Cursor 是基于 AI 的代码编辑器，完全支持 MCP 协议。

### 配置文件位置

**macOS**: `~/Library/Application Support/Cursor/User/globalStorage/mcp_servers_config.json`
**Windows**: `%APPDATA%/Cursor/User/globalStorage/mcp_servers_config.json`
**Linux**: `~/.config/Cursor/User/globalStorage/mcp_servers_config.json`

### 方法 1：通过 Cursor 设置界面

1. 打开 Cursor 设置
2. 导航到 **MCP Servers**
3. 添加新服务器：
   - **名称**: `RegistryTools`
   - **命令**: `uvx`
   - **参数**: `["registry-tools"]`

### 方法 2：通过 fastmcp.json

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

### 方法 3：手动编辑配置文件

**基础配置**：
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

**开发模式配置**：
```json
{
  "mcpServers": {
    "RegistryTools-Dev": {
      "command": "python",
      "args": ["-m", "registrytools"],
      "cwd": "/path/to/RegistryTools",
      "env": {
        "PYTHONPATH": "/path/to/RegistryTools/src",
        "REGISTRYTOOLS_LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

---

## Continue.dev 配置

Continue.dev 是 VSCode 的 AI 编程助手扩展。

### 配置文件位置

`~/.continue/config.json` 或项目级 `.continue/config.json`

### 基础配置

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

### 使用环境变量

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

---

## Cline (VSCode扩展) 配置

Cline 是另一个流行的 VSCode AI 助手。

### 配置文件位置

项目级：`.cline/settings.json`
用户级：`~/.cline/settings.json`

### 基础配置

```json
{
  "mcpServers": {
    "RegistryTools": {
      "command": "uvx",
      "args": ["registry-tools"],
      "env": {
        "REGISTRYTOOLS_DATA_PATH": "~/.RegistryTools"
      }
    }
  }
}
```

### 使用 uv 运行（推荐用于开发）

```json
{
  "mcpServers": {
    "RegistryTools": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/RegistryTools",
        "run",
        "registry-tools"
      ]
    }
  }
}
```

---

## 通用配置模式

### 使用环境变量传递配置

所有 MCP 客户端都支持通过 `env` 字段传递环境变量：

```json
{
  "mcpServers": {
    "RegistryTools": {
      "command": "uvx",
      "args": ["registry-tools"],
      "env": {
        "REGISTRYTOOLS_DATA_PATH": "~/.RegistryTools",
        "REGISTRYTOOLS_LOG_LEVEL": "INFO",
        "REGISTRYTOOLS_TRANSPORT": "stdio"
      }
    }
  }
}
```

### 可用的环境变量

| 环境变量 | 默认值 | 描述 |
|---------|--------|------|
| `REGISTRYTOOLS_DATA_PATH` | `~/.RegistryTools` | 数据目录路径 |
| `REGISTRYTOOLS_LOG_LEVEL` | `INFO` | 日志级别（DEBUG/INFO/WARNING/ERROR） |
| `REGISTRYTOOLS_TRANSPORT` | `stdio` | 传输协议（stdio/http） |
| `REGISTRYTOOLS_ENABLE_AUTH` | `false` | 启用 RegistryTools 内置 API Key 认证（Phase 15） |

### 混合配置（CLI 参数 + 环境变量）

```json
{
  "mcpServers": {
    "RegistryTools": {
      "command": "uvx",
      "args": [
        "registry-tools",
        "--data-path",
        "/custom/path"
      ],
      "env": {
        "REGISTRYTOOLS_LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

**配置优先级**：环境变量 > CLI 参数 > 代码默认值

---

## 多服务器配置

### 同时使用本地和远程服务器

```json
{
  "mcpServers": {
    "RegistryTools-Local": {
      "command": "uvx",
      "args": ["registry-tools"],
      "env": {
        "REGISTRYTOOLS_LOG_LEVEL": "DEBUG"
      }
    },
    "RegistryTools-Remote": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

### 多实例配置（不同数据集）

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

## 配置验证

### 验证步骤

**1. 检查配置文件语法**：

```bash
# 验证 JSON 格式
cat ~/.claude/config.json | python -m json.tool
```

**2. 检查 RegistryTools 可用性**：

```bash
# 使用 uvx 测试
uvx registry-tools --version

# 使用 pip 安装版本测试
registry-tools --version

# 或直接运行 Python 模块
python -m registrytools --version
```

**3. 查看 MCP 服务器连接状态**：

在 IDE 中检查 MCP 服务器列表，RegistryTools 应显示为已连接。

**4. 测试工具调用**：

在 IDE 中输入测试请求：
```
搜索 GitHub 创建 PR 的工具
```

Claude 应该会调用 `search_tools` 工具并返回结果。

### 日志查看

| IDE | 日志位置 |
|-----|----------|
| **Claude Desktop** | `~/Library/Logs/Claude/` (macOS) |
| **Claude Code** | VSCode 输出面板 |
| **Cursor** | Help → Toggle Developer Tools |
| **Continue.dev** | VSCode 输出面板 |
| **Cline** | VSCode 输出面板 |

---

## 故障排除

### 问题 1: MCP 服务器未连接

**解决方案**:
1. 确认配置文件路径正确
2. 验证 `command` 和 `args` 是否正确
3. 检查 RegistryTools 是否已安装：
   ```bash
   uvx registry-tools --version
   ```
4. 查看 IDE 日志获取详细错误信息

### 问题 2: uvx 命令不可用

**解决方案**:
1. 安装 uv: `pip install uv`
2. 或使用 pip 安装: `pip install registry-tools`
3. 配置中使用完整 Python 路径

### 问题 3: 工具调用无响应

**解决方案**:
1. 检查数据目录权限：
   ```bash
   mkdir -p ~/.RegistryTools
   chmod 755 ~/.RegistryTools
   ```
2. 查看日志: 设置 `REGISTRYTOOLS_LOG_LEVEL=DEBUG`
3. 确认 RegistryTools 进程正在运行

### 问题 4: HTTP 连接失败

**解决方案**:
1. 确认 HTTP 服务器正在运行：
   ```bash
   registry-tools --transport http --port 8000
   ```
2. 检查防火墙设置
3. 验证 URL 格式正确（包含 `/mcp` 路径）

---

## 高级配置

### 使用自定义 Python 解释器

```json
{
  "mcpServers": {
    "RegistryTools": {
      "command": "/custom/path/python3.11",
      "args": ["-m", "registrytools"]
    }
  }
}
```

### 使用虚拟环境

```json
{
  "mcpServers": {
    "RegistryTools": {
      "command": "/path/to/venv/bin/python",
      "args": ["-m", "registrytools"],
      "env": {
        "PYTHONPATH": "/path/to/RegistryTools/src"
      }
    }
  }
}
```

**Windows 虚拟环境**：
```json
{
  "mcpServers": {
    "RegistryTools": {
      "command": "C:\\path\\to\\venv\\Scripts\\python.exe",
      "args": ["-m", "registrytools"]
    }
  }
}
```

### 使用 conda 环境

```json
{
  "mcpServers": {
    "RegistryTools": {
      "command": "/opt/anaconda3/envs/registrytools/bin/python",
      "args": ["-m", "registrytools"]
    }
  }
}
```

### Docker 容器部署

**启动容器**：
```bash
docker run -d \
  --name registrytools \
  -p 8000:8000 \
  -v ~/.RegistryTools:/data \
  registrytools:latest \
  registry-tools --transport http --host 0.0.0.0 --port 8000
```

**IDE 连接到容器**：
```json
{
  "mcpServers": {
    "RegistryTools-Docker": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

---

## 开发模式配置

### 源码开发模式

用于本地源码开发，自动重载：

```json
{
  "mcpServers": {
    "RegistryTools-Dev": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/RegistryTools",
        "run",
        "python",
        "-m",
        "registrytools"
      ],
      "cwd": "/path/to/RegistryTools",
      "env": {
        "PYTHONPATH": "/path/to/RegistryTools/src",
        "REGISTRYTOOLS_LOG_LEVEL": "DEBUG",
        "REGISTRYTOOLS_DATA_PATH": "./.RegistryTools-dev"
      }
    }
  }
}
```

---

## .claude/ 目录结构最佳实践

### 项目级配置

```
your-project/
├── .claude/
│   ├── config.json           # MCP 服务器配置
│   ├── prompts/              # 项目级系统提示
│   │   └── registry-tools.md
│   └── output-styles/        # 输出样式配置
│       └── technical-docs.md
├── fastmcp.json             # FastMCP 配置
└── ...
```

### .claude/config.json 示例

```json
{
  "mcpServers": {
    "RegistryTools": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/RegistryTools",
        "run",
        "registry-tools"
      ],
      "env": {
        "REGISTRYTOOLS_DATA_PATH": "./.RegistryTools-project"
      }
    }
  },
  "systemPrompt": {
    "append": "使用 RegistryTools 搜索和发现 MCP 工具"
  }
}
```

---

## 相关资源

- [安装指南](INSTALLATION.md) - 详细安装说明
- [用户指南](USER_GUIDE.md) - 工具使用说明
- [架构设计](ARCHITECTURE.md) - 系统架构文档
- [API 文档](API.md) - MCP 工具 API 参考

---

**维护者**: Maric
**文档版本**: v1.0
