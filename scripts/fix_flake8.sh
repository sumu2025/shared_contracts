#!/bin/bash
# 修复未使用的导入
find . -name "*.py" -exec autoflake --remove-all-unused-imports --in-place {} \;

# 修复行过长问题
black . --line-length=88

# 运行flake8检查看结果
flake8 . --max-line-length=88 --extend-ignore=E203
