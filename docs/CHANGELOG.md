# RegistryTools 变更日志

本文件记录 RegistryTools 项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [Unreleased]

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
