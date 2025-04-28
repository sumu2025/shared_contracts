#!/bin/bash
# 一键修复代码风格问题脚本
set -e

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "===== 开始修复代码风格问题 ====="

# 确保脚本可执行
chmod +x "$SCRIPT_DIR"/*.sh
chmod +x "$SCRIPT_DIR"/fix_tools/*.py

# 步骤1: 修复导入顺序
echo -e "\n===== 修复导入顺序 ====="
poetry run python "$SCRIPT_DIR/fix_tools/fix_imports.py"

# 步骤2: 使用Black格式化代码
echo -e "\n===== 使用Black格式化代码 ====="
poetry run black "$ROOT_DIR"

# 步骤3: 运行flake8检查剩余问题
echo -e "\n===== 检查剩余flake8问题 ====="
poetry run flake8 "$ROOT_DIR" || true

# 步骤4: 修复文档字符串格式
echo -e "\n===== 修复文档字符串格式 ====="
poetry run python "$SCRIPT_DIR/fix_tools/fix_docstrings.py"

# 步骤5: 检查类型注解问题
echo -e "\n===== 检查类型注解问题 ====="
poetry run python "$SCRIPT_DIR/fix_tools/fix_type_annotations.py"

# 步骤6: 运行mypy检查类型
echo -e "\n===== 运行mypy类型检查 ====="
poetry run mypy --namespace-packages --explicit-package-bases "$ROOT_DIR" || true

echo -e "\n===== 所有自动修复步骤已完成 ====="
echo "请手动检查并修复剩余的问题，特别是文档字符串和类型注解问题。"
