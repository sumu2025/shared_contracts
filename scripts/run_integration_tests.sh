#!/bin/bash
# 运行所有集成测试并生成报告
set -e

echo "=== 开始运行集成测试 ==="

# 确保依赖已安装
if ! command -v poetry &> /dev/null; then
    echo "需要安装poetry。请执行: pip install poetry"
    exit 1
fi

# 安装依赖
echo "正在确认依赖安装..."
poetry install --with dev --quiet

# 设置环境变量
export TESTING=1
export PYTHONPATH=.

# 运行集成测试
echo "正在运行集成测试..."
poetry run pytest integration_tests/ \
    -v \
    --tb=short \
    -m "integration" \
    --junitxml=integration_test_results.xml

# 如果需要运行特定的集成测试
if [ "$1" != "" ]; then
    echo "正在运行指定的集成测试: $1"
    poetry run pytest "integration_tests/$1" -v
fi

# 生成HTML报告(如果已安装pytest-html)
if poetry run python -c "import pytest_html" 2>/dev/null; then
    echo "正在生成HTML报告..."
    poetry run pytest integration_tests/ \
        -v \
        --tb=short \
        -m "integration" \
        --html=integration_test_report.html \
        --self-contained-html
fi

echo "=== 集成测试完成 ==="
