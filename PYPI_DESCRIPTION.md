# RegistryTools v0.2.1 - MCP Tool Registry Server

一个通用的 MCP 工具注册服务器，支持智能搜索、冷热分离和多种存储后端。

---

## 🎉 v0.2.1 更新说明

### 主要更新

**1. Embedding 搜索引擎优化 🚀**

解决了 v0.2.0 中启动时立即加载模型和 GPU 资源的问题：

- ✅ **延迟加载**: 模型仅在首次搜索时加载，启动时间从 3 秒降至 0.5 秒
- ✅ **智能设备选择**: 新增 `REGISTRYTOOLS_DEVICE` 环境变量（cpu/gpu:0/gpu:1/auto）
- ✅ **优雅降级**: GPU 不可用时自动降级到 CPU

**2. 存储后端重构 💾**

新增 SQLite 存储支持，性能提升显著：

- JSON 存储（默认）: 适用于少于 1000 工具
- SQLite 存储: 适用于大规模工具集，性能提升 76%

**3. 文档完善 📚**

- INSTALLATION.md 新增搜索方法配置
- BEST_PRACTICES.md 新增环境变量说明
- 新增 STORAGE.md 存储选择指南

---

## 安装

```bash
# 基础版本
pip install registry-tools==0.2.1

# 含 Embedding 支持
pip install registry-tools[embedding]==0.2.1
```

---

## 核心特性

### 🔍 智能搜索

支持三种搜索算法：

| 方法 | 准确率 | 速度 | 适用场景 |
|------|--------|------|----------|
| regex | 高 | 最快 | 精确匹配工具名 |
| bm25 | 高 | 快 | 自然语言查询 |
| embedding | 最高 | 慢 | 语义搜索 |

### 🌡️ 冷热分离

根据使用频率自动分类工具，优化搜索性能：

- **热工具**: 使用 ≥10 次，启动时预加载
- **温工具**: 使用 3-9 次，按需加载并缓存
- **冷工具**: 使用 <3 次，延迟加载

### 💾 灵活存储

根据规模选择存储后端：

```bash
# JSON 存储（< 1000 工具）
export REGISTRYTOOLS_STORAGE_BACKEND=json

# SQLite 存储（> 1000 工具）
export REGISTRYTOOLS_STORAGE_BACKEND=sqlite
```

---

## 配置示例

### 基础使用

```bash
# 启动服务器
registry-tools

# 指定数据目录
registry-tools --data-path /path/to/data
```

### Embedding 搜索 + GPU 加速

```bash
# 安装依赖
pip install registry-tools[embedding]

# 配置使用
export REGISTRYTOOLS_SEARCH_METHOD=embedding
export REGISTRYTOOLS_DEVICE=gpu:0

registry-tools
```

### HTTP 模式 + API Key 认证

```bash
registry-tools \
  --transport http \
  --host 0.0.0.0 \
  --port 8000 \
  --enable-auth
```

---

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `REGISTRYTOOLS_SEARCH_METHOD` | bm25 | 搜索方法：regex/bm25/embedding |
| `REGISTRYTOOLS_DEVICE` | cpu | Embedding 设备：cpu/gpu:0/gpu:1/auto |
| `REGISTRYTOOLS_STORAGE_BACKEND` | json | 存储后端：json/sqlite |
| `REGISTRYTOOLS_LOG_LEVEL` | INFO | 日志级别：DEBUG/INFO/WARNING/ERROR |
| `REGISTRYTOOLS_ENABLE_AUTH` | false | 启用 API Key 认证 |

---

## Claude Desktop 配置

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

---

## 文档链接

- [配置指南](https://github.com/GeerMrc/RegistryTools/blob/master/docs/CONFIGURATION.md)
- [安装指南](https://github.com/GeerMrc/RegistryTools/blob/master/docs/INSTALLATION.md)
- [用户指南](https://github.com/GeerMrc/RegistryTools/blob/master/docs/USER_GUIDE.md)
- [存储选择](https://github.com/GeerMrc/RegistryTools/blob/master/docs/STORAGE.md)

---

## 许可证

MIT License - 详见 [LICENSE](https://github.com/GeerMrc/RegistryTools/blob/master/LICENSE)

---

## 质量指标

- ✅ 453 个测试全部通过
- ✅ 代码覆盖率: 84%
- ✅ 支持 Python 3.10+
