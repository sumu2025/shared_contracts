#!/bin/bash
# 本地验证脚本 - 在提交前运行以确保代码质量
set -e

echo "=== 检查依赖项 ==="
poetry check

# 检查 pydantic 版本
PYDANTIC_VERSION=$(poetry run python -c "import pydantic; print(pydantic.__version__)")
echo "Pydantic version: $PYDANTIC_VERSION"

# 检查主版本是否至少为2
MAJOR_VERSION=$(echo $PYDANTIC_VERSION | cut -d'.' -f1)
if [ "$MAJOR_VERSION" -lt 2 ]; then
    echo "Error: Pydantic version must be >= 2.0.0"
    exit 1
fi

echo "=== 运行代码风格检查 ==="
poetry run black . --check --line-length=88
poetry run isort . --check --profile black
poetry run flake8 . --max-line-length=88 --extend-ignore=E203

echo "=== 运行类型检查 ==="
poetry run mypy .

echo "=== 运行单元测试 ==="
poetry run pytest -xvs tests/

echo "=== 生成覆盖率报告 ==="
poetry run pytest --cov=agentforge_contracts tests/ --cov-report=term

echo "全部检查通过！"
