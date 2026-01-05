# RegistryTools 使用示例

本目录包含 RegistryTools 的使用示例代码。

## 示例列表

### basic_usage.py

基本使用示例，演示：
- 创建工具注册表
- 搜索工具
- 按类别列出工具
- 获取工具定义
- 注册新工具

### custom_tools.py

自定义工具注册示例，演示：
- 定义自定义工具元数据
- 批量注册工具
- 工具属性配置

### search_demo.py

搜索功能演示，展示：
- BM25 搜索算法
- Regex 搜索算法
- 中文搜索支持
- 自然语言查询

## 运行示例

确保已安装 RegistryTools：

```bash
pip install RegistryTools
```

运行示例：

```bash
# 基本使用
python examples/basic_usage.py

# 自定义工具
python examples/custom_tools.py

# 搜索演示
python examples/search_demo.py
```

## 输出示例

```
=== 搜索 GitHub 工具 ===
- github.create_pull_request: Create a new pull request in a GitHub repository (相关度: 0.85)
- github.merge_pull_request: Merge a pull request in a GitHub repository (相关度: 0.72)
- github.add_issue_comment: Add a comment to a specific issue (相关度: 0.65)

=== 按类别列出工具 ===
可用类别: github, slack, aws, google, utilities...
GitHub 工具 (8 个):
  - github.create_pull_request
  - github.merge_pull_request
  - github.create_issue
```
