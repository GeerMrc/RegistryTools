# RegistryTools 故障排除

**版本**: v0.1.1
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

本文档提供常见问题的诊断和解决方案。

---

## 目录

- [快速诊断](#快速诊断)
- [安装问题](#安装问题)
- [配置问题](#配置问题)
- [MCP 连接问题](#mcp-连接问题)
- [性能问题](#性能问题)
- [认证问题](#认证问题)
- [搜索问题](#搜索问题)
- [数据问题](#数据问题)

---

## 快速诊断

### 健康检查

```bash
# 1. 检查版本
registry-tools --version

# 2. 检查数据目录
ls -la ~/.RegistryTools/

# 3. 测试 STDIO 模式
echo '{"jsonrpc":"2.0","id":1,"method":"ping"}' | registry-tools

# 4. 测试 HTTP 模式
curl http://localhost:8000/mcp
```

### 启用调试日志

```bash
# 启用 DEBUG 日志
export REGISTRYTOOLS_LOG_LEVEL=DEBUG
registry-tools

# 查看详细日志
registry-tools 2>&1 | tee debug.log
```

---

## 安装问题

### 问题: uvx 命令无法连接

**症状**:
```
Error: Failed to connect to MCP server
```

**原因**: `uvx registry-tools` 需要包已发布到 PyPI。

**解决方案**:

**方案 1: 使用本地开发环境**
```bash
# 从源码安装
git clone https://github.com/GeerMrc/RegistryTools.git
cd RegistryTools
pip install -e .

# 使用 registry-tools 命令
registry-tools --version
```

**方案 2: 配置中使用 registry-tools 命令**
```json
{
  "mcpServers": {
    "RegistryTools": {
      "command": "registry-tools"
    }
  }
}
```

### 问题: 安装后命令不可用

**症状**:
```
bash: registry-tools: command not found
```

**原因**: Python Scripts 目录不在 PATH 中。

**解决方案**:

**Windows**:
```bash
set PATH=%PATH%;%APPDATA%\Python\Scripts
```

**Linux/Mac**:
```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
export PATH="$HOME/.local/bin:$PATH"

# 重新加载配置
source ~/.bashrc
```

### 问题: 依赖安装失败

**症状**:
```
ERROR: Could not find a version that satisfies the requirement ...
```

**解决方案**:
```bash
# 更新 pip
pip install --upgrade pip

# 使用 uv 安装（更快）
pip install uv
uv pip install -e .

# 或使用国内镜像
pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 配置问题

### 问题: 环境变量不生效

**症状**: 环境变量设置后没有效果。

**原因**: 环境变量设置位置不正确。

**解决方案**:

**检查环境变量**:
```bash
# Linux/Mac
echo $REGISTRYTOOLS_DATA_PATH
echo $REGISTRYTOOLS_LOG_LEVEL

# Windows
echo %REGISTRYTOOLS_DATA_PATH%
echo %REGISTRYTOOLS_LOG_LEVEL%
```

**正确设置方式**:
```bash
# 临时设置（当前会话）
export REGISTRYTOOLS_DATA_PATH=/custom/path
registry-tools

# 永久设置（添加到 ~/.bashrc 或 ~/.zshrc）
echo 'export REGISTRYTOOLS_DATA_PATH=/custom/path' >> ~/.bashrc
source ~/.bashrc
```

**在 Claude Desktop 中设置**:
```json
{
  "mcpServers": {
    "RegistryTools": {
      "command": "registry-tools",
      "env": {
        "REGISTRYTOOLS_DATA_PATH": "~/.RegistryTools",
        "REGISTRYTOOLS_LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

### 问题: 数据目录权限错误

**症状**:
```
PermissionError: [Errno 13] Permission denied: '/path/to/data'
```

**解决方案**:
```bash
# 检查目录权限
ls -la ~/.RegistryTools/

# 修复权限
chmod 755 ~/.RegistryTools/
chmod 644 ~/.RegistryTools/tools.json

# 或使用自定义目录
export REGISTRYTOOLS_DATA_PATH=$HOME/registrytools_data
registry-tools
```

### 问题: 日志级别 CLI 参数无效

**症状**:
```
registry-tools --log-level DEBUG
# 错误: unrecognized arguments: --log-level
```

**原因**: 日志级别仅支持通过环境变量配置。

**解决方案**:
```bash
# 使用环境变量
export REGISTRYTOOLS_LOG_LEVEL=DEBUG
registry-tools
```

---

## MCP 连接问题

### 问题: Claude Desktop 无法连接

**症状**: Claude Desktop 中看不到 RegistryTools 工具。

**诊断步骤**:

**1. 检查配置文件位置**:
```
macOS:   ~/Library/Application Support/Claude/claude_desktop_config.json
Windows: %APPDATA%/Claude/claude_desktop_config.json
Linux:   ~/.config/Claude/claude_desktop_config.json
```

**2. 验证配置格式**:
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

**3. 测试命令**:
```bash
# 手动运行命令测试
registry-tools --data-path ~/.RegistryTools
```

**4. 检查 Claude Desktop 日志**:
```
macOS:   ~/Library/Logs/Claude/
Windows: %APPDATA%/Claude/logs/
Linux:   ~/.config/Claude/logs/
```

### 问题: HTTP 模式连接失败

**症状**:
```
Connection refused: http://localhost:8000/mcp
```

**解决方案**:

**1. 确认服务正在运行**:
```bash
# 检查端口
netstat -an | grep 8000
# 或
lsof -i :8000

# 测试连接
curl http://localhost:8000/mcp
```

**2. 检查防火墙**:
```bash
# Linux (ufw)
sudo ufw allow 8000/tcp

# Linux (firewalld)
sudo firewall-cmd --add-port=8000/tcp --permanent
sudo firewall-cmd --reload

# macOS
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/local/bin/registry-tools
```

**3. 检查主机绑定**:
```bash
# 使用 0.0.0.0 而非 127.0.0.1
registry-tools --transport http --host 0.0.0.0 --port 8000
```

### 问题: Streamable HTTP 超时

**症状**: HTTP 连接频繁超时。

**解决方案**:

**1. 增加超时时间**（客户端配置）:
```json
{
  "mcpServers": {
    "RegistryTools": {
      "url": "http://localhost:8000/mcp",
      "timeout": 30000
    }
  }
}
```

**2. 检查网络延迟**:
```bash
# 测试网络延迟
ping localhost
curl -w "@-" -o /dev/null -s "http://localhost:8000/mcp" <<EOF
    time_namelookup:  %{time_namelookup}\n
       time_connect:  %{time_connect}\n
    time_appconnect:  %{time_appconnect}\n
   time_pretransfer:  %{time_pretransfer}\n
      time_redirect:  %{time_redirect}\n
 time_starttransfer:  %{time_starttransfer}\n
                    ----------\n
         time_total:  %{time_total}\n
EOF
```

---

## 性能问题

### 问题: 搜索响应慢

**症状**: 搜索操作耗时超过 1 秒。

**诊断**:
```bash
# 启用 DEBUG 日志
export REGISTRYTOOLS_LOG_LEVEL=DEBUG
registry-tools 2>&1 | grep "Search"
```

**解决方案**:

**1. 使用 regex 搜索**:
```python
# 更快的精确搜索
search_tools("github.*pull", "regex", 10)
```

**2. 限制结果数量**:
```python
# 减少返回结果
search_tools("github", "bm25", 3)
```

**3. 预加载热工具**:
```python
# 预热关键工具
for _ in range(10):
    get_tool_definition("github.create_pull_request")
```

**4. 调整配置**:
```python
# 减少预加载数量
MAX_HOT_TOOLS_PRELOAD = 50

# 禁用降级
ENABLE_DOWNGRADE = False
```

### 问题: 内存占用过高

**症状**: 进程内存占用超过 500MB。

**解决方案**:

**1. 检查工具数量**:
```python
# 获取统计信息
import requests
response = requests.get("http://localhost:8000/mcp/resources/registry://stats")
print(response.json())
```

**2. 减少预加载**:
```python
MAX_HOT_TOOLS_PRELOAD = 20
```

**3. 启用降级**:
```python
ENABLE_DOWNGRADE = True
HOT_TOOL_INACTIVE_DAYS = 14
WARM_TOOL_INACTIVE_DAYS = 30
```

### 问题: 启动时间长

**症状**: 服务启动耗时超过 5 秒。

**诊断**:
```bash
# 测量启动时间
time registry-tools --version
```

**解决方案**:

**1. 检查数据文件大小**:
```bash
ls -lh ~/.RegistryTools/tools.json
```

**2. 优化工具数量**:
```python
# 移除不必要的工具
# 或使用类别筛选
```

**3. 使用 SQLite 存储**（可能更快）:
```python
from registrytools.server import create_server_with_sqlite
app = create_server_with_sqlite(Path("~/.RegistryTools"))
```

---

## 认证问题

### 问题: API Key 认证失败

**症状**:
```
401 Unauthorized: Invalid API Key
```

**诊断**:

**1. 验证 API Key 格式**:
```bash
# 正确格式
rtk_<64个十六进制字符>

# 示例
rtk_a1b2c3d4e5f6789012345678901234567890123456789012345678901234
```

**2. 检查 API Key 是否存在**:
```bash
registry-tools api-key list
```

**3. 测试 API Key**:
```bash
curl -X POST http://localhost:8000/mcp/tools/search_tools \
  -H "Content-Type: application/json" \
  -H "X-API-Key: rtk_xxx..." \
  -d '{"query": "github"}'
```

**解决方案**:

**1. 重新创建 API Key**:
```bash
registry-tools api-key create "New Key" --permission read
```

**2. 检查权限级别**:
```bash
# 确认权限足够
registry-tools api-key list
# 需要 write 权限才能注册工具
```

### 问题: API Key 已过期

**症状**:
```
401 Unauthorized: API Key expired
```

**解决方案**:

**1. 创建新的 API Key**:
```bash
registry-tools api-key create "New Key" --expires-in 2592000  # 30 天
```

**2. 删除过期 Key**:
```bash
registry-tools api-key delete <expired-key-id>
```

### 问题: 权限不足

**症状**:
```
403 Forbidden: Insufficient permission
```

**解决方案**:

**1. 检查所需权限**:
- `search_tools`: read 权限
- `get_tool_definition`: read 权限
- `register_tool`: write 权限

**2. 升级权限**:
```bash
# 删除旧 Key
registry-tools api-key delete <key-id>

# 创建新 Key（更高权限）
registry-tools api-key create "Write Key" --permission write
```

---

## 搜索问题

### 问题: 搜索结果为空

**症状**:
```python
search_tools("github", "bm25", 5)
# 返回: []
```

**诊断**:

**1. 检查工具是否已注册**:
```python
list_tools_by_category("all")
```

**2. 检查搜索参数**:
```python
# 尝试不同的查询
search_tools("git", "bm25", 20)  # 更宽泛
search_tools("github\\..*", "regex", 50)  # 正则表达式
```

**3. 启用调试日志**:
```bash
export REGISTRYTOOLS_LOG_LEVEL=DEBUG
registry-tools 2>&1 | grep "Search"
```

**解决方案**:

**1. 注册默认工具**:
```python
# 首次启动会自动加载默认工具
# 或手动注册
register_tool(
    name="github.create_pull_request",
    description="Create a pull request in a GitHub repository",
    category="github"
)
```

**2. 使用更具体的关键词**:
```python
# ❌ 太泛泛
search_tools("tool", "bm25", 5)

# ✅ 更具体
search_tools("github pull request", "bm25", 5)
```

### 问题: 搜索方法无效

**症状**:
```
ValueError: 无效的搜索方法: xxx
```

**原因**: 搜索方法拼写错误或使用了不支持的方法。

**解决方案**:

**使用正确的搜索方法**:
```python
# ✅ 正确
search_tools("github", "regex", 5)
search_tools("github", "bm25", 5)

# ❌ 错误
search_tools("github", "regexx", 5)  # 拼写错误
search_tools("github", "embedding", 5)  # 暂不支持
```

---

## 数据问题

### 问题: 数据文件损坏

**症状**:
```
JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

**诊断**:
```bash
# 检查文件
cat ~/.RegistryTools/tools.json
```

**解决方案**:

**1. 从备份恢复**:
```bash
# 如果有备份
cp ~/.RegistryTools/tools.json.backup ~/.RegistryTools/tools.json
```

**2. 重新初始化**:
```bash
# 删除损坏的数据
rm ~/.RegistryTools/tools.json

# 重新启动（会自动创建）
registry-tools
```

**3. 使用 SQLite 存储**（更健壮）:
```python
from registrytools.server import create_server_with_sqlite
app = create_server_with_sqlite(Path("~/.RegistryTools"))
```

### 问题: 工具定义不一致

**症状**: 搜索返回的工具定义与实际不符。

**解决方案**:

**1. 重新加载工具**:
```bash
# 删除 tools.json
rm ~/.RegistryTools/tools.json

# 重启服务
registry-tools
```

**2. 验证工具定义**:
```python
# 获取工具定义
definition = get_tool_definition("github.create_pull_request")

# 验证字段
import json
tool = json.loads(definition)
assert tool["name"] == "github.create_pull_request"
assert tool["category"] == "github"
```

---

## 获取帮助

如果以上方案都无法解决问题，请：

1. **启用调试日志**:
   ```bash
   export REGISTRYTOOLS_LOG_LEVEL=DEBUG
   registry-tools 2>&1 | tee debug.log
   ```

2. **收集系统信息**:
   ```bash
   # Python 版本
   python --version

   # pip 版本
   pip --version

   # 已安装的包
   pip list | grep registry

   # 操作系统
   uname -a  # Linux/Mac
   ver       # Windows
   ```

3. **查看 GitHub Issues**:
   - [RegistryTools Issues](https://github.com/GeerMrc/RegistryTools/issues)

4. **提交新 Issue**:
   - 描述问题
   - 提供错误日志
   - 提供系统信息
   - 提供复现步骤

---

## 相关文档

- [配置指南](CONFIGURATION.md) - 完整配置说明
- [用户指南](USER_GUIDE.md) - 快速开始和基本使用
- [最佳实践](BEST_PRACTICES.md) - 优化建议和使用技巧
- [API 文档](API.md) - 完整的 API 参考

---

**维护者**: Maric
**文档版本**: v0.1.0
