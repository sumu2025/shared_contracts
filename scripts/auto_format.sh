#!/bin/bash
# 自动格式化脚本 - 用于CI环境或本地开发
set -e

echo "=== 自动格式化代码 ==="
poetry run black .
poetry run isort .

echo "=== 检查其他代码风格问题 ==="
poetry run flake8 . --max-line-length=88 --extend-ignore=E203 --count --statistics

echo "格式化完成！"
