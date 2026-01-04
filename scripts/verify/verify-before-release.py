#!/usr/bin/env python
"""
发布前验证脚本

在发布新版本前执行，确保项目处于可发布状态。

用法:
    python scripts/verify/verify-before-release.py
"""

import os
import subprocess
import sys
from pathlib import Path


class Colors:
    """终端颜色"""
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"


def print_check(name: str, passed: bool, message: str = ""):
    """打印检查结果"""
    status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if passed else f"{Colors.RED}✗ FAIL{Colors.RESET}"
    print(f"  {status} {name}")
    if message:
        print(f"    {message}")


def verify_project_structure():
    """验证项目结构"""
    print(f"\n{Colors.BLUE}📁 验证项目结构{Colors.RESET}")

    required_dirs = [
        "docs",
        "RegistryTools",
        "scripts",
        "tests",
        "examples"
    ]

    required_docs = [
        "docs/TASK.md",
        "docs/CONTRIBUTING.md",
        "docs/DEVELOPMENT_WORKFLOW.md",
        "docs/ARCHITECTURE.md",
        "docs/API.md",
        "docs/CHANGELOG.md"
    ]

    all_passed = True

    for dir_name in required_dirs:
        exists = Path(dir_name).is_dir()
        print_check(f"目录 {dir_name}/", exists)
        if not exists:
            all_passed = False

    for doc_path in required_docs:
        exists = Path(doc_path).is_file()
        print_check(f"文件 {doc_path}", exists)
        if not exists:
            all_passed = False

    return all_passed


def verify_documentation_sync():
    """验证文档同步状态"""
    print(f"\n{Colors.BLUE}📖 验证文档同步{Colors.RESET}")

    # 检查 TASK.md 是否包含所有 Phase
    task_md = Path("docs/TASK.md")
    if not task_md.exists():
        print_check("TASK.md 存在", False)
        return False

    content = task_md.read_text(encoding="utf-8")

    required_phases = [
        "Phase 0", "Phase 1", "Phase 2",
        "Phase 3", "Phase 4", "Phase 5"
    ]

    all_passed = True
    for phase in required_phases:
        found = phase in content
        print_check(f"包含 {phase}", found)
        if not found:
            all_passed = False

    return all_passed


def verify_tests():
    """验证测试"""
    print(f"\n{Colors.BLUE}🧪 验证测试{Colors.RESET}")

    # 检查是否有测试文件
    test_dir = Path("tests")
    if not test_dir.exists():
        print_check("tests/ 目录", False)
        return False

    test_files = list(test_dir.glob("test_*.py"))
    has_tests = len(test_files) > 0
    print_check(f"测试文件 ({len(test_files)} 个)", has_tests)

    # 运行测试（如果 pytest 可用）
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "--collect-only"],
            capture_output=True,
            timeout=10
        )
        tests_passed = result.returncode == 0
        print_check("pytest 可运行", tests_passed)
    except Exception:
        print_check("pytest 可运行", False, "pytest 未安装或超时")

    return has_tests


def verify_code_quality():
    """验证代码质量"""
    print(f"\n{Colors.BLUE}🔍 验证代码质量{Colors.RESET}")

    all_passed = True

    # 检查 Black
    try:
        result = subprocess.run(
            ["black", "--check", "RegistryTools/"],
            capture_output=True,
            timeout=30
        )
        formatted = result.returncode == 0
        print_check("代码格式 (Black)", formatted)
        if not formatted:
            all_passed = False
    except Exception:
        print_check("代码格式 (Black)", False, "Black 未安装")

    # 检查 Ruff
    try:
        result = subprocess.run(
            ["ruff", "check", "RegistryTools/"],
            capture_output=True,
            timeout=30
        )
        passed = result.returncode == 0
        print_check("代码检查 (Ruff)", passed)
        if not passed:
            all_passed = False
    except Exception:
        print_check("代码检查 (Ruff)", False, "Ruff 未安装")

    return all_passed


def verify_git_status():
    """验证 Git 状态"""
    print(f"\n{Colors.BLUE}📦 验证 Git 状态{Colors.RESET}")

    # 检查是否在 Git 仓库中
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True
        )
        is_repo = result.stdout.strip() == "true"
        print_check("Git 仓库", is_repo)
        if not is_repo:
            return False
    except Exception:
        print_check("Git 仓库", False)
        return False

    # 检查是否有未提交的更改
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True
    )
    has_changes = len(result.stdout.strip()) > 0
    print_check("工作目录干净", not has_changes)
    if has_changes:
        print(f"    {Colors.YELLOW}⚠️  有未提交的更改{Colors.RESET}")

    return True


def main():
    """主函数"""
    print("=" * 60)
    print("RegistryTools - 发布前验证")
    print("=" * 60)

    checks = [
        ("项目结构", verify_project_structure),
        ("文档同步", verify_documentation_sync),
        ("测试", verify_tests),
        ("代码质量", verify_code_quality),
        ("Git 状态", verify_git_status),
    ]

    results = []
    for name, check_func in checks:
        try:
            passed = check_func()
            results.append((name, passed))
        except Exception as e:
            print(f"{Colors.RED}✗ {name}: 检查出错 - {e}{Colors.RESET}")
            results.append((name, False))

    # 总结
    print()
    print("=" * 60)
    print("验证总结")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if passed else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"  {status} {name}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print(f"{Colors.GREEN}✅ 所有验证通过，可以发布！{Colors.RESET}")
        return 0
    else:
        print(f"{Colors.RED}❌ 部分验证失败，请修复后重试。{Colors.RESET}")
        return 1


if __name__ == "__main__":
    exit(main())
