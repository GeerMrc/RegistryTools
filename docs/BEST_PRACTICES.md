# RegistryTools 最佳实践

**版本**: v0.2.0
**更新日期**: 2026-01-10
**项目**: RegistryTools - MCP Tool Registry Server

---

## ⚠️ PyPI 发布状态

> **注意**: RegistryTools 尚未发布到 PyPI，当前仅支持本地开发环境安装。
> 详见 [安装指南 - PyPI 发布状态](INSTALLATION.md#pypi-发布状态)。

---

本文档提供使用 RegistryTools 的最佳实践建议，帮助您充分发挥工具注册表的潜力。

---

## 目录

- [工具命名规范](#工具命名规范)
- [搜索方法选择](#搜索方法选择)
- [冷热工具优化](#冷热工具优化)
- [API Key 权限管理](#api-key-权限管理)
- [性能优化技巧](#性能优化技巧)
- [部署建议](#部署建议)
- [常见使用模式](#常见使用模式)

---

## 工具命名规范

### 推荐格式

使用 `<provider>.<action>_<resource>` 格式命名工具：

| 部分 | 描述 | 示例 |
|------|------|------|
| `provider` | 服务提供商 | `github`, `gitlab`, `aws`, `slack` |
| `action` | 执行动作 | `create`, `get`, `list`, `update`, `delete` |
| `resource` | 操作资源 | `pull_request`, `issue`, `file`, `user` |

### 正确示例

```
github.create_pull_request        # GitHub - 创建 PR
gitlab.merge_request              # GitLab - 合并请求
aws.s3.upload_file                # AWS S3 - 上传文件
slack.send_message                # Slack - 发送消息
gdrive.list_files                 # Google Drive - 列出文件
database.query                    # 数据库 - 查询
```

### 错误示例

```
create_pr                         # ❌ 缺少 provider
github_pr                         # ❌ 使用下划线分隔
GitHubCreatePullRequest           # ❌ 使用驼峰命名
create-github-pull-request        # ❌ 使用连字符
github.CreatePullRequest          # ❌ 大小写不一致
```

### 命名原则

1. **使用小写字母**: 全部使用小写，避免大小写混淆
2. **使用点号分隔**: 分隔 provider 和 action
3. **使用下划线**: 分隔 action 和 resource
4. **使用动词**: action 应该是动词（create, get, list 等）
5. **保持简洁**: 避免过长的名称
6. **使用复数**: resource 尽量使用复数形式（files, users）

---

## 搜索方法选择

### 方法对比

| 方法 | 适用场景 | 准确率 | 速度 | 示例 |
|------|----------|--------|------|------|
| **regex** | 已知工具名称 | 高 | 最快 | `github.*pull` |
| **bm25** | 关键词搜索 | 高 | 快 | `github PR` |
| **embedding** | 语义搜索 | 高 | 慢 | `如何创建代码合并请求` |

### 使用 Regex 搜索

**适用场景**:
- 已知工具的确切名称或部分名称
- 需要精确匹配工具
- 搜索速度要求高

**示例**:

```python
# 精确查找 GitHub PR 相关工具
search_tools("github.*pull", "regex", 10)

# 查找所有 create 开头的工具
search_tools(".*\\.create_", "regex", 20)

# 查找特定提供商的所有工具
search_tools("github\\..*", "regex", 50)
```

**Regex 技巧**:
- 使用 `.*` 匹配任意字符
- 使用 `\\.` 匹配点号
- 使用 `^` 和 `$` 匹配开头和结尾

### 使用 BM25 搜索

**适用场景**:
- 自然语言查询
- 不确定确切工具名称
- 需要语义匹配

**示例**:

```python
# 自然语言查询
search_tools("如何在 GitHub 上创建 PR", "bm25", 5)
search_tools("upload file to S3 bucket", "bm25", 5)
search_tools("send message to slack channel", "bm25", 5)

# 关键词搜索
search_tools("github pull request create", "bm25", 5)
search_tools("aws s3 upload", "bm25", 5)
```

### 搜索优化建议

1. **从 BM25 开始**: 除非确定工具名称，否则优先使用 BM25
2. **调整 limit 参数**: 根据需求调整返回结果数量
3. **使用具体关键词**: 避免过于泛泛的查询
4. **结合类别筛选**: 先用 `list_tools_by_category` 缩小范围

---

## 冷热工具优化

### 温度级别影响

| 温度级别 | 使用频率 | 加载方式 | 搜索性能 |
|---------|---------|----------|----------|
| **HOT** | ≥ 10 次 | 启动时预加载 | 最快 |
| **WARM** | 3-9 次 | 按需加载并缓存 | 快 |
| **COLD** | < 3 次 | 延迟加载 | 标准 |

### 优化策略

#### 1. 预热热工具

对于高频使用的工具，可以通过多次调用将其升级为热工具：

```python
# 预热关键工具（调用 10 次以上）
for _ in range(10):
    get_tool_definition("github.create_pull_request")
```

#### 2. 合理设置阈值

根据实际使用情况调整冷热阈值（参见 [配置指南](CONFIGURATION.md#冷热工具分离配置)）：

```python
# 高频使用场景（工具集 < 100）
HOT_TOOL_THRESHOLD = 1      # 使用 1 次即为热工具
WARM_TOOL_THRESHOLD = 1

# 低频使用场景（大型工具集）
HOT_TOOL_THRESHOLD = 20     # 使用 20 次才为热工具
WARM_TOOL_THRESHOLD = 5
```

#### 3. 监控工具温度

定期检查工具温度分布：

```python
# 获取统计信息
import requests
response = requests.get(
    "http://localhost:8000/mcp/resources/registry://stats",
    headers={"X-API-Key": "rtk_xxx..."}
)
stats = response.json()

print(f"热工具数: {stats.get('hot_tools', 0)}")
print(f"温工具数: {stats.get('warm_tools', 0)}")
print(f"冷工具数: {stats.get('cold_tools', 0)}")
```

---

## API Key 权限管理

### 权限级别

| 权限 | 描述 | 允许操作 | 使用场景 |
|------|------|----------|----------|
| **read** | 只读 | 搜索、查看工具定义 | 生产环境客户端 |
| **write** | 读写 | 上述 + 注册工具 | 开发环境客户端 |
| **admin** | 管理员 | 所有操作 + API Key 管理 | 运维人员 |

### 最佳实践

#### 1. 最小权限原则

始终授予完成任务所需的最小权限：

```bash
# 生产环境：只读权限
registry-tools api-key create "Production Client" --permission read

# 开发环境：读写权限
registry-tools api-key create "Development Client" --permission write

# 运维人员：管理员权限
registry-tools api-key create "Admin Key" --permission admin
```

#### 2. 设置过期时间

为临时使用场景设置过期时间：

```bash
# 临时测试 Key（1 小时后过期）
registry-tools api-key create "Temp Test Key" --expires-in 3600 --permission read

# 短期项目 Key（7 天后过期）
registry-tools api-key create "Project Key" --expires-in 604800 --permission write
```

#### 3. 使用所有者标识

为不同团队或用户创建专属 Key：

```bash
# 团队 A 的 Key
registry-tools api-key create "Team A Key" --owner team-a@example.com --permission read

# 团队 B 的 Key
registry-tools api-key create "Team B Key" --owner team-b@example.com --permission read
```

#### 4. 定期轮换 Key

建议定期更换 API Key（如每 90 天）：

```bash
# 1. 创建新 Key
registry-tools api-key create "New Key" --permission read

# 2. 更新客户端配置

# 3. 验证新 Key 工作正常

# 4. 删除旧 Key
registry-tools api-key delete <old-key-id>
```

#### 5. 定期清理

定期检查并删除不再使用的 Key：

```bash
# 列出所有 Key
registry-tools api-key list

# 检查使用情况，删除长期未使用的 Key
registry-tools api-key delete <unused-key-id>
```

---

## 性能优化技巧

### 1. 减少搜索延迟

- **使用 regex 搜索**: 对于已知工具名称，使用 regex 比 bm25 更快
- **限制结果数量**: 使用较小的 `limit` 值减少响应时间
- **预加载热工具**: 通过调用预热关键工具

### 2. 降低内存占用

- **限制热工具数量**: 调整 `MAX_HOT_TOOLS_PRELOAD` 配置
- **禁用降级机制**: 对于稳定环境，可以禁用降级保持工具温度稳定
- **按需加载**: 使用 COLD 工具的 `defer_loading` 机制

### 3. 优化网络请求

- **使用 HTTP Keep-Alive**: 复用 TCP 连接
- **批量操作**: 尽可能批量注册或查询工具
- **本地缓存**: 客户端端缓存常用工具定义

### 4. 配置调优示例

```python
# 低内存环境
MAX_HOT_TOOLS_PRELOAD = 20     # 减少预加载数量
ENABLE_DOWNGRADE = True         # 启用降级

# 高性能环境
MAX_HOT_TOOLS_PRELOAD = 200    # 增加预加载数量
ENABLE_DOWNGRADE = False        # 禁用降级
HOT_TOOL_THRESHOLD = 5          # 降低热工具阈值
```

---

## 部署建议

### 开发环境

```bash
# STDIO 模式，本地调试
export REGISTRYTOOLS_LOG_LEVEL=DEBUG
registry-tools
```

### 测试环境

```bash
# HTTP 模式，团队共享
registry-tools \
  --transport http \
  --host 0.0.0.0 \
  --port 8000 \
  --enable-auth

# 创建测试 Key
registry-tools api-key create "Test Client" --permission write --expires-in 86400
```

### 生产环境

```bash
# 使用 systemd 管理
# /etc/systemd/system/registrytools.service

[Unit]
Description=RegistryTools MCP Server
After=network.target

[Service]
Type=simple
User=registrytools
Group=registrytools
WorkingDirectory=/var/lib/registrytools
Environment="REGISTRYTOOLS_DATA_PATH=/var/lib/registrytools"
Environment="REGISTRYTOOLS_TRANSPORT=http"
Environment="REGISTRYTOOLS_ENABLE_AUTH=true"
Environment="REGISTRYTOOLS_LOG_LEVEL=INFO"
ExecStart=/usr/local/bin/registry-tools --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Docker 部署

```dockerfile
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
    restart: unless-stopped

volumes:
  registrytools-data:
```

---

## 常见使用模式

### 模式 1: 工具发现流程

```python
# 1. 搜索相关工具
tools = search_tools("github create pull request", "bm25", 5)

# 2. 获取工具定义
for tool in tools:
    definition = get_tool_definition(tool["tool_name"])
    # 分析工具定义...

# 3. 选择最佳工具
best_tool = tools[0]["tool_name"]

# 4. 使用工具（更新使用频率）
update_usage(best_tool)
```

### 模式 2: 类别浏览

```python
# 1. 列出所有类别
categories = list_tools_by_category("all")

# 2. 浏览特定类别
github_tools = list_tools_by_category("github", 20)

# 3. 按使用频率排序
sorted_tools = sorted(
    github_tools["tools"],
    key=lambda t: t.get("use_frequency", 0),
    reverse=True
)
```

### 模式 3: 动态工具注册

```python
# 1. 发现新工具
new_tool = {
    "name": "my.custom.tool",
    "description": "A custom tool for specific purpose",
    "category": "custom",
    "tags": ["custom", "utility"]
}

# 2. 注册工具
result = register_tool(
    name=new_tool["name"],
    description=new_tool["description"],
    category=new_tool["category"],
    tags=new_tool["tags"]
)

# 3. 验证注册
definition = get_tool_definition(new_tool["name"])
```

---

## 相关文档

- [配置指南](CONFIGURATION.md) - 完整配置说明
- [用户指南](USER_GUIDE.md) - 快速开始和基本使用
- [API 文档](API.md) - 完整的 API 参考
- [故障排除](TROUBLESHOOTING.md) - 常见问题和解决方案
- [架构设计](ARCHITECTURE.md) - 系统架构和设计决策

---

**维护者**: Maric
**文档版本**: v0.2.0
