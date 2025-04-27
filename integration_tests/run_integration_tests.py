#!/usr/bin/env python
"""
运行所有集成测试的脚本。

此脚本用于执行shared_contracts模块的所有集成测试，
便于在命令行中一键运行所有测试。
"""

import argparse
import os
import sys
from datetime import datetime

import pytest


def run_tests(verbose=False, test_name=None, fail_fast=False):
    """
    运行集成测试。

    Args:
        verbose: 是否显示详细输出
        test_name: 特定测试名称（可选）
        fail_fast: 是否在第一个失败后停止

    Returns:
        测试成功返回True，否则返回False
    """
    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # 构建测试参数
    args = [current_dir]
    if verbose:
        args.append("-v")
    if fail_fast:
        args.append("-x")

    # 如果指定了特定测试，只运行该测试
    if test_name:
        if not test_name.startswith("test_"):
            test_name = f"test_{test_name}"
        args.append(f"{current_dir}/{test_name}.py")

    # 运行测试
    print(f"=== 开始运行集成测试 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")
    result = pytest.main(args)
    success = result == 0

    if success:
        print(f"=== 所有测试通过! ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")
    else:
        print(f"=== 测试失败! ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")

    return success


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="运行AgentForge集成测试")
    parser.add_argument("-v", "--verbose", action="store_true", help="显示详细输出")
    parser.add_argument(
        "-t", "--test", type=str, help="运行特定测试 (例如: agent_model_integration)"
    )
    parser.add_argument("-x", "--fail-fast", action="store_true", help="在第一个失败后停止")

    args = parser.parse_args()

    # 运行测试
    success = run_tests(
        verbose=args.verbose, test_name=args.test, fail_fast=args.fail_fast
    )

    # 根据测试结果设置退出码
    sys.exit(0 if success else 1)
