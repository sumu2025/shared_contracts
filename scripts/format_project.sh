#!/bin/bash
# 一键格式化项目代码脚本

set -e

# 显示操作信息
echo "=== 开始格式化代码 ==="

# 确保依赖已安装
if ! command -v poetry &> /dev/null; then
    echo "需要安装poetry。请执行: pip install poetry"
    exit 1
fi

# 运行black格式化代码
echo "运行black格式化..."
poetry run black .

# 运行isort整理导入
echo "运行isort整理导入..."
poetry run isort .

# 检查是否有flake8错误
echo "检查flake8错误..."
poetry run flake8 . --max-line-length=88 --extend-ignore=E203 --count --statistics || {
    echo "flake8检查发现问题，但这不会中断脚本"
}

echo "=== 代码格式化完成 ==="
