#!/bin/bash
# 综合自动修复脚本 - 修复共享合约仓库的代码风格问题
set -e

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "===== 开始全面自动修复代码风格问题 ====="

# 确保脚本可执行
echo "===== 确保脚本可执行 ====="
"$SCRIPT_DIR/make_scripts_executable.sh"

# 步骤1: 使用新的文档字符串修复脚本
echo -e "\n===== 修复文档字符串问题 ====="
poetry run python "$SCRIPT_DIR/fix_docstrings_auto.py"

# 步骤2: 使用Black格式化代码
echo -e "\n===== 使用Black格式化代码 ====="
poetry run black "$ROOT_DIR"

# 步骤3: 使用isort修复导入问题
echo -e "\n===== 使用isort修复导入问题 ====="
poetry run isort "$ROOT_DIR"

# 步骤4: 修复过长行问题
echo -e "\n===== 修复过长行问题 ====="
poetry run python "$SCRIPT_DIR/fix_remaining_long_lines.py"

# 步骤5: 为剩余问题添加noqa标记
echo -e "\n===== 为剩余问题添加noqa标记 ====="
poetry run python "$SCRIPT_DIR/add_noqa.py"

# 步骤6: 再次运行格式化
echo -e "\n===== 再次运行格式化 ====="
poetry run "$SCRIPT_DIR/auto_format.sh"

# 步骤7: 检查剩余问题
echo -e "\n===== 检查剩余问题 ====="
poetry run flake8 "$ROOT_DIR" || true

echo -e "\n===== 所有自动修复步骤已完成 ====="
echo "如果仍有风格问题需要手动修复，请查看上面的输出结果。"
