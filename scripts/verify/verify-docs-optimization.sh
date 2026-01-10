#!/bin/bash
# 验证文档优化效果

echo "=== Phase 32 文档优化验证 ==="
echo ""

echo "=== 1. 验证 REGISTRYTOOLS_DESCRIPTION 统一性 ==="
if grep -r "官方默认描述" docs/ 2>/dev/null; then
    echo "❌ 发现占位符"
else
    echo "✅ 已统一，无占位符"
fi

echo ""
echo "=== 2. 验证 REGISTRYTOOLS_DESCRIPTION 完整性 ==="
count=$(grep -r "统一的 MCP 工具注册与搜索服务，用于发现和筛选可用工具，提升任务执行工具调用准确性，复杂任务工具调用效率" docs/ 2>/dev/null | wc -l)
echo "完整默认值出现次数: $count (预期: ≥3)"

echo ""
echo "=== 3. 验证 PyPI 发布状态简化 ==="
pypi_full_count=$(grep -r "尚未发布到 PyPI" docs/ 2>/dev/null | grep -v "TASK.md" | wc -l)
echo "完整 PyPI 状态说明数量: $pypi_full_count (预期: 3)"
echo "保留完整说明的文档应为: README.md, INSTALLATION.md, PUBLISHING.md"

echo ""
echo "=== 4. 验证 PyPI 状态引用链接 ==="
ref_count=$(grep -r "安装指南 - PyPI 发布状态" docs/ 2>/dev/null | wc -l)
echo "PyPI 状态引用链接数量: $ref_count (预期: ≥6)"

echo ""
echo "=== 5. 验证版本号一致性 ==="
version_count=$(grep -r "^\*\*版本\*\*: v0.1.1" docs/ 2>/dev/null | wc -l)
version_total=$(grep -r "^\*\*版本\*\*:" docs/ 2>/dev/null | wc -l)
echo "v0.1.1 版本号文档数: $version_count / $version_total"

echo ""
echo "=== 6. 验证更新日期一致性 ==="
date_count=$(grep -r "^\*\*更新日期\*\*: 2026-01-10" docs/ 2>/dev/null | wc -l)
date_total=$(grep -r "^\*\*更新日期\*\*:" docs/ 2>/dev/null | wc -l)
echo "2026-01-10 更新日期文档数: $date_count / $date_total"

echo ""
echo "=== 7. 统计文档行数 ==="
wc -l docs/*.md | tail -1

echo ""
echo "=== 验证完成 ==="
