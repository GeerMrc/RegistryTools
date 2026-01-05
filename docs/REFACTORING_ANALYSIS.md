# 项目目录结构重构分析

> 分析RegistryTools到src的完整重构方案

## 会话信息

- **会话ID**: `aecfd455-050e-41f0-a49b-fcb55bbc74e7`
- **状态**: ✅ 已完成
- **创建时间**: 2026-01-05 18:44:46
- **更新时间**: 2026-01-05 18:45:45
- **思考步骤数**: 6

## 思考步骤

💭 **步骤 1**

问题分析：当前项目使用 `RegistryTools/RegistryTools/` 嵌套目录结构作为开发目录，这与标准 Python 项目的 `src/` 布局规范不符。

**当前结构问题**：
1. 项目根目录: `/models/claude-glm/RegistryTools/`
2. 开发代码目录: `/models/claude-glm/RegistryTools/RegistryTools/`
3. 这种嵌套结构（包名=目录名）虽然可以工作，但不是最佳实践

**标准 Python 项目 `src/` 布局优势**：
1. 防止测试意外导入已安装的包而非开发版本
2. 确保导入的是开发中的代码
3. 符合 setuptools 和 pip 推荐的项目结构
4. 更好的 IDE 支持和代码导航

**影响范围分析**：
需要修改的文件和配置：
1. 目录结构重组（物理移动）
2. pyproject.toml 配置
3. 所有导入语句
4. 测试文件中的导入
5. 文档中的路径引用
6. scripts/ 中的脚本
7. fastmcp.json 配置

这是一个影响全项目的重大重构，需要谨慎规划。

<details><summary>🕒 2026-01-05 18:45:13</summary>

</details>

💭 **步骤 2**

**重构方案设计 - 目标结构**：

```
RegistryTools/
├── src/
│   └── registrytools/          # 重命名: RegistryTools → registrytools (PEP 8)
│       ├── __init__.py
│       ├── __main__.py
│       ├── server.py
│       ├── defaults.py
│       ├── registry/
│       ├── search/
│       └── storage/
├── tests/                       # 保持不变
├── docs/                        # 保持不变
├── scripts/                     # 需要更新路径引用
├── examples/                    # 需要更新导入语句
├── pyproject.toml               # 关键配置更新
├── fastmcp.json                # 更新 source.path
└── README.md                    # 更新文档
```

**关键变更点**：
1. **目录命名**: `RegistryTools` → `registrytools` (遵循 PEP 8 小写规范)
2. **包路径更新**: `RegistryTools.*` → `registrytools.*`
3. **命令行入口**: `registry-tools` 命令保持不变（PyPI 包名仍为 Registry-Tools）
4. **配置文件**:
   - pyproject.toml: `packages = ["src/registrytools"]`
   - `[project.scripts]`: 保持 `registry-tools = "registrytools.__main__:main"`
   - `[tool.hatch.build.targets.wheel]`: 更新为 `packages = ["src/registrytools"]`
   - `[tool.pytest.ini_options]`: 更新 `--cov=registrytools`
   - `[tool.coverage.run]`: 更新 `source = ["src/registrytools"]`

<details><summary>🕒 2026-01-05 18:45:18</summary>

</details>

💭 **步骤 3**

**风险评估与迁移策略**：

**高风险点**：
1. **Git 历史**: 移动目录会导致 Git 历史记录复杂化
   - 缓解: 使用 `git mv` 而非系统 mv，保留历史
   
2. **已发布的 PyPI 包**: 如果已有用户安装了 `Registry-Tools`
   - 当前状态: v0.1.0 尚未发布（TASK.md 显示 Phase 9 未完成）
   - 优势: 这是进行重构的最佳时机！

3. **导入兼容性**: 破坏性变更
   - 现有用户代码需要更新导入语句
   - 由于未发布，影响范围仅限于项目本身

**分阶段迁移策略**：

**阶段 1: 准备阶段**
- 创建新的 src/registrytools/ 目录结构
- 复制并修改所有源文件
- 更新 pyproject.toml 配置
- 暂时保留旧目录

**阶段 2: 测试验证**
- 更新所有测试文件导入
- 运行完整测试套件
- 确保覆盖率不下降

**阶段 3: 文档更新**
- 更新所有文档中的路径引用
- 更新 examples/ 中的导入语句
- 更新 scripts/ 中的路径

**阶段 4: 清理阶段**
- 删除旧的 RegistryTools/ 目录
- Git 提交
- 交叉验证

**优势分析**：
由于项目处于 v0.1.0 发布前（Phase 9 未完成），这是进行此重构的**最佳时机**，没有向后兼容负担。

<details><summary>🕒 2026-01-05 18:45:24</summary>

</details>

💭 **步骤 4**

**详细文件变更清单**：

**需要修改的文件统计**：

1. **源代码文件** (约 15 个):
   - RegistryTools/__init__.py
   - RegistryTools/__main__.py
   - RegistryTools/server.py
   - RegistryTools/defaults.py
   - RegistryTools/registry/__init__.py
   - RegistryTools/registry/models.py
   - RegistryTools/registry/registry.py
   - RegistryTools/search/__init__.py
   - RegistryTools/search/base.py
   - RegistryTools/search/bm25_search.py
   - RegistryTools/search/regex_search.py
   - RegistryTools/storage/__init__.py
   - RegistryTools/storage/base.py
   - RegistryTools/storage/json_storage.py
   - RegistryTools/storage/sqlite_storage.py

2. **测试文件** (约 10 个):
   - tests/test_*.py - 所有测试文件的导入语句

3. **配置文件** (5 个):
   - pyproject.toml (关键配置)
   - fastmcp.json
   - fastmcp.http.json
   - .ruff.conf (如存在)
   - mypy.ini (如存在)

4. **脚本文件** (5 个):
   - scripts/build/build-wheel.py
   - scripts/build/build-mcp.py
   - scripts/verify/verify-before-release.py
   - scripts/verify/verify-after-install.py
   - scripts/release/create-release.py

5. **示例文件** (3 个):
   - examples/basic_usage.py
   - examples/custom_tools.py
   - examples/search_demo.py

6. **文档文件** (约 7 个):
   - README.md
   - docs/ARCHITECTURE.md
   - docs/API.md
   - docs/CONTRIBUTING.md
   - docs/DEVELOPMENT_WORKFLOW.md
   - docs/TASK.md
   - docs/CHANGELOG.md

**总计**: 约 45+ 个文件需要检查或修改

**导入语句变更模式**：
- `from registrytools.xxx import` → `from registrytools.xxx import`
- `import registrytools.xxx` → `import registrytools.xxx`
- `RegistryTools.` → `registrytools.`

<details><summary>🕒 2026-01-05 18:45:34</summary>

</details>

💭 **步骤 5**

**验证清单与质量保证**：

**重构后必须验证的项目**：

1. **代码质量检查**：
   ```bash
   # Rint 代码检查
   ruff check src/registrytools/ tests/
   
   # Black 格式检查
   black --check src/registrytools/ tests/
   
   # MyPy 类型检查
   mypy src/registrytools/
   ```

2. **测试套件验证**：
   ```bash
   # 运行所有测试
   pytest tests/ -v
   
   # 测试覆盖率
   pytest --cov=registrytools --cov-report=term-missing
   
   # 目标: 所有测试通过，覆盖率 >= 88%（当前水平）
   ```

3. **构建验证**：
   ```bash
   # 构建 Wheel 包
   pipx run build
   
   # 验证包可安装
   pip install --force-reinstall dist/Registry_Tools-*.whl
   
   # 验证命令行入口
   registry-tools --help
   ```

4. **MCP 服务器验证**：
   ```bash
   # STDIO 模式
   registry-tools --transport stdio
   
   # HTTP 模式
   registry-tools --transport http --port 8000
   ```

5. **导入路径验证**：
   ```python
   # 验证所有导入路径正确
   from registrytools import ToolRegistry
   from registrytools.storage import JSONStorage
   from registrytools.search import BM25Search
   ```

6. **文档交叉验证**：
   - 检查所有文档中的路径引用是否正确
   - 验证代码示例是否可运行
   - 确认架构图与实际结构一致

<details><summary>🕒 2026-01-05 18:45:39</summary>

</details>

💭 **步骤 6**

**最终执行计划总结**：

**重构决策**：✅ **推荐执行**

**理由**：
1. 项目处于 v0.1.0 发布前，无向后兼容负担
2. 符合 Python 社区标准项目结构（src layout）
3. 改善开发体验和测试可靠性
4. 遵循 PEP 8 命名规范（小写模块名）

**执行计划概览**：

**Phase 11: 项目结构标准化重构**（新增阶段）

**11.1 准备阶段**
- TASK-1101: 创建 src/ 目录结构
- TASK-1102: 移动源代码到 src/registrytools/
- TASK-1103: 更新 pyproject.toml 配置

**11.2 代码适配阶段**
- TASK-1104: 更新源代码内部导入
- TASK-1105: 更新测试文件导入
- TASK-1106: 更新脚本文件路径

**11.3 文档更新阶段**
- TASK-1107: 更新配置文件（fastmcp.json 等）
- TASK-1108: 更新示例代码导入
- TASK-1109: 更新所有文档引用

**11.4 验证与清理阶段**
- TASK-1110: 运行完整测试套件
- TASK-1111: 代码质量检查
- TASK-1112: 构建与安装验证
- TASK-1113: 删除旧目录
- TASK-1114: Git 提交与交叉验证

**预期结果**：
- 符合 Python 标准的 src/ 布局
- 所有 249+ 测试通过
- 代码覆盖率保持 88%+
- 无功能回归
- 为 v0.1.0 发布做好结构准备

**风险等级**: 🟡 中等（可控，最佳时机）

<details><summary>🕒 2026-01-05 18:45:45</summary>

</details>

## 元数据

```json
{
  "type": "refactoring",
  "scope": "project_structure",
  "priority": "high"
}
```

---
*导出时间: 2026-01-05 18:45:52*

*由 DeepThinking-MCP 生成*