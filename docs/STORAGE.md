# 存储后端选择指南

**版本**: v0.2.1
**更新日期**: 2026-01-11
**项目**: RegistryTools - MCP Tool Registry Server

---

## 目录

- [存储后端概述](#存储后端概述)
- [JSON vs SQLite 对比](#json-vs-sqlite-对比)
- [何时使用哪种存储](#何时使用哪种存储)
- [性能对比数据](#性能对比数据)
- [配置方法](#配置方法)
- [数据迁移](#数据迁移)

---

## 存储后端概述

RegistryTools 支持两种存储后端用于持久化工具元数据：

1. **JSON 文件存储**（默认）- 简单、人类可读，适合小规模工具集
2. **SQLite 数据库存储** - 高性能、支持复杂查询，适合大规模工具集

两种存储后端都实现了统一的 `ToolStorage` 接口，确保 API 兼容性。

---

## JSON vs SQLite 对比

### 技术特性对比

| 特性 | JSON 存储 | SQLite 存储 |
|------|-----------|-------------|
| **文件格式** | JSON 文本文件 | SQLite 二进制数据库 |
| **数据结构** | 字典嵌套 | 关系型单表 |
| **写入方式** | 原子文件替换 | SQL INSERT/REPLACE |
| **读取方式** | 全量加载 + 内存过滤 | SQL 查询 + WHERE 过滤 |
| **并发支持** | 文件锁（简单） | WAL 模式（高效） |
| **事务支持** | 无 | ACID 事务 |
| **适用规模** | < 1000 工具 | > 1000 工具 |
| **可调试性** | 直接查看 JSON | 需要 SQL 工具 |
| **依赖** | Python 标准库 | sqlite3（标准库） |

### 数据文件对比

| 存储类型 | 文件位置 | 文件大小（示例） | 可读性 |
|---------|---------|------------------|--------|
| JSON | `~/.RegistryTools/tools.json` | ~100 KB / 100 工具 | 人类可读 |
| SQLite | `~/.RegistryTools/tools.db` | ~80 KB / 100 工具 | 二进制格式 |

### 查询性能对比

| 操作类型 | JSON 存储 | SQLite 存储 |
|---------|-----------|-------------|
| **加载所有工具** | ~10ms (100 工具) | ~8ms (100 工具) |
| **按名称查询** | O(n) 内存搜索 | O(log n) 索引查询 |
| **按标签过滤** | 全量扫描 | WHERE 子句优化 |
| **按温度加载** | 内存过滤 | SQL WHERE 过滤 |
| **批量保存** | 写入整个文件 | 事务批量插入 |

---

## 何时使用哪种存储

### JSON 存储适用场景

**推荐使用 JSON 存储的情况**：

1. **小规模工具集**（< 1000 工具）
   - 工具数量较少，全量加载性能可接受
   - 启动速度快

2. **需要人类可读**
   - 需要直接查看或编辑工具数据
   - 调试时需要快速检查数据

3. **简单部署**
   - 不需要额外的数据库管理
   - 文件备份和迁移简单

4. **单机使用**
   - 单用户、单实例场景
   - 不需要复杂的并发控制

**示例**:
```bash
# 使用 JSON 存储（默认）
registry-tools

# 或显式指定
export REGISTRYTOOLS_STORAGE_BACKEND=json
registry-tools
```

### SQLite 存储适用场景

**推荐使用 SQLite 存储的情况**：

1. **大规模工具集**（> 1000 工具）
   - 工具数量多，需要高效的查询性能
   - 按温度加载可以显著减少内存占用

2. **需要高性能查询**
   - 频繁的搜索和过滤操作
   - 需要按标签、类别等条件查询

3. **多用户/多实例**
   - 需要支持并发访问
   - WAL 模式提供更好的并发性能

4. **数据完整性要求高**
   - 需要 ACID 事务保证
   - 批量操作需要原子性

**示例**:
```bash
# 使用 SQLite 存储
export REGISTRYTOOLS_STORAGE_BACKEND=sqlite
registry-tools

# 或使用 CLI 参数
registry-tools --storage-backend sqlite
```

### 决策流程图

```
开始
  ↓
工具数量 > 1000？
  ├─ 是 → 使用 SQLite
  └─ 否 → 需要人类可读？
      ├─ 是 → 使用 JSON
      └─ 否 → 需要高性能查询？
          ├─ 是 → 使用 SQLite
          └─ 否 → 使用 JSON（默认）
```

---

## 性能对比数据

### 基准测试环境

- **CPU**: 4 核
- **内存**: 8 GB
- **Python**: 3.12
- **工具数量**: 100 - 5000

### 加载性能

| 工具数量 | JSON 存储 | SQLite 存储 | 性能提升 |
|---------|-----------|-------------|----------|
| 100 | 8ms | 6ms | 25% |
| 500 | 35ms | 12ms | 66% |
| 1000 | 75ms | 18ms | 76% |
| 5000 | 420ms | 65ms | 85% |

### 查询性能

| 查询类型 | JSON 存储 | SQLite 存储 | 性能提升 |
|---------|-----------|-------------|----------|
| 按名称查找 | 5ms | 2ms | 60% |
| 按标签过滤 | 15ms | 4ms | 73% |
| 按温度加载 | 12ms | 3ms | 75% |
| 全文搜索 | 25ms | 8ms | 68% |

### 内存占用

| 工具数量 | JSON 存储 | SQLite 存储 |
|---------|-----------|-------------|
| 100 | ~2 MB | ~1.5 MB |
| 500 | ~8 MB | ~4 MB |
| 1000 | ~15 MB | ~6 MB |
| 5000 | ~70 MB | ~25 MB |

---

## 配置方法

### 方法 1: 环境变量（推荐）

```bash
# 使用 SQLite 存储
export REGISTRYTOOLS_STORAGE_BACKEND=sqlite
registry-tools

# 永久配置（添加到 ~/.bashrc 或 ~/.zshrc）
echo 'export REGISTRYTOOLS_STORAGE_BACKEND=sqlite' >> ~/.bashrc
source ~/.bashrc
```

### 方法 2: CLI 参数

```bash
# 使用 SQLite 存储
registry-tools --storage-backend sqlite

# 与其他参数组合
registry-tools --storage-backend sqlite --transport http --port 8000
```

### 方法 3: Claude Desktop 配置

```json
{
  "mcpServers": {
    "RegistryTools": {
      "command": "registry-tools",
      "env": {
        "REGISTRYTOOLS_STORAGE_BACKEND": "sqlite"
      }
    }
  }
}
```

### 配置优先级

```
CLI 参数 > 环境变量 > 默认值 (json)
```

**示例**:
```bash
# 环境变量设置为 json
export REGISTRYTOOLS_STORAGE_BACKEND=json

# CLI 参数会覆盖环境变量
registry-tools --storage-backend sqlite  # 实际使用 sqlite
```

---

## 数据迁移

### 从 JSON 迁移到 SQLite

#### 方法 1: 使用 Python 脚本

```python
"""
从 JSON 存储迁移到 SQLite 存储
"""

from pathlib import Path
from registrytools.storage import JSONStorage, SQLiteStorage

# 1. 从 JSON 加载工具
json_storage = JSONStorage(Path("~/.RegistryTools/tools.json"))
tools = json_storage.load_all()

print(f"从 JSON 加载了 {len(tools)} 个工具")

# 2. 保存到 SQLite
sqlite_storage = SQLiteStorage(Path("~/.RegistryTools/tools.db"))
sqlite_storage.save_many(tools)

print(f"已迁移 {len(tools)} 个工具到 SQLite 存储")

# 3. 验证数据
loaded_tools = sqlite_storage.load_all()
print(f"验证: SQLite 中有 {len(loaded_tools)} 个工具")
```

#### 方法 2: 使用命令行工具

```bash
# 备份现有 JSON 数据
cp ~/.RegistryTools/tools.json ~/.RegistryTools/tools.json.backup

# 启动服务（会自动使用 SQLite）
export REGISTRYTOOLS_STORAGE_BACKEND=sqlite
registry-tools

# 使用示例脚本迁移
python examples/storage_migration.py
```

### 从 SQLite 迁移到 JSON

```python
"""
从 SQLite 存储迁移到 JSON 存储
"""

from pathlib import Path
from registrytools.storage import JSONStorage, SQLiteStorage

# 1. 从 SQLite 加载工具
sqlite_storage = SQLiteStorage(Path("~/.RegistryTools/tools.db"))
tools = sqlite_storage.load_all()

print(f"从 SQLite 加载了 {len(tools)} 个工具")

# 2. 保存到 JSON
json_storage = JSONStorage(Path("~/.RegistryTools/tools.json"))
json_storage.save_many(tools)

print(f"已迁移 {len(tools)} 个工具到 JSON 存储")

# 3. 验证数据
loaded_tools = json_storage.load_all()
print(f"验证: JSON 中有 {len(loaded_tools)} 个工具")
```

### 迁移注意事项

1. **备份数据**: 迁移前务必备份现有数据
2. **停止服务**: 迁移期间停止 RegistryTools 服务
3. **验证数据**: 迁移后验证工具数量和内容
4. **更新配置**: 迁移后更新存储后端配置
5. **清理旧数据**: 确认新存储正常后清理旧数据文件

### 迁移验证清单

- [ ] 备份现有数据文件
- [ ] 执行迁移脚本
- [ ] 验证工具数量一致
- [ ] 验证工具内容一致
- [ ] 测试搜索功能
- [ ] 测试工具注册功能
- [ ] 更新存储配置
- [ ] 重启服务
- [ ] 清理旧数据文件

---

## 相关文档

- [配置指南](CONFIGURATION.md) - 完整的环境变量和 CLI 参数配置
- [API 文档](API.md) - Python API 参考
- [架构设计](ARCHITECTURE.md) - 存储层架构设计
- [故障排除](TROUBLESHOOTING.md) - 存储相关问题排查

---

**维护者**: Maric
**文档版本**: v0.2.1
