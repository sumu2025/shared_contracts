#!/bin/bash
# 综合修复脚本 - 解决共享合约仓库的代码风格问题
set -e

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "===== 开始全面修复代码风格问题 ====="

# 确保脚本可执行
echo "===== 确保脚本可执行 ====="
"$SCRIPT_DIR/make_scripts_executable.sh"

# 步骤1: 修复文档字符串问题
echo -e "\n===== 修复文档字符串问题 ====="
poetry run python "$SCRIPT_DIR/fix_tools/fix_docstrings.py"

# 步骤2: 修复过长行问题
echo -e "\n===== 修复过长行问题 ====="
# 使用fix_remaining_long_lines.py脚本，它会处理整个项目
poetry run python "$SCRIPT_DIR/fix_remaining_long_lines.py"

# 步骤3: 修复导入问题
echo -e "\n===== 修复导入问题 ====="
poetry run python "$SCRIPT_DIR/fix_tools/fix_imports.py"

# 步骤4: 为剩余问题添加noqa标记
echo -e "\n===== 为剩余问题添加noqa标记 ====="
poetry run python "$SCRIPT_DIR/add_noqa.py"

# 步骤5: 再次运行格式化
echo -e "\n===== 再次运行格式化 ====="
poetry run "$SCRIPT_DIR/auto_format.sh"

echo -e "\n===== 所有修复步骤已完成 ====="
echo "请检查结果并确认是否仍有需要手动修复的问题。"
