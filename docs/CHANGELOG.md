# RegistryTools 变更日志

本文件记录 RegistryTools 项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [Unreleased]

### 新增
- **Phase 11 项目结构标准化重构** (TASK-1101 至 TASK-1114)
  - 迁移到标准 Python `src/` 布局
  - 包名从 `RegistryTools` 改为小写 `registrytools` (PEP 8)
  - 源代码从 `RegistryTools/` 移动到 `src/registrytools/`

### 变更
- **项目结构** (Phase 11)
  - 采用标准 `src/` 布局，符合 Python 社区最佳实践
  - 更新所有导入语句: `from RegistryTools` → `from registrytools`
  - 更新 pyproject.toml 配置以支持 src/ 布局
  - 更新 fastmcp.json 配置文件路径
  - 更新所有文档中的路径引用

- **Phase 8.5 质量修复** (TASK-851 至 TASK-860)
  - 新增 `tests/test_mcp_integration.py` FastMCP 集成测试（27个测试）
  - 新增 `docs/README.md` 文档索引
  - 总测试数量: 217 → 244 (+27)
  - server.py 测试覆盖率: 46% → 97%

### 修复
- **Pydantic V2 废弃警告** (TASK-854)
  - 移除 `json_encoders` 配置
  - 使用 `field_serializer` 替代
- **server.py 测试覆盖率** (TASK-852)
  - 添加 FastMCP 工具层集成测试
  - 覆盖所有 MCP 工具和资源接口

### 变更
- **冷热工具分离机制** (TASK-802)
  - 新增 `ToolTemperature` 枚举（HOT/WARM/COLD）
  - 新增 `defaults.py` 配置文件，包含分类阈值常量
  - 新增三层存储字典和温度锁
  - 新增工具温度自动分类和升降级机制
  - 新增存储层 `load_by_temperature()` 接口

### 变更
- **RegexSearch 缓存修复** (TASK-801-FIX)
  - 统一使用基类的哈希值检测方法
  - 添加 6 个 RegexSearch 缓存测试

### 改进
- `ToolRegistry.register()`: 自动分类工具温度
- `ToolRegistry.update_usage()`: 自动升级温度 + 检查降级
- `ToolRegistry.unregister()`: 从温度层移除
- `ToolMetadata`: 新增 `temperature` 字段
- `JSONStorage`: 实现按温度加载工具（过滤模式）
- `SQLiteStorage`: 实现按温度加载工具（SQL 优化）

### 计划中
- 语义搜索支持 (Embedding)
- Web UI 管理界面
- 分布式工具索引

---

## [0.1.0] - 2026-01-04

### 新增
- 项目初始化
- 核心文档创建
  - CONTRIBUTING.md (贡献指南)
  - DEVELOPMENT_WORKFLOW.md (开发流程规范)
  - TASK.md (任务追踪文档)
  - ARCHITECTURE.md (架构设计文档)
  - API.md (API 文档)
  - CHANGELOG.md (变更日志)
- 目录结构创建
  - RegistryTools/ (主包)
  - docs/ (文档)
  - scripts/ (脚本工具)
  - tests/ (测试)
  - examples/ (示例)

### 计划
- ToolMetadata 数据模型
- BM25 搜索算法
- 工具注册表实现
- JSON/SQLite 存储层
- MCP 工具接口
- FastMCP 服务器入口

---

## 版本说明

### [0.1.0] - 初始版本
首次发布，包含基础的工具注册和搜索功能。

---

## 变更类型说明

- **新增**: 新功能
- **变更**: 现有功能的变更
- **弃用**: 即将移除的功能
- **移除**: 已移除的功能
- **修复**: 问题修复
- **安全**: 安全相关的修复

---

**维护者**: Maric
**文档版本**: v0.1.0
