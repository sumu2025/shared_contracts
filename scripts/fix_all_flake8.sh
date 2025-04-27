#!/bin/bash
# 运行所有修复脚本
echo "===== 修复行过长问题 ====="
./scripts/fix_long_lines.sh

echo "===== 修复f-string问题 ====="
./scripts/fix_fstrings.sh

echo "===== 修复未使用变量问题 ====="
./scripts/fix_unused_vars.sh

echo "===== 修复裸异常问题 ====="
./scripts/fix_bare_except.sh

echo "===== 修复未使用全局声明问题 ====="
./scripts/fix_unused_global.sh

echo "===== 运行最终检查 ====="
flake8 . --max-line-length=88 --extend-ignore=E203

echo "如果还有问题，可能需要重复运行该脚本或手动修复一些特殊情况。"
