#!/bin/bash
# 安装和配置pre-commit钩子的脚本
set -e

echo "===== 开始设置pre-commit钩子 ====="

# 确保已安装pre-commit
if ! command -v pre-commit &> /dev/null; then
    echo "正在安装pre-commit..."
    poetry add --group dev pre-commit
fi

# 安装额外的依赖
echo "正在安装额外依赖..."
poetry add --group dev \
    flake8-bugbear \
    flake8-docstrings \
    bandit \
    autoflake

# 安装pre-commit钩子
echo "正在安装Git钩子..."
poetry run pre-commit install

# 检查钩子配置
echo "检查钩子配置..."
poetry run pre-commit autoupdate

echo "钩子配置："
poetry run pre-commit list-hooks

echo -e "\n===== pre-commit钩子设置完成 ====="
echo "提示: 可以使用以下命令在提交前手动运行所有钩子:"
echo "  poetry run pre-commit run --all-files"
echo ""
echo "要临时跳过钩子检查(不推荐)，可以使用:"
echo "  git commit --no-verify"
