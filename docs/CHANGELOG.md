# RegistryTools 变更日志

本文件记录 RegistryTools 项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [Unreleased]

### 新增
- **Phase 18.3 配置文档本地/PyPI差异化说明** (2026-01-06)
  - 所有配置文档添加本地开发环境 vs PyPI 发布后的配置区分
  - 解决 `uvx registry-tools` 在本地开发环境无法连接的问题
  - 更新 README.md、CLAUDE_CONFIG.md、IDE_CONFIG.md、INSTALLATION.md
  - 新增故障排除章节，说明 uvx 连接失败的原因和解决方案
  - 所有配置示例明确标注"本地开发环境配置"和"PyPI 发布后配置"
- **Phase 18.2 命名规范完全统一** (2026-01-06)
  - PyPI 包名从 `Registry_Tools` 改为 `registry-tools`（符合 Python 最佳实践）
  - 统一所有文档中的安装命令引用（`pip install registry-tools`）
  - wheel 文件名自动规范化为 `registry_tools-0.1.0-py3-none-any.whl`
  - pip list 显示统一为 `registry-tools`
- **Phase 18 命名规范统一** (2026-01-06)
  - PyPI 包名从 `Registry-Tools` 改为 `Registry_Tools`
  - 统一 pip list 显示与 wheel 文件名（`Registry_Tools`）
  - 更新所有文档中的安装命令引用
  - wheel 文件名从 `registry_tools-0.1.0-py3-none-any.whl` 改为 `Registry_Tools-0.1.0-py3-none-any.whl`
- **Phase 15 API Key 认证功能** (2026-01-05)
  - 实现 API Key 生成、存储、认证中间件
  - 支持 READ/WRITE/ADMIN 三级权限
  - 提供 api-key CLI 子命令管理 API Key
  - API Key 格式: `rtk_<64-char-hex>`
  - 支持 HTTP Header 认证 (X-API-Key / Authorization Bearer)

- **Phase 14.2 日志功能** (2026-01-05)
  - 实现 Python logging 模块集成
  - 支持动态日志级别配置 (DEBUG/INFO/WARNING/ERROR)
  - 日志格式: `YYYY-MM-DD HH:MM:SS - registrytools - LEVEL - Message`
  - 支持 --log-level CLI 参数
  - 支持 REGISTRYTOOLS_LOG_LEVEL 环境变量

- **Phase 14.1 环境变量支持** (2026-01-05)
  - 支持 REGISTRYTOOLS_DATA_PATH 环境变量
  - 支持 REGISTRYTOOLS_TRANSPORT 环境变量
  - 支持 REGISTRYTOOLS_LOG_LEVEL 环境变量
  - 支持 REGISTRYTOOLS_ENABLE_AUTH 环境变量
  - 配置优先级: 环境变量 > CLI 参数 > 默认值

- **Phase 13 IDE 配置文档补充** (2026-01-05)
  - 创建 docs/IDE_CONFIG.md
  - 添加 Claude Desktop 配置方式 (STDIO/HTTP)
  - 添加 Claude Code CLI 命令配置方式（推荐）
  - 添加 Cursor 配置方式
  - 添加 Continue.dev 和 Cline 配置方式
  - 添加环境变量配置说明

- **Phase 12 文档体系完善** (2026-01-05)
  - 创建 docs/PUBLISHING.md 发布指南
  - 创建 docs/INSTALLATION.md 安装指南
  - 创建 docs/USER_GUIDE.md 用户指南
  - 创建 docs/CLAUDE_CONFIG.md 配置指南

- **Phase 10 Streamable HTTP 传输支持** (2026-01-05)
  - 实现 --transport http CLI 参数
  - 支持 --host, --port, --path 配置
  - 创建 fastmcp.json 配置文件
  - 支持 STDIO 和 Streamable HTTP 双模式

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
